# Database Package

This package contains all database-related functionality for the RAG (Retrieval-Augmented Generation) system, including PostgreSQL and Milvus Lite management, synchronization, and verification.

## 📁 Structure

```
database/
├── __init__.py              # Package initialization
├── database_manager.py      # Core database management class
├── models.py                # Data classes for type-safe data handling
├── verify_databases.py      # Database verification and CSV export script
├── README.md               # This file
├── QUICK_START.md          # Quick reference guide
└── DATA_CLASSES.md         # Data classes documentation
```

## 📦 Data Classes

All data structures use Python data classes for type safety and consistency:

- **DocumentData**: Complete document information
- **ChunkData**: Text chunk with metadata
- **VectorData**: Vector embedding for Milvus
- **SearchResult**: Search results with similarity scores
- **VerificationResult**: Database verification status
- **ResyncResult**: Resynchronization operation results
- **DocumentListItem**: Lightweight document for lists

See [DATA_CLASSES.md](DATA_CLASSES.md) for detailed documentation.

## 🏗️ Architecture

The database system uses a dual-database architecture:

### PostgreSQL
- **Purpose**: Stores all text data and metadata
- **Tables**:
  - `documents`: Full document information (filename, text, hash, metadata)
  - `chunks`: Text chunks with indexing information
- **Data Stored**: Full text, filenames, hashes, timestamps, chunk indices

### Milvus Lite
- **Purpose**: Stores vector embeddings for fast similarity search
- **Collection**: `chatbox_vectors` (configurable)
- **Data Stored**: 
  - `id` (int64): Chunk identifier (hashed UUID)
  - `vector` (float array): Embedding vector
  - `document_id` (string): Reference to document
  - `chunk_index` (int): Position in document
  - **Note**: Text is NOT stored in Milvus, only embeddings

### Design Principle
- **Milvus**: Embeddings only (for fast vector search)
- **PostgreSQL**: All text data (single source of truth)

## 🔧 Setup

### Prerequisites

1. **PostgreSQL**: Running in Docker container
   ```bash
   cd backend
   bash setup_databases.sh
   ```

2. **Environment Variables**: Configure in `backend/.env`
   ```env
   # PostgreSQL Configuration
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=chatbox_rag
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres

   # Milvus Lite Configuration
   MILVUS_LITE_PATH=./milvus_lite.db
   MILVUS_COLLECTION=chatbox_vectors
   MILVUS_METRIC_TYPE=L2
   EMBEDDING_DIM=1536
   ```

### Installation

The database package is automatically available when the backend is set up:

```bash
cd backend
pip install -r requirements.txt
```

## 📚 Usage

### DatabaseManager Class

The `DatabaseManager` class handles all database operations:

```python
from database import DatabaseManager

# Initialize
db_manager = DatabaseManager()
db_manager.initialize()

# Get a database session
db = db_manager.get_session()

# Insert vectors into Milvus
vectors_data = [
    {
        "id": 1234567890,  # int64
        "vector": [0.1, 0.2, ...],  # embedding
        "document_id": "doc-uuid",
        "chunk_index": 0
    }
]
db_manager.insert_vectors(vectors_data)

# Search vectors
results = db_manager.search_vectors(
    query_vector=[0.1, 0.2, ...],
    top_k=5,
    output_fields=["document_id", "chunk_index"]
)

# Verify databases
verification = db_manager.verify()

# Clean all data
db_manager.clean_all()

# Delete a document
db_manager.delete_document("document-id")
```

### Models

#### Document Model
```python
from database import Document

# Document fields:
# - id: str (UUID)
# - filename: str
# - full_text: str
# - file_hash: str (MD5)
# - created_at: datetime
# - chunk_count: int
```

#### Chunk Model
```python
from database import Chunk

# Chunk fields:
# - id: str (UUID)
# - document_id: str
# - chunk_index: int
# - text: str
# - created_at: datetime
```

## 🔍 Verification Script

### Basic Usage

```bash
cd backend
python database/verify_databases.py
```

### Export to CSV

```bash
# Default output (database_verification.csv)
python database/verify_databases.py

# Custom output file
python database/verify_databases.py --output my_report.csv
python database/verify_databases.py -o my_report.csv

# Skip CSV export (console only)
python database/verify_databases.py --no-export
```

### CSV Output Format

The CSV includes synchronized data from both databases:

| Column | Description |
|--------|-------------|
| `document_id` | Document UUID |
| `document_filename` | Original filename |
| `document_created_at` | Creation timestamp |
| `document_file_hash` | MD5 hash |
| `document_chunk_count` | Number of chunks |
| `document_full_text_length` | Full text length |
| `postgres_chunk_id` | PostgreSQL chunk UUID |
| `postgres_chunk_index` | Chunk position |
| `postgres_chunk_text` | **Full chunk text** |
| `postgres_chunk_created_at` | Chunk creation time |
| `postgres_exists` | Yes/No |
| `milvus_vector_id` | Milvus vector ID (int64) |
| `milvus_chunk_index` | Chunk index in Milvus |
| `milvus_exists` | Yes/No |
| `synchronized` | Yes/No |
| `sync_notes` | Status notes |

## 🌐 API Endpoints

### List Documents

```bash
curl -X GET http://localhost:8000/api/documents
```

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "filename": "example.txt",
      "chunk_count": 10,
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

### Delete Document

```bash
curl -X DELETE http://localhost:8000/api/documents/{document_id}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Document {document_id} deleted"
}
```

