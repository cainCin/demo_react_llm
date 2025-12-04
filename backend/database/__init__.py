"""
Database package for RAG System
Contains database management, models, and verification tools
"""
from .database_manager import DatabaseManager, Document, Chunk, Base
from .models import (
    DocumentData,
    ChunkData,
    VectorData,
    SearchResult,
    VerificationResult,
    ResyncResult,
    DocumentListItem
)

__all__ = [
    # ORM Models (for database operations)
    'DatabaseManager',
    'Document',
    'Chunk',
    'Base',
    # Data Classes (for business logic)
    'DocumentData',
    'ChunkData',
    'VectorData',
    'SearchResult',
    'VerificationResult',
    'ResyncResult',
    'DocumentListItem'
]

