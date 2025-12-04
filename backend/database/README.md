# Database Package

This package contains all database-related functionality for the RAG (Retrieval-Augmented Generation) system, including PostgreSQL and Milvus Lite management, synchronization, and verification.

## 📁 Structure

```
database/
├── __init__.py              # Package initialization
├── database_manager.py      # Core database management class
├── models.py                # Data classes for type-safe data handling
├── verify_databases.py      # Database verification and CSV export script
├── verify_synchronization.py # Data class synchronization verification
├── UML_DIAGRAM.puml         # PlantUML diagram of database architecture
├── SYNCHRONIZATION_REPORT.md # Detailed synchronization verification report
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
  - `vector`: Embedding vector (List[float])
  - `document_id`: Reference to document
  - `chunk_index`: Position in document
- **Important**: Text is **NOT** stored in Milvus, only embeddings

## 🔄 Data Synchronization

### Key Principles

1. **Text Separation**: Text is stored **only** in PostgreSQL, never in Milvus
2. **ID Conversion**: UUID strings (PostgreSQL) are hashed to int64 (Milvus)
3. **Synchronization**: Both databases must be kept in sync
4. **Verification**: Use `verify()` to check synchronization status

### Synchronization Flow

```
Document Upload
    ↓
PostgreSQL: Store Document + Chunks (with text)
    ↓
Generate Embeddings
    ↓
Milvus: Store VectorData (embeddings only, no text)
    ↓
Search Query
    ↓
Milvus: Returns document_id, chunk_index, distance
    ↓
PostgreSQL: Retrieves text using document_id + chunk_index
    ↓
SearchResult: Combines Milvus metadata + PostgreSQL text
```

## 📊 UML Diagram

See [UML_DIAGRAM.puml](UML_DIAGRAM.puml) for a complete PlantUML diagram showing:
- ORM models (Document, Chunk)
- Data classes (DocumentData, ChunkData, VectorData, etc.)
- DatabaseManager relationships
- Data flow between PostgreSQL and Milvus

To view the diagram:
- Use PlantUML: `plantuml UML_DIAGRAM.puml`
- Or use online viewer: http://www.plantuml.com/plantuml/uml/

## ✅ Synchronization Verification

All data classes are verified to be synchronized with their ORM models. See:
- [SYNCHRONIZATION_REPORT.md](SYNCHRONIZATION_REPORT.md) - Detailed verification report
- `verify_synchronization.py` - Automated verification script

### Verification Status

✅ **All data classes are fully synchronized:**
- DocumentData ↔ Document ORM
- ChunkData ↔ Chunk ORM
- DocumentListItem ↔ Document ORM (subset)
- VectorData ↔ Milvus schema
- All classes have `to_dict()` and `from_orm()` methods where applicable

## 🔧 Usage

### Basic Operations

```python
from database import DatabaseManager, DocumentData, ChunkData, VectorData

# Initialize
db_manager = DatabaseManager()
db_manager.initialize()

# Get session
db = db_manager.get_session()

# Query documents
documents = db.query(Document).all()

# Convert to data class
doc_data = DocumentData.from_orm(documents[0])

# Insert vectors
vectors = [VectorData(id=1, vector=[0.1, 0.2, ...], document_id="...", chunk_index=0)]
db_manager.insert_vectors(vectors)

# Verify synchronization
result = db_manager.verify()
print(result.to_dict())
```

### Verification

```python
# Check synchronization
verification = db_manager.verify()
if not verification.synchronized:
    print(f"Issues: {verification.issues}")
    
# Resynchronize if needed
resync_result = db_manager.resync_databases()
```

## 📝 API Endpoints

The database manager is used by the RAG system and exposed through FastAPI:

- `GET /api/documents` - List all documents
- `DELETE /api/documents/{document_id}` - Delete document
- `DELETE /api/documents` - Delete all documents
- `GET /api/verify` - Verify database synchronization
- `POST /api/resync` - Resynchronize databases

## 🔍 Verification Scripts

### Database Verification
```bash
python backend/database/verify_databases.py
```

### Synchronization Verification
```bash
python backend/database/verify_synchronization.py
```

## 📚 Documentation

- [DATA_CLASSES.md](DATA_CLASSES.md) - Data class reference
- [QUICK_START.md](QUICK_START.md) - Quick start guide
- [SYNCHRONIZATION_REPORT.md](SYNCHRONIZATION_REPORT.md) - Synchronization verification
- [UML_DIAGRAM.puml](UML_DIAGRAM.puml) - Architecture diagram

## ⚠️ Important Notes

1. **Text Storage**: Text is stored **only** in PostgreSQL. Milvus contains **only** embeddings.
2. **ID Types**: PostgreSQL uses UUID strings, Milvus uses int64 (hashed from UUID).
3. **Synchronization**: Always use `verify()` before critical operations.
4. **Cleanup**: Use `clean_all()` to remove all data from both databases.

## 🐛 Troubleshooting

### Synchronization Issues

If verification shows synchronization problems:

1. Check the verification report: `python backend/database/verify_databases.py`
2. Resynchronize: `POST /api/resync`
3. Check logs for errors during insertion

### ID Type Errors

If you see Milvus ID type errors:
- Ensure UUID strings are converted to int64 using `_uuid_to_int64()`
- Check that VectorData uses `id: int` (not `str`)

### Missing Text in Search Results

If search results don't have text:
- Verify PostgreSQL connection
- Check that chunks exist in PostgreSQL with matching `document_id` and `chunk_index`
- Ensure `search_similar()` retrieves text from PostgreSQL after Milvus search
