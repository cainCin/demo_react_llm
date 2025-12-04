"""
Database Manager for RAG System
Handles PostgreSQL and Milvus Lite database operations, synchronization, and verification
"""
import os
import hashlib
import struct
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pymilvus import MilvusClient
import sys
import os
# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
    MILVUS_LITE_PATH, MILVUS_COLLECTION, MILVUS_METRIC_TYPE, EMBEDDING_DIM
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


class DatabaseManager:
    """
    Manages PostgreSQL and Milvus Lite databases for the RAG system
    Handles initialization, synchronization, verification, and cleanup
    """
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.milvus_client = None
        self.collection_name = MILVUS_COLLECTION
        self.embedding_dim = EMBEDDING_DIM
        self._postgres_initialized = False
        self._milvus_initialized = False
    
    def initialize(self):
        """Initialize both PostgreSQL and Milvus Lite connections"""
        self._init_postgres()
        self._init_milvus()
        return self._postgres_initialized and self._milvus_initialized
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection"""
        db_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        try:
            self.engine = create_engine(db_url, pool_pre_ping=True)
            Base.metadata.create_all(self.engine)
            self.SessionLocal = sessionmaker(bind=self.engine)
            self._postgres_initialized = True
            print(f"✅ Connected to PostgreSQL: {POSTGRES_DB}")
        except Exception as e:
            error_msg = str(e)
            # Check if it's a connection error
            if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "OperationalError" in str(type(e)):
                troubleshooting = "\n"
                troubleshooting += "   Troubleshooting steps:\n"
                troubleshooting += "   1. Check if PostgreSQL is running:\n"
                troubleshooting += "      docker ps -a --filter 'name=chatbox-postgres'\n"
                troubleshooting += "   2. If container exists but is stopped, start it:\n"
                troubleshooting += "      docker start chatbox-postgres\n"
                troubleshooting += "   3. If container doesn't exist, run the setup script:\n"
                troubleshooting += "      cd backend && bash setup_databases.sh\n"
                troubleshooting += "   4. Verify PostgreSQL is accessible:\n"
                troubleshooting += f"      Check connection to {POSTGRES_HOST}:{POSTGRES_PORT}\n"
                raise ConnectionError(f"Failed to connect to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}\n{error_msg}{troubleshooting}")
            raise
    
    def _init_milvus(self):
        """Initialize Milvus Lite connection"""
        # Convert relative path to absolute path
        milvus_path = os.path.abspath(MILVUS_LITE_PATH)
        
        # Ensure the path ends with .db (Milvus Lite requires this)
        if not milvus_path.endswith('.db'):
            milvus_path = os.path.join(milvus_path, 'milvus_lite.db')
        
        # Ensure the directory exists
        milvus_dir = os.path.dirname(milvus_path)
        if milvus_dir and not os.path.exists(milvus_dir):
            os.makedirs(milvus_dir, exist_ok=True)
        
        # Milvus Lite expects a local file path ending with .db (no file:// prefix needed)
        try:
            self.milvus_client = MilvusClient(uri=milvus_path)
            self._milvus_initialized = True
        except Exception as e:
            error_msg = str(e)
            troubleshooting = "\n"
            troubleshooting += "   Troubleshooting steps:\n"
            troubleshooting += "   1. Ensure pymilvus version supports Milvus Lite (2.4.2+):\n"
            troubleshooting += "      pip install --upgrade 'pymilvus>=2.4.2'\n"
            troubleshooting += "   2. Check MILVUS_LITE_PATH in your .env file\n"
            troubleshooting += f"      Current path: {MILVUS_LITE_PATH}\n"
            troubleshooting += f"      Resolved to: {milvus_path}\n"
            troubleshooting += "   3. Ensure the directory exists and is writable:\n"
            troubleshooting += f"      Directory: {milvus_dir}\n"
            troubleshooting += "   4. For WSL, ensure paths are accessible\n"
            raise ConnectionError(f"Failed to initialize Milvus Lite\n{error_msg}{troubleshooting}")
        
        print(f"✅ Initialized Milvus Lite: {milvus_path}")
        
        # Check if collection exists, create if not
        if not self.milvus_client.has_collection(self.collection_name):
            # Create collection with vector dimension
            # Note: Milvus requires id field to be int64, so we convert UUID strings to int64
            self.milvus_client.create_collection(
                collection_name=self.collection_name,
                dimension=self.embedding_dim,
                metric_type=MILVUS_METRIC_TYPE
            )
            print(f"✅ Created Milvus Lite collection: {self.collection_name}")
            print(f"   Metric: {MILVUS_METRIC_TYPE}, Dimension: {self.embedding_dim}")
            print(f"   Note: IDs are stored as int64 (UUIDs are hashed to int64)")
        else:
            print(f"✅ Using existing Milvus Lite collection: {self.collection_name}")
            print(f"   Note: If you see ID type errors, delete the collection to recreate with correct schema")
    
    @staticmethod
    def _uuid_to_int64(uuid_str: str) -> int:
        """Convert UUID string to int64 for Milvus (uses MD5 hash)"""
        hash_bytes = hashlib.md5(uuid_str.encode()).digest()[:8]
        return struct.unpack('>q', hash_bytes)[0]
    
    def get_session(self) -> Session:
        """Get a new database session"""
        if not self._postgres_initialized:
            raise RuntimeError("PostgreSQL not initialized. Call initialize() first.")
        return self.SessionLocal()
    
    def verify(self) -> 'VerificationResult':
        """
        General verification method - checks both databases and synchronization
        Returns comprehensive verification status as VerificationResult data class
        """
        from database import VerificationResult, DocumentListItem
        
        verification_result = VerificationResult(
            postgres_connected=False,
            milvus_connected=False,
            synchronized=True,
            postgres_documents=0,
            postgres_chunks=0,
            milvus_vectors=0,
            issues=[],
            details={}
        )
        
        # Verify PostgreSQL
        if self._postgres_initialized and self.engine:
            try:
                db = self.get_session()
                try:
                    postgres_docs = db.query(Document).all()
                    postgres_chunks = db.query(Chunk).all()
                    
                    verification_result.postgres_connected = True
                    verification_result.postgres_documents = len(postgres_docs)
                    verification_result.postgres_chunks = len(postgres_chunks)
                    
                    verification_result.details["postgres"] = {
                        "documents": [
                            DocumentListItem.from_orm(doc).to_dict()
                            for doc in postgres_docs
                        ]
                    }
                finally:
                    db.close()
            except Exception as e:
                verification_result.issues.append(f"PostgreSQL verification error: {e}")
        
        # Verify Milvus
        if self._milvus_initialized and self.milvus_client:
            try:
                if self.milvus_client.has_collection(self.collection_name):
                    verification_result.milvus_connected = True
                    
                    # Get collection info
                    try:
                        collection_info = self.milvus_client.describe_collection(self.collection_name)
                        verification_result.details["milvus"] = {
                            "collection_name": collection_info.get('collection_name', 'N/A'),
                            "description": collection_info.get('description', 'N/A')
                        }
                    except:
                        pass
                    
                    # Count vectors
                    try:
                        all_data = self.milvus_client.query(
                            collection_name=self.collection_name,
                            filter="",
                            limit=10000,
                            output_fields=["id", "document_id", "chunk_index"]
                        )
                        verification_result.milvus_vectors = len(all_data) if all_data else 0
                    except Exception as e:
                        verification_result.issues.append(f"Could not query Milvus vectors: {e}")
                else:
                    verification_result.issues.append("Milvus collection does not exist")
            except Exception as e:
                verification_result.issues.append(f"Milvus verification error: {e}")
        
        # Check synchronization
        if verification_result.postgres_chunks != verification_result.milvus_vectors:
            verification_result.synchronized = False
            diff = verification_result.postgres_chunks - verification_result.milvus_vectors
            verification_result.issues.append(
                f"Count mismatch: PostgreSQL has {verification_result.postgres_chunks} chunks, "
                f"Milvus has {verification_result.milvus_vectors} vectors (difference: {diff})"
            )
        
        return verification_result
    
    def clean_all(self):
        """Clean all data from both databases"""
        if not self._postgres_initialized:
            raise RuntimeError("PostgreSQL not initialized")
        if not self._milvus_initialized:
            raise RuntimeError("Milvus not initialized")
        
        db = self.get_session()
        try:
            print("🧹 Cleaning all databases...")
            
            # Get all chunk IDs from PostgreSQL before deletion
            all_chunks = db.query(Chunk).all()
            chunk_ids_str = [chunk.id for chunk in all_chunks]
            
            # Delete all from PostgreSQL
            db.query(Chunk).delete()
            db.query(Document).delete()
            db.commit()
            print(f"✅ Cleared PostgreSQL: {len(all_chunks)} chunks, {len(set(c.document_id for c in all_chunks))} documents")
            
            # Delete all from Milvus Lite
            if chunk_ids_str:
                chunk_ids_int = [self._uuid_to_int64(chunk_id) for chunk_id in chunk_ids_str]
                try:
                    self.milvus_client.delete(
                        collection_name=self.collection_name,
                        ids=chunk_ids_int
                    )
                    print(f"✅ Cleared Milvus Lite: {len(chunk_ids_int)} vectors")
                except Exception as e:
                    print(f"⚠️  Error clearing Milvus Lite: {e}")
                    # Try to drop and recreate collection as fallback
                    try:
                        if self.milvus_client.has_collection(self.collection_name):
                            self.milvus_client.drop_collection(self.collection_name)
                            print("✅ Dropped Milvus collection")
                    except Exception as drop_error:
                        print(f"⚠️  Could not drop collection: {drop_error}")
            
            print("✅ All databases cleaned successfully")
        except Exception as e:
            db.rollback()
            print(f"Error cleaning databases: {e}")
            raise
        finally:
            db.close()
    
    def delete_document(self, document_id: str):
        """Delete a document and all its chunks from both databases"""
        if not self._postgres_initialized:
            raise RuntimeError("PostgreSQL not initialized")
        if not self._milvus_initialized:
            raise RuntimeError("Milvus not initialized")
        
        db = self.get_session()
        try:
            # Get chunk IDs before deleting from PostgreSQL
            chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()
            chunk_ids_str = [chunk.id for chunk in chunks]
            
            # Delete from PostgreSQL first
            db.query(Chunk).filter(Chunk.document_id == document_id).delete()
            db.query(Document).filter(Document.id == document_id).delete()
            db.commit()
            
            # Delete from Milvus Lite (convert UUID strings to int64)
            if chunk_ids_str:
                chunk_ids_int = [self._uuid_to_int64(chunk_id) for chunk_id in chunk_ids_str]
                try:
                    self.milvus_client.delete(
                        collection_name=self.collection_name,
                        ids=chunk_ids_int
                    )
                except Exception as milvus_error:
                    # If Milvus delete fails, rollback PostgreSQL
                    db.rollback()
                    print(f"⚠️  Milvus delete failed, rolling back PostgreSQL: {milvus_error}")
                    raise
            
            print(f"✅ Deleted document: {document_id} from both databases")
        except Exception as e:
            db.rollback()
            print(f"Error deleting document: {e}")
            raise
        finally:
            db.close()
    
    def insert_vectors(self, vectors_data: List['VectorData']):
        """
        Insert vectors into Milvus
        Accepts list of VectorData objects
        Note: text is NOT stored in Milvus, only embeddings. Text is stored in PostgreSQL only.
        """
        if not self._milvus_initialized:
            raise RuntimeError("Milvus not initialized")
        
        if vectors_data:
            # Convert VectorData objects to dicts for Milvus
            clean_data = [vec.to_dict() for vec in vectors_data]
            
            self.milvus_client.insert(
                collection_name=self.collection_name,
                data=clean_data
            )
    
    def search_vectors(self, query_vector: List[float], top_k: int, output_fields: List[str] = None) -> List:
        """
        Search for similar vectors in Milvus
        Note: text is NOT stored in Milvus, only embeddings. Text should be retrieved from PostgreSQL.
        """
        if not self._milvus_initialized:
            raise RuntimeError("Milvus not initialized")
        
        if output_fields is None:
            output_fields = ["document_id", "chunk_index"]  # No text field - retrieve from PostgreSQL
        
        # Remove 'text' from output_fields if present (text is not in Milvus)
        output_fields = [f for f in output_fields if f != "text"]
        
        results = self.milvus_client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            limit=top_k,
            output_fields=output_fields
        )
        
        return results[0] if results and len(results) > 0 else []
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
        # Milvus Lite doesn't need explicit closing
        self._postgres_initialized = False
        self._milvus_initialized = False