### Clean All Databases

```bash
curl -X DELETE http://localhost:8000/api/documents
```

**Response:**
```json
{
  "status": "ok",
  "message": "All documents cleaned from both databases"
}
```

### Check Synchronization

```bash
curl -X GET http://localhost:8000/api/documents/sync
```

**Response:**
```json
{
  "postgres_connected": true,
  "milvus_connected": true,
  "synchronized": true,
  "postgres_documents": 5,
  "postgres_chunks": 50,
  "milvus_vectors": 50,
  "issues": []
}
```

### Resynchronize Databases

```bash
curl -X POST http://localhost:8000/api/documents/resync
```

**Response:**
```json
{
  "success": true,
  "documents_processed": 5,
  "chunks_processed": 50,
  "vectors_inserted": 0,
  "errors": []
}
```

## 📝 Script Examples

### Python Script: Verify Databases

```python
#!/usr/bin/env python3
from database import DatabaseManager

# Initialize
db_manager = DatabaseManager()
db_manager.initialize()

# Verify
result = db_manager.verify()
print(f"PostgreSQL: {result['postgres_connected']}")
print(f"Milvus: {result['milvus_connected']}")
print(f"Synchronized: {result['synchronized']}")
print(f"PostgreSQL chunks: {result['postgres_chunks']}")
print(f"Milvus vectors: {result['milvus_vectors']}")

if result['issues']:
    print("Issues found:")
    for issue in result['issues']:
        print(f"  - {issue}")
```

### Python Script: Clean Databases

```python
#!/usr/bin/env python3
from database import DatabaseManager

db_manager = DatabaseManager()
db_manager.initialize()
db_manager.clean_all()
print("All databases cleaned")
```

### Python Script: Export to CSV

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from database import DatabaseManager
from database.verify_databases import export_to_csv

db_manager = DatabaseManager()
db_manager.initialize()
export_to_csv(db_manager, "my_export.csv")
```

## 🔄 Synchronization

### How It Works

1. **Storage**: When a document is stored:
   - Text → PostgreSQL (chunks table)
   - Embeddings → Milvus (vectors)

2. **Search**: When searching:
   - Query → Generate embedding
   - Search Milvus → Get similar vectors (with document_id, chunk_index)
   - Query PostgreSQL → Retrieve text using document_id and chunk_index

3. **Synchronization**: Records are matched by `(document_id, chunk_index)`

### Verification

The verification process checks:
- Connection status for both databases
- Record counts match
- Each PostgreSQL chunk has a corresponding Milvus vector
- Identifies missing records in either database

### Resynchronization

If databases are out of sync:
1. Identifies missing vectors in Milvus
2. Generates embeddings for missing chunks
3. Inserts missing vectors into Milvus
4. Reports results

## 🛠️ Troubleshooting

### PostgreSQL Connection Issues

```bash
# Check if container is running
docker ps -a --filter 'name=chatbox-postgres'

# Start container if stopped
docker start chatbox-postgres

# Check logs
docker logs chatbox-postgres
```

### Milvus Issues

```bash
# Check if database file exists
ls -la backend/milvus_lite.db

# Verify pymilvus version
pip show pymilvus

# Upgrade if needed
pip install --upgrade 'pymilvus>=2.4.2'
```

### Synchronization Issues

```bash
# Check synchronization status
curl http://localhost:8000/api/documents/sync

# Resynchronize if needed
curl -X POST http://localhost:8000/api/documents/resync

# Export to CSV for analysis
python database/verify_databases.py -o sync_report.csv
```

## 📊 Database Schema

### PostgreSQL Schema

```sql
-- Documents table
CREATE TABLE documents (
    id VARCHAR PRIMARY KEY,
    filename VARCHAR NOT NULL,
    full_text TEXT NOT NULL,
    file_hash VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    chunk_count INTEGER DEFAULT 0
);

-- Chunks table
CREATE TABLE chunks (
    id VARCHAR PRIMARY KEY,
    document_id VARCHAR NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chunks_document_id ON chunks(document_id);
```

### Milvus Schema

```
Collection: chatbox_vectors
Fields:
  - id: int64 (primary key, hashed from UUID)
  - vector: float vector (dimension: 1536)
  - document_id: varchar
  - chunk_index: int32
```

## 🔐 Security Notes

- PostgreSQL credentials are stored in `.env` file (never commit this)
- Milvus Lite is local file-based (no network access needed)
- Use environment variables for all sensitive configuration
- Database connections use connection pooling

## 📖 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Milvus Documentation](https://milvus.io/docs)
- [pymilvus Documentation](https://milvus.io/api-reference/pymilvus/v2.4.x/About.md)

## 🐛 Common Issues

### Issue: "Connection refused" to PostgreSQL
**Solution**: Ensure Docker container is running
```bash
docker start chatbox-postgres
```

### Issue: "Illegal uri" for Milvus
**Solution**: Ensure path ends with `.db` and pymilvus >= 2.4.2
```bash
pip install --upgrade 'pymilvus>=2.4.2'
```

### Issue: Count mismatch between databases
**Solution**: Run resynchronization
```bash
curl -X POST http://localhost:8000/api/documents/resync
```

### Issue: Text not found in search results
**Solution**: Ensure text is retrieved from PostgreSQL (not Milvus). The system automatically does this, but verify the chunk exists in PostgreSQL.

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Run verification script: `python database/verify_databases.py`
3. Check API status: `curl http://localhost:8000/api/documents/sync`
4. Review logs in the backend console

