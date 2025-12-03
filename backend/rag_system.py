"""
RAG (Retrieval-Augmented Generation) System
Uses Milvus Lite for vector search and PostgreSQL for full text storage
"""
import os
import uuid
import hashlib
from typing import List, Optional, Dict
from datetime import datetime
from pymilvus import MilvusClient
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import (
    CHUNK_SIZE, CHUNK_OVERLAP, CHUNK_MIN_SIZE,
    EMBEDDING_MODEL, EMBEDDING_DIM,
    RAG_TOP_K, RAG_SIMILARITY_THRESHOLD,
    MILVUS_METRIC_TYPE,
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
    MILVUS_LITE_PATH, MILVUS_COLLECTION
)

Base = declarative_base()


# PostgreSQL Models
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    full_text = Column(Text, nullable=False)
    file_hash = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    chunk_count = Column(Integer, default=0)


class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(String, primary_key=True)
    document_id = Column(String, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class RAGSystem:
    def __init__(self, openai_client, embedding_model: Optional[str] = None, use_azure: bool = False):
        self.openai_client = openai_client
        self.embedding_model = embedding_model or EMBEDDING_MODEL
        self.embedding_dim = EMBEDDING_DIM
        self.use_azure = use_azure
        
        # Initialize PostgreSQL
        self._init_postgres()
        
        # Initialize Milvus Lite
        self._init_milvus()
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection"""
        db_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        self.engine = create_engine(db_url, pool_pre_ping=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        print(f"✅ Connected to PostgreSQL: {POSTGRES_DB}")
    
    def _init_milvus(self):
        """Initialize Milvus Lite (local/embedded version)"""
        # Use Milvus Lite with local file storage
        self.milvus_client = MilvusClient(uri=MILVUS_LITE_PATH)
        print(f"✅ Initialized Milvus Lite: {MILVUS_LITE_PATH}")
        
        # Check if collection exists, create if not
        if not self.milvus_client.has_collection(MILVUS_COLLECTION):
            # Create collection with vector dimension
            self.milvus_client.create_collection(
                collection_name=MILVUS_COLLECTION,
                dimension=self.embedding_dim,
                metric_type=MILVUS_METRIC_TYPE
            )
            print(f"✅ Created Milvus Lite collection: {MILVUS_COLLECTION}")
            print(f"   Metric: {MILVUS_METRIC_TYPE}, Dimension: {self.embedding_dim}")
        else:
            print(f"✅ Using existing Milvus Lite collection: {MILVUS_COLLECTION}")
        
        self.collection_name = MILVUS_COLLECTION
    
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
        db: Session = self.SessionLocal()
        
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
            insert_data = []
            for idx, chunk_text in enumerate(chunks):
                embedding = self.generate_embedding(chunk_text)
                chunk_id = chunk_records[idx].id
                
                insert_data.append({
                    "id": chunk_id,
                    "vector": embedding,
                    "document_id": doc_id,
                    "chunk_index": idx,
                    "text": chunk_text[:65535]  # Limit text length
                })
            
            # Insert into Milvus Lite
            if insert_data:
                self.milvus_client.insert(
                    collection_name=self.collection_name,
                    data=insert_data
                )
                print(f"✅ Stored {len(insert_data)} chunks in Milvus Lite")
            
            print(f"✅ Stored document: {filename} (ID: {doc_id})")
            return doc_id
            
        except Exception as e:
            db.rollback()
            print(f"Error storing document: {e}")
            raise
        finally:
            db.close()
    
    def search_similar(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """
        Search for similar chunks using vector similarity
        Returns list of relevant chunks with metadata
        Uses config values if top_k not provided
        """
        top_k = top_k or RAG_TOP_K
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Search in Milvus Lite
            results = self.milvus_client.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                limit=top_k,
                output_fields=["document_id", "chunk_index", "text"]
            )
            
            # Format results and filter by similarity threshold
            similar_chunks = []
            if results and len(results) > 0:
                for hit in results[0]:
                    # Milvus Lite returns results with distance and entity fields
                    distance = hit.get("distance", 0)
                    entity = hit.get("entity", {})
                    
                    # Convert distance to similarity score
                    # For L2: lower is better, for cosine: higher is better
                    if MILVUS_METRIC_TYPE == "L2":
                        score = 1 / (1 + distance)
                    else:
                        score = 1 - distance  # For cosine similarity
                    
                    # Filter by similarity threshold
                    if score >= RAG_SIMILARITY_THRESHOLD:
                        similar_chunks.append({
                            "id": hit.get("id"),
                            "document_id": entity.get("document_id"),
                            "chunk_index": entity.get("chunk_index"),
                            "text": entity.get("text"),
                            "distance": distance,
                            "score": score
                        })
            
            return similar_chunks
            
        except Exception as e:
            print(f"Error searching similar chunks: {e}")
            return []
    
    def get_document_text(self, document_id: str) -> Optional[str]:
        """Retrieve full document text from PostgreSQL"""
        db: Session = self.SessionLocal()
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            return document.full_text if document else None
        finally:
            db.close()
    
    def delete_document(self, document_id: str):
        """Delete document and all its chunks"""
        db: Session = self.SessionLocal()
        try:
            # Get chunk IDs before deleting from PostgreSQL
            chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()
            chunk_ids = [chunk.id for chunk in chunks]
            
            # Delete from PostgreSQL
            db.query(Chunk).filter(Chunk.document_id == document_id).delete()
            db.query(Document).filter(Document.id == document_id).delete()
            db.commit()
            
            # Delete from Milvus Lite
            if chunk_ids:
                self.milvus_client.delete(
                    collection_name=self.collection_name,
                    ids=chunk_ids
                )
            
            print(f"✅ Deleted document: {document_id}")
        except Exception as e:
            db.rollback()
            print(f"Error deleting document: {e}")
            raise
        finally:
            db.close()
