"""
Configuration file for Chatbox App
All constants and configurable parameters are defined here
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# RAG System Configuration
# ============================================

# Chunking Strategy
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "500"))  # Characters per chunk
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))  # Overlap between chunks
CHUNK_MIN_SIZE = int(os.getenv("RAG_CHUNK_MIN_SIZE", "100"))  # Minimum chunk size

# Embedding Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))  # Dimension for ada-002

# Retrieval Configuration
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))  # Number of chunks to retrieve
RAG_SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.0"))  # Minimum similarity score

# Milvus Lite Configuration (local/embedded version)
MILVUS_LITE_PATH = os.getenv("MILVUS_LITE_PATH", "./milvus_lite.db")  # Local file path for Milvus Lite
MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION", "chatbox_vectors")
MILVUS_METRIC_TYPE = os.getenv("MILVUS_METRIC_TYPE", "L2")  # Distance metric: L2, IP, COSINE

# ============================================
# LLM Configuration
# ============================================

# Chat Completion Parameters
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "500"))
LLM_TOP_P = float(os.getenv("LLM_TOP_P", "1.0"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "60.0"))  # Timeout in seconds for API calls

# ============================================
# File Upload Configuration
# ============================================

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))  # 10MB default

# ============================================
# Database Configuration
# ============================================

# PostgreSQL
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# ============================================
# Session Configuration
# ============================================

SESSIONS_DIR = os.getenv("SESSIONS_DIR", "./sessions")

# ============================================
# Database Configuration (PostgreSQL)
# ============================================

POSTGRES_DB = os.getenv("POSTGRES_DB", "chatbox_rag")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

# ============================================
# Backup Configuration
# ============================================

BACKUP_DIR = os.getenv("BACKUP_DIR", "./backups")
BACKUP_ON_SHUTDOWN = os.getenv("BACKUP_ON_SHUTDOWN", "true").lower() == "true"
RESTORE_ON_START = os.getenv("RESTORE_ON_START", "false").lower() == "true"

# ============================================
# Feature Flags
# ============================================

RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() == "true"
