"""
Data classes for database operations
These are used for data transfer and business logic, separate from SQLAlchemy ORM models
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class DocumentData:
    """Data class for document information"""
    id: str
    filename: str
    full_text: str
    file_hash: str
    created_at: Optional[datetime] = None
    chunk_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "filename": self.filename,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "file_hash": self.file_hash,
            "full_text_length": len(self.full_text)
        }
    
    @classmethod
    def from_orm(cls, orm_doc) -> 'DocumentData':
        """Create from SQLAlchemy ORM model"""
        return cls(
            id=orm_doc.id,
            filename=orm_doc.filename,
            full_text=orm_doc.full_text,
            file_hash=orm_doc.file_hash,
            created_at=orm_doc.created_at,
            chunk_count=orm_doc.chunk_count
        )


@dataclass
class ChunkData:
    """Data class for chunk information"""
    id: str
    document_id: str
    chunk_index: int
    text: str
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "text_length": len(self.text)
        }
    
    @classmethod
    def from_orm(cls, orm_chunk) -> 'ChunkData':
        """Create from SQLAlchemy ORM model"""
        return cls(
            id=orm_chunk.id,
            document_id=orm_chunk.document_id,
            chunk_index=orm_chunk.chunk_index,
            text=orm_chunk.text,
            created_at=orm_chunk.created_at
        )


@dataclass
class VectorData:
    """Data class for Milvus vector data"""
    id: int  # int64 for Milvus
    vector: List[float]
    document_id: str
    chunk_index: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Milvus insertion"""
        return {
            "id": self.id,
            "vector": self.vector,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index
        }


@dataclass
class SearchResult:
    """Data class for search results"""
    id: int
    document_id: str
    chunk_index: int
    text: str
    distance: float
    score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "distance": self.distance,
            "score": self.score
        }


@dataclass
class VerificationResult:
    """Data class for database verification results"""
    postgres_connected: bool
    milvus_connected: bool
    synchronized: bool
    postgres_documents: int
    postgres_chunks: int
    milvus_vectors: int
    issues: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "postgres_connected": self.postgres_connected,
            "milvus_connected": self.milvus_connected,
            "synchronized": self.synchronized,
            "postgres_documents": self.postgres_documents,
            "postgres_chunks": self.postgres_chunks,
            "milvus_vectors": self.milvus_vectors,
            "issues": self.issues,
            "details": self.details
        }


@dataclass
class ResyncResult:
    """Data class for resynchronization results"""
    success: bool
    documents_processed: int
    chunks_processed: int
    vectors_inserted: int
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "success": self.success,
            "documents_processed": self.documents_processed,
            "chunks_processed": self.chunks_processed,
            "vectors_inserted": self.vectors_inserted,
            "errors": self.errors
        }


@dataclass
class DocumentListItem:
    """Data class for document list items (lightweight)"""
    id: str
    filename: str
    chunk_count: int
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "filename": self.filename,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_orm(cls, orm_doc) -> 'DocumentListItem':
        """Create from SQLAlchemy ORM model"""
        return cls(
            id=orm_doc.id,
            filename=orm_doc.filename,
            chunk_count=orm_doc.chunk_count,
            created_at=orm_doc.created_at
        )

