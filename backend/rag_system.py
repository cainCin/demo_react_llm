"""
RAG (Retrieval-Augmented Generation) System
Uses Milvus Lite for vector search and PostgreSQL for full text storage
Database operations are handled by DatabaseManager
"""
import uuid
import hashlib
from typing import List, Optional, Dict, Tuple
from database import (
    DatabaseManager, Document, Chunk,
    DocumentData, ChunkData, VectorData, SearchResult,
    VerificationResult, ResyncResult
)
from config import (
    CHUNK_SIZE, CHUNK_OVERLAP, CHUNK_MIN_SIZE, EMBEDDING_MAX_LENGTH,
    EMBEDDING_MODEL, EMBEDDING_DIM,
    RAG_TOP_K, RAG_SIMILARITY_THRESHOLD,
    MILVUS_METRIC_TYPE
)

# Import extractors (following convention: extractors package)
try:
    from extractors import ChunkExtractor, chunk_text_toc_aware
except ImportError:
    # Fallback if extractors not available
    ChunkExtractor = None
    chunk_text_toc_aware = None


class RAGSystem:
    """
    RAG System for document storage and retrieval
    Handles chunking, embedding generation, and similarity search
    Database operations are delegated to DatabaseManager
    """
    
    def __init__(self, openai_client, embedding_model: Optional[str] = None, use_azure: bool = False):
        self.openai_client = openai_client
        self.embedding_model = embedding_model or EMBEDDING_MODEL
        self.embedding_dim = EMBEDDING_DIM
        self.use_azure = use_azure
        
        # Initialize database manager
        self.db_manager = DatabaseManager()
        self.db_manager.initialize()
    
    def chunk_text(self, text: str, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None) -> List[str]:
        """
        Simple chunking strategy: split text into overlapping chunks
        Delegates to ChunkExtractor (following convention: delegate to specialized classes)
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk (default: from config)
            chunk_overlap: Overlap between chunks (default: from config)
            
        Returns:
            List of text chunks
        """
        if ChunkExtractor:
            extractor = ChunkExtractor()
            return extractor.chunk_text_simple(text, chunk_size, chunk_overlap)
        else:
            # Fallback if extractors not available
            chunk_size = chunk_size or CHUNK_SIZE
            chunk_overlap = chunk_overlap or CHUNK_OVERLAP
            
            if not text or len(text) <= chunk_size:
                return [text] if text else []
            
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + chunk_size
                chunk = text[start:end]
                
                # Try to break at sentence boundary if not at end
                if end < len(text):
                    for break_char in ['. ', '.\n', '! ', '!\n', '? ', '?\n', '\n\n']:
                        last_break = chunk.rfind(break_char)
                        if last_break > chunk_size * 0.5:
                            chunk = chunk[:last_break + len(break_char)]
                            end = start + len(chunk)
                            break
                
                chunk_text = chunk.strip()
                if len(chunk_text) >= CHUNK_MIN_SIZE or start == 0:
                    chunks.append(chunk_text)
                
                start = end - chunk_overlap
                if start >= len(text):
                    break
            
            return chunks
    
    def chunk_text_toc_aware(self, text: str, filename: str) -> Tuple[List[str], Optional[List[Dict]]]:
        """
        TOC-aware chunking strategy that aligns chunks with TOC sections
        Delegates to ChunkExtractor (following convention: delegate to specialized classes)
        
        Args:
            text: Document text content
            filename: Original filename (for format detection)
            
        Returns:
            Tuple of (chunks: List[str], toc: Optional[List[Dict]])
        """
        if chunk_text_toc_aware:
            return chunk_text_toc_aware(text, filename)
        else:
            # Fallback to simple chunking if extractors not available
            chunks = self.chunk_text(text)
            return chunks, None
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI or Azure OpenAI"""
        try:
            # Use embeddings API (works for both standard OpenAI and Azure OpenAI)
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dim
    
    def store_document(self, filename: str, text: str) -> str:
        """
        Store document in PostgreSQL and chunks in Milvus Lite
        Returns document_id
        """
        db = self.db_manager.get_session()
        
        try:
            # Calculate file hash
            file_hash = hashlib.md5(text.encode()).hexdigest()
            
            # Check if document already exists
            existing_doc = db.query(Document).filter(Document.file_hash == file_hash).first()
            if existing_doc:
                print(f"Document already exists: {filename}")
                return existing_doc.id
            
            # Create document ID
            doc_id = str(uuid.uuid4())
            
            # Chunk the text using TOC-aware strategy (delegates to ChunkExtractor)
            chunks, toc_data = self.chunk_text_toc_aware(text, filename)
            print(f"Created {len(chunks)} chunks for {filename}")
            
            if toc_data:
                print(f"📑 Extracted {len(toc_data)} TOC items and aligned chunks with sections")
            
            # Store document in PostgreSQL
            document = Document(
                id=doc_id,
                filename=filename,
                full_text=text,
                file_hash=file_hash,
                chunk_count=len(chunks),
                toc=toc_data
            )
            db.add(document)
            
            # Store chunks in PostgreSQL
            chunk_records = []
            for idx, chunk_text in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                chunk_record = Chunk(
                    id=chunk_id,
                    document_id=doc_id,
                    chunk_index=idx,
                    text=chunk_text
                )
                chunk_records.append(chunk_record)
                db.add(chunk_record)
            
            db.commit()
            
            # Generate embeddings and store in Milvus Lite
            print(f"📊 Generating embeddings for {len(chunks)} chunks...")
            insert_data: List[VectorData] = []
            total_chunks = len(chunks)
            
            for idx, chunk_text in enumerate(chunks):
                # Show progress for embedding generation
                progress = ((idx + 1) / total_chunks) * 100
                print(f"   Generating embedding {idx + 1}/{total_chunks} ({progress:.1f}%)", end='\r')
                
                embedding = self.generate_embedding(chunk_text)
                chunk_id_str = chunk_records[idx].id
                # Convert UUID string to int64 for Milvus
                chunk_id_int = self.db_manager._uuid_to_int64(chunk_id_str)
                
                # Create VectorData object
                vector_data = VectorData(
                    id=chunk_id_int,  # Milvus requires int64
                    vector=embedding,  # Only embedding stored in Milvus
                    document_id=doc_id,  # Keep document_id for reference
                    chunk_index=idx  # Keep chunk_index for reference
                    # Note: text is NOT stored in Milvus, only in PostgreSQL
                )
                insert_data.append(vector_data)
            
            print()  # New line after progress
            
            # Insert into Milvus Lite using database manager
            if insert_data:
                print(f"📤 Inserting {len(insert_data)} chunks into Milvus Lite...")
                self.db_manager.insert_vectors(insert_data)
                print(f"✅ Stored {len(insert_data)} chunks in Milvus Lite")
            
            print(f"✅ Stored document: {filename} (ID: {doc_id})")
            return doc_id
            
        except Exception as e:
            db.rollback()
            print(f"Error storing document: {e}")
            raise
        finally:
            db.close()
    
    def search_similar(self, query: str, top_k: Optional[int] = None, document_ids: Optional[List[str]] = None) -> List[SearchResult]:
        """
        Search for similar chunks using vector similarity
        Returns list of SearchResult objects with metadata
        Text is retrieved from PostgreSQL, not Milvus
        Uses config values if top_k not provided
        
        Args:
            query: Search query text
            top_k: Number of results to return (default: from config)
            document_ids: Optional list of document IDs to filter results (for @ mentions)
        """
        top_k = top_k or RAG_TOP_K
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Format results and retrieve text from PostgreSQL
            similar_chunks: List[SearchResult] = []
            db = self.db_manager.get_session()
            
            try:
                # If filtering by document_ids, query PostgreSQL first to get chunks
                if document_ids and len(document_ids) > 0:
                    print(f"📌 Filtering by {len(document_ids)} documents - querying PostgreSQL first")
                    
                    # Get all chunks from mentioned documents
                    chunks_from_docs = db.query(Chunk).filter(
                        Chunk.document_id.in_(document_ids)
                    ).all()
                    
                    print(f"   Found {len(chunks_from_docs)} chunks in mentioned documents")
                    
                    if not chunks_from_docs:
                        print(f"⚠️  No chunks found in mentioned documents")
                        return []
                    
                    # Convert chunk UUIDs to int64 for Milvus lookup
                    chunk_uuid_to_int64 = {}
                    milvus_ids = []
                    for chunk in chunks_from_docs:
                        milvus_id = DatabaseManager._uuid_to_int64(chunk.id)
                        chunk_uuid_to_int64[milvus_id] = chunk.id
                        milvus_ids.append(milvus_id)
                    
                    print(f"   Querying Milvus for {len(milvus_ids)} specific chunk vectors")
                    
                    # Create a set for fast lookup
                    milvus_ids_set = set(milvus_ids)
                    
                    # Since Milvus search doesn't support filtering by IDs directly,
                    # we'll search with a limit based on the number of chunks we need
                    # This is still more efficient than searching the entire collection
                    search_limit = min(len(milvus_ids) * 3, 1000)  # Search enough to likely get all our chunks
                    
                    # Use search to get vectors with similarity scores
                    search_results = self.db_manager.milvus_client.search(
                        collection_name=self.db_manager.collection_name,
                        data=[query_embedding],
                        limit=search_limit,
                        output_fields=["id", "document_id", "chunk_index"]
                    )
                    
                    # Filter search results to only include chunks from mentioned documents
                    filtered_results = []
                    if search_results and len(search_results) > 0:
                        for hit in search_results[0]:  # search returns list of lists
                            # Extract ID and metadata from hit
                            hit_id = None
                            document_id = None
                            chunk_index = None
                            distance = 0
                            
                            if isinstance(hit, dict):
                                hit_id = hit.get("id")
                                distance = hit.get("distance", 0)
                                entity = hit.get("entity", {})
                                if isinstance(entity, dict):
                                    document_id = entity.get("document_id")
                                    chunk_index = entity.get("chunk_index")
                                else:
                                    document_id = hit.get("document_id")
                                    chunk_index = hit.get("chunk_index")
                            else:
                                hit_id = getattr(hit, "id", None)
                                distance = getattr(hit, "distance", 0)
                                document_id = getattr(hit, "document_id", None)
                                chunk_index = getattr(hit, "chunk_index", None)
                            
                            # Check if this chunk is from a mentioned document
                            if hit_id in milvus_ids_set:
                                filtered_results.append({
                                    "id": hit_id,
                                    "document_id": document_id,
                                    "chunk_index": chunk_index,
                                    "distance": distance
                                })
                    
                    if not filtered_results:
                        print(f"⚠️  No vectors found in Milvus for mentioned documents")
                        return []
                    
                    print(f"   Retrieved {len(filtered_results)} relevant vectors from Milvus")
                    
                    # Process filtered results and get chunks from PostgreSQL
                    chunk_scores = []
                    for result in filtered_results:
                        milvus_id = result["id"]
                        chunk_uuid = chunk_uuid_to_int64.get(milvus_id)
                        
                        if not chunk_uuid:
                            continue
                        
                        # Get the chunk from PostgreSQL
                        chunk = db.query(Chunk).filter(Chunk.id == chunk_uuid).first()
                        if not chunk:
                            continue
                        
                        # Get distance from Milvus search result
                        distance = result.get("distance", 0)
                        
                        # Convert distance to similarity score
                        if MILVUS_METRIC_TYPE == "L2":
                            score = 1 / (1 + distance) if distance > 0 else 1.0
                        else:
                            score = 1 - distance  # For cosine similarity
                        
                        # Filter by similarity threshold
                        if score >= RAG_SIMILARITY_THRESHOLD:
                            chunk_scores.append({
                                "chunk": chunk,
                                "distance": distance,
                                "score": score
                            })
                    
                    # Sort by score (descending) and take top_k
                    chunk_scores.sort(key=lambda x: x["score"], reverse=True)
                    chunk_scores = chunk_scores[:top_k]
                    
                    # Convert to SearchResult format
                    for item in chunk_scores:
                        chunk = item["chunk"]
                        search_result = SearchResult(
                            id=chunk.id,  # PostgreSQL UUID string
                            document_id=chunk.document_id,
                            chunk_index=chunk.chunk_index,
                            text=chunk.text,
                            distance=item["distance"],
                            score=item["score"]
                        )
                        similar_chunks.append(search_result)
                    
                    print(f"✅ Found {len(similar_chunks)} relevant chunks from {len(document_ids)} mentioned documents")
                    return similar_chunks
                
                # Normal search: Search entire Milvus collection
                search_limit = max(top_k * 2, 10)  # At least 10, or 2x top_k
                results = self.db_manager.search_vectors(
                    query_vector=query_embedding,
                    top_k=search_limit,
                    output_fields=["document_id", "chunk_index"]  # No text field - retrieve from PostgreSQL
                )
                
                print(f"🔍 Requested {search_limit} results from Milvus (target: {top_k} chunks)")
                
                if results:
                    print(f"🔍 Milvus returned {len(results)} results (requested top_k={top_k})")
                    print(f"   First result structure: {type(results[0]) if results else 'N/A'}")
                    if results and len(results) > 0:
                        print(f"   Sample result keys: {list(results[0].keys()) if isinstance(results[0], dict) else 'Not a dict'}")
                    
                    for idx, hit in enumerate(results):
                        # Milvus Lite returns results - check different possible formats
                        # Format 1: Direct dict with fields
                        if isinstance(hit, dict):
                            # Try direct access first
                            distance = hit.get("distance", hit.get("id", 0))
                            document_id = hit.get("document_id")
                            chunk_index = hit.get("chunk_index")
                            
                            # If not found, try entity structure
                            if not document_id:
                                entity = hit.get("entity", {})
                                document_id = entity.get("document_id") if isinstance(entity, dict) else None
                                chunk_index = entity.get("chunk_index") if isinstance(entity, dict) else chunk_index
                                if not distance or distance == 0:
                                    distance = hit.get("distance", 0)
                        else:
                            # Format 2: Object with attributes
                            distance = getattr(hit, "distance", 0)
                            document_id = getattr(hit, "document_id", None)
                            chunk_index = getattr(hit, "chunk_index", None)
                        
                        if not document_id or chunk_index is None:
                            print(f"⚠️  Skipping result {idx}: missing document_id or chunk_index")
                            print(f"   Hit structure: {hit}")
                            continue
                        
                        # Filter by document_ids if provided (for @ mentions)
                        if document_ids and document_id not in document_ids:
                            print(f"⏭️  Skipping chunk from non-mentioned document: doc={document_id}")
                            continue
                        
                        # Retrieve text from PostgreSQL using document_id and chunk_index
                        chunk = db.query(Chunk).filter(
                            Chunk.document_id == document_id,
                            Chunk.chunk_index == chunk_index
                        ).first()
                        
                        if not chunk:
                            print(f"⚠️  Chunk not found in PostgreSQL: doc={document_id}, index={chunk_index}")
                            # Continue to next result instead of stopping
                            continue
                        
                        # Convert distance to similarity score
                        # For L2: lower is better, for cosine: higher is better
                        if MILVUS_METRIC_TYPE == "L2":
                            score = 1 / (1 + distance) if distance > 0 else 1.0
                        else:
                            score = 1 - distance  # For cosine similarity
                        
                        # Filter by similarity threshold
                        if score >= RAG_SIMILARITY_THRESHOLD:
                            # Use PostgreSQL chunk ID (UUID string), not Milvus int64 ID
                            search_result = SearchResult(
                                id=chunk.id,  # PostgreSQL UUID string, not Milvus int64
                                document_id=document_id,
                                chunk_index=chunk_index,
                                text=chunk.text,  # Retrieved from PostgreSQL
                                distance=distance,
                                score=score
                            )
                            similar_chunks.append(search_result)
                            print(f"✅ Added chunk {len(similar_chunks)}/{top_k}: doc={document_id}, index={chunk_index}, score={score:.3f}")
                            
                            # Stop once we have enough chunks
                            if len(similar_chunks) >= top_k:
                                print(f"✅ Reached target of {top_k} chunks, stopping search")
                                break
                        else:
                            print(f"⚠️  Chunk filtered by threshold: score={score:.3f} < threshold={RAG_SIMILARITY_THRESHOLD}")
                    
                    print(f"📊 Final result: {len(similar_chunks)} chunks (requested: {top_k})")
                    if len(similar_chunks) < top_k:
                        print(f"⚠️  Warning: Only {len(similar_chunks)} chunks returned, expected {top_k}")
                        print(f"   This may be due to:")
                        print(f"   - Missing chunks in PostgreSQL (check synchronization)")
                        print(f"   - Similarity threshold too high (current: {RAG_SIMILARITY_THRESHOLD})")
                        print(f"   - Not enough vectors in Milvus")
                else:
                    print(f"⚠️  No results returned from Milvus search (top_k={top_k})")
            finally:
                db.close()
            
            return similar_chunks
            
        except Exception as e:
            print(f"Error searching similar chunks: {e}")
            return []
    
    def get_document_text(self, document_id: str) -> Optional[str]:
        """Retrieve full document text from PostgreSQL"""
        db = self.db_manager.get_session()
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            return document.full_text if document else None
        finally:
            db.close()
    
    def delete_document(self, document_id: str):
        """Delete document and all its chunks from both databases"""
        self.db_manager.delete_document(document_id)
    
    def clean_all_databases(self):
        """Clean all data from both databases"""
        self.db_manager.clean_all()
    
    def verify_synchronization(self) -> VerificationResult:
        """Verify that PostgreSQL and Milvus databases are synchronized"""
        return self.db_manager.verify()
    
    def resync_databases(self) -> ResyncResult:
        """
        Resynchronize databases by ensuring all PostgreSQL chunks exist in Milvus
        This will re-insert any missing vectors into Milvus
        """
        db = self.db_manager.get_session()
        resync_result = ResyncResult(
            success=True,
            documents_processed=0,
            chunks_processed=0,
            vectors_inserted=0,
            errors=[]
        )
        
        try:
            print("🔄 Resynchronizing databases...")
            
            # Get all documents and chunks from PostgreSQL
            documents = db.query(Document).all()
            all_chunks = db.query(Chunk).all()
            
            # Get existing vectors from Milvus
            existing_vector_ids = set()
            if self.db_manager.milvus_client.has_collection(self.db_manager.collection_name):
                try:
                    existing_vectors = self.db_manager.milvus_client.query(
                        collection_name=self.db_manager.collection_name,
                        filter="",
                        limit=10000,
                        output_fields=["id"]
                    )
                    if existing_vectors:
                        existing_vector_ids = {v.get("id") if isinstance(v, dict) else getattr(v, "id", None) for v in existing_vectors}
                except Exception as e:
                    resync_result.errors.append(f"Could not query existing Milvus vectors: {e}")
            
            # Process each document
            for doc in documents:
                doc_chunks = [c for c in all_chunks if c.document_id == doc.id]
                chunks_to_insert: List[VectorData] = []
                
                for chunk in doc_chunks:
                    chunk_id_int = self.db_manager._uuid_to_int64(chunk.id)
                    
                    # Check if vector already exists in Milvus
                    if chunk_id_int not in existing_vector_ids:
                        # Generate embedding and prepare for insertion
                        embedding = self.generate_embedding(chunk.text)
                        vector_data = VectorData(
                            id=chunk_id_int,
                            vector=embedding,  # Only embedding stored in Milvus
                            document_id=doc.id,
                            chunk_index=chunk.chunk_index
                            # Note: text is NOT stored in Milvus, only in PostgreSQL
                        )
                        chunks_to_insert.append(vector_data)
                
                # Insert missing vectors
                if chunks_to_insert:
                    try:
                        self.db_manager.insert_vectors(chunks_to_insert)
                        resync_result.vectors_inserted += len(chunks_to_insert)
                        print(f"   Inserted {len(chunks_to_insert)} missing vectors for document: {doc.filename}")
                    except Exception as e:
                        resync_result.errors.append(f"Error inserting vectors for document {doc.id}: {e}")
                        resync_result.success = False
                
                resync_result.chunks_processed += len(doc_chunks)
                resync_result.documents_processed += 1
            
            print(f"✅ Resynchronization complete: {resync_result.vectors_inserted} vectors inserted")
            
        except Exception as e:
            resync_result.success = False
            resync_result.errors.append(f"Error during resynchronization: {e}")
            print(f"❌ Resynchronization failed: {e}")
        finally:
            db.close()
        
        return resync_result
    
    @property
    def SessionLocal(self):
        """Compatibility property for existing code"""
        return self.db_manager.SessionLocal
