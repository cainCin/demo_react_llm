"""
RAG (Retrieval-Augmented Generation) System
Uses Milvus Lite for vector search and PostgreSQL for full text storage
Database operations are handled by DatabaseManager
"""
import uuid
import hashlib
from typing import List, Optional, Dict
from database import (
    DatabaseManager, Document, Chunk,
    DocumentData, ChunkData, VectorData, SearchResult,
    VerificationResult, ResyncResult
)
from config import (
    CHUNK_SIZE, CHUNK_OVERLAP, CHUNK_MIN_SIZE,
    EMBEDDING_MODEL, EMBEDDING_DIM,
    RAG_TOP_K, RAG_SIMILARITY_THRESHOLD,
    MILVUS_METRIC_TYPE
)


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
        Uses config values if parameters not provided
        """
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
                # Look for sentence endings
                for break_char in ['. ', '.\n', '! ', '!\n', '? ', '?\n', '\n\n']:
                    last_break = chunk.rfind(break_char)
                    if last_break > chunk_size * 0.5:  # Only break if we're past halfway
                        chunk = chunk[:last_break + len(break_char)]
                        end = start + len(chunk)
                        break
            
            # Only add chunk if it meets minimum size requirement
            chunk_text = chunk.strip()
            if len(chunk_text) >= CHUNK_MIN_SIZE or start == 0:  # Always include first chunk
                chunks.append(chunk_text)
            
            # Move start position with overlap
            start = end - chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
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
            
            # Chunk the text
            chunks = self.chunk_text(text)
            print(f"Created {len(chunks)} chunks for {filename}")
            
            # Store document in PostgreSQL
            document = Document(
                id=doc_id,
                filename=filename,
                full_text=text,
                file_hash=file_hash,
                chunk_count=len(chunks)
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
    
    def search_similar(self, query: str, top_k: Optional[int] = None) -> List[SearchResult]:
        """
        Search for similar chunks using vector similarity
        Returns list of SearchResult objects with metadata
        Text is retrieved from PostgreSQL, not Milvus
        Uses config values if top_k not provided
        """
        top_k = top_k or RAG_TOP_K
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Search in Milvus Lite using database manager (only get IDs and indices, no text)
            results = self.db_manager.search_vectors(
                query_vector=query_embedding,
                top_k=top_k,
                output_fields=["document_id", "chunk_index"]  # No text field - retrieve from PostgreSQL
            )
            
            # Format results and retrieve text from PostgreSQL
            similar_chunks: List[SearchResult] = []
            db = self.db_manager.get_session()
            
            try:
                if results:
                    for hit in results:
                        # Milvus Lite returns results with distance and entity fields
                        distance = hit.get("distance", 0)
                        entity = hit.get("entity", {})
                        
                        document_id = entity.get("document_id")
                        chunk_index = entity.get("chunk_index")
                        
                        # Retrieve text from PostgreSQL using document_id and chunk_index
                        chunk = db.query(Chunk).filter(
                            Chunk.document_id == document_id,
                            Chunk.chunk_index == chunk_index
                        ).first()
                        
                        if chunk:
                            # Convert distance to similarity score
                            # For L2: lower is better, for cosine: higher is better
                            if MILVUS_METRIC_TYPE == "L2":
                                score = 1 / (1 + distance)
                            else:
                                score = 1 - distance  # For cosine similarity
                            
                            # Filter by similarity threshold
                            if score >= RAG_SIMILARITY_THRESHOLD:
                                search_result = SearchResult(
                                    id=hit.get("id"),
                                    document_id=document_id,
                                    chunk_index=chunk_index,
                                    text=chunk.text,  # Retrieved from PostgreSQL
                                    distance=distance,
                                    score=score
                                )
                                similar_chunks.append(search_result)
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
