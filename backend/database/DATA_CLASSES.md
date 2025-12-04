# Data Classes Reference

This document describes all data classes used in the database package and how they should be used.

## 📋 Data Classes Overview

All data classes are defined in `models.py` and provide type-safe, structured data handling throughout the application.

## 🏗️ Data Classes

### DocumentData

Represents a complete document with all metadata.

```python
from database import DocumentData

doc = DocumentData(
    id="uuid-string",
    filename="example.txt",
    full_text="Full document text...",
    file_hash="md5-hash",
    created_at=datetime.now(),
    chunk_count=10
)

# Convert to dict for API responses
doc_dict = doc.to_dict()

# Create from ORM model
doc = DocumentData.from_orm(orm_document)
```

**Fields:**
- `id`: str - Document UUID
- `filename`: str - Original filename
- `full_text`: str - Complete document text
- `file_hash`: str - MD5 hash of content
- `created_at`: Optional[datetime] - Creation timestamp
- `chunk_count`: int - Number of chunks

### ChunkData

Represents a text chunk with metadata.

```python
from database import ChunkData

chunk = ChunkData(
    id="uuid-string",
    document_id="doc-uuid",
    chunk_index=0,
    text="Chunk text content...",
    created_at=datetime.now()
)

# Convert to dict
chunk_dict = chunk.to_dict()

# Create from ORM model
chunk = ChunkData.from_orm(orm_chunk)
```

**Fields:**
- `id`: str - Chunk UUID
- `document_id`: str - Parent document ID
- `chunk_index`: int - Position in document
- `text`: str - Chunk text content
- `created_at`: Optional[datetime] - Creation timestamp

### VectorData

Represents a vector embedding for Milvus storage.

```python
from database import VectorData

vector = VectorData(
    id=1234567890,  # int64
    vector=[0.1, 0.2, ...],  # Embedding vector
    document_id="doc-uuid",
    chunk_index=0
)

# Convert to dict for Milvus insertion
vector_dict = vector.to_dict()
```

**Fields:**
- `id`: int - int64 identifier (hashed from UUID)
- `vector`: List[float] - Embedding vector
- `document_id`: str - Reference to document
- `chunk_index`: int - Position in document

**Note:** Text is NOT stored in Milvus, only embeddings.

### SearchResult

Represents a search result with similarity scores.

```python
from database import SearchResult

result = SearchResult(
    id=1234567890,
    document_id="doc-uuid",
    chunk_index=0,
    text="Retrieved chunk text...",
    distance=0.5,
    score=0.8
)

# Convert to dict for API responses
result_dict = result.to_dict()
```

**Fields:**
- `id`: int - Vector ID from Milvus
- `document_id`: str - Document reference
- `chunk_index`: int - Chunk position
- `text`: str - Chunk text (retrieved from PostgreSQL)
- `distance`: float - Vector distance
- `score`: float - Similarity score (0-1)

### VerificationResult

Represents database verification status.

```python
from database import VerificationResult

result = db_manager.verify()
print(f"Synchronized: {result.synchronized}")
print(f"PostgreSQL chunks: {result.postgres_chunks}")
print(f"Milvus vectors: {result.milvus_vectors}")

# Convert to dict for API responses
result_dict = result.to_dict()
```

**Fields:**
- `postgres_connected`: bool
- `milvus_connected`: bool
- `synchronized`: bool
- `postgres_documents`: int
- `postgres_chunks`: int
- `milvus_vectors`: int
- `issues`: List[str]
- `details`: Dict[str, Any]

### ResyncResult

Represents resynchronization operation results.

```python
from database import ResyncResult

result = rag_system.resync_databases()
print(f"Success: {result.success}")
print(f"Vectors inserted: {result.vectors_inserted}")

# Convert to dict for API responses
result_dict = result.to_dict()
```

**Fields:**
- `success`: bool
- `documents_processed`: int
- `chunks_processed`: int
- `vectors_inserted`: int
- `errors`: List[str]

### DocumentListItem

Lightweight document representation for lists.

```python
from database import DocumentListItem

item = DocumentListItem(
    id="uuid",
    filename="example.txt",
    chunk_count=10,
    created_at=datetime.now()
)

# Convert to dict
item_dict = item.to_dict()

# Create from ORM model
item = DocumentListItem.from_orm(orm_document)
```

**Fields:**
- `id`: str
- `filename`: str
- `chunk_count`: int
- `created_at`: Optional[datetime]

## 🔄 Usage Patterns

### Converting ORM to Data Class

```python
from database import Document, DocumentData

# In database query
orm_doc = db.query(Document).first()

# Convert to data class
doc_data = DocumentData.from_orm(orm_doc)

# Use data class
print(doc_data.filename)
print(doc_data.chunk_count)
```

### Using Data Classes in API Responses

```python
from database import DocumentListItem

# Query documents
documents = db.query(Document).all()

# Convert to data classes
doc_list = [DocumentListItem.from_orm(doc) for doc in documents]

# Return as dicts
return {"documents": [doc.to_dict() for doc in doc_list]}
```

### Creating VectorData for Insertion

```python
from database import VectorData

# Generate embedding
embedding = generate_embedding(text)

# Create VectorData
vector = VectorData(
    id=uuid_to_int64(chunk_id),
    vector=embedding,
    document_id=doc_id,
    chunk_index=idx
)

# Insert into Milvus
db_manager.insert_vectors([vector])
```

## ✅ Benefits

1. **Type Safety**: Clear type hints and structure
2. **Consistency**: Same data structure throughout codebase
3. **Validation**: Data class validation on creation
4. **Serialization**: Built-in `to_dict()` methods
5. **ORM Integration**: `from_orm()` factory methods
6. **Documentation**: Self-documenting code with clear fields

## 📝 Best Practices

1. **Always use data classes** instead of raw dictionaries
2. **Use `from_orm()`** when converting from SQLAlchemy models
3. **Use `to_dict()`** when returning data from API endpoints
4. **Import from `database` package** for consistency
5. **Type hints** should reference data classes, not Dict

## 🔍 Examples

### Example: Storing a Document

```python
from database import DocumentData, ChunkData, VectorData

# Create document data
doc_data = DocumentData(
    id=str(uuid.uuid4()),
    filename="example.txt",
    full_text=text,
    file_hash=hashlib.md5(text.encode()).hexdigest(),
    chunk_count=len(chunks)
)

# Create chunk data
chunk_data = ChunkData(
    id=str(uuid.uuid4()),
    document_id=doc_data.id,
    chunk_index=0,
    text=chunk_text
)

# Create vector data
vector_data = VectorData(
    id=uuid_to_int64(chunk_data.id),
    vector=embedding,
    document_id=doc_data.id,
    chunk_index=0
)
```

### Example: Search Results

```python
from database import SearchResult

# Search returns List[SearchResult]
results = rag_system.search_similar("query text")

# Access fields
for result in results:
    print(f"Document: {result.document_id}")
    print(f"Text: {result.text}")
    print(f"Score: {result.score}")

# Convert to dicts for API
return {"results": [r.to_dict() for r in results]}
```

