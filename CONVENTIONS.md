# Chatbox App - Development Conventions & Rules

This document outlines all conventions, patterns, and best practices used in the Chatbox App codebase. Use this as a reference for code reviews, new development, and automated checks.

## 📋 Table of Contents

1. [Project Structure](#project-structure)
2. [Code Organization](#code-organization)
3. [Naming Conventions](#naming-conventions)
4. [Database Patterns](#database-patterns)
5. [API Patterns](#api-patterns)
6. [Error Handling](#error-handling)
7. [Testing Conventions](#testing-conventions)
8. [Documentation Standards](#documentation-standards)
9. [Environment Configuration](#environment-configuration)
10. [Security Practices](#security-practices)

---

## 🏗️ Project Structure

### Directory Layout

```
chatbox-app/
├── backend/
│   ├── database/          # Database package (isolated)
│   │   ├── __init__.py
│   │   ├── database_manager.py
│   │   ├── models.py      # Data classes
│   │   └── README.md
│   ├── tests/              # Test suite
│   │   ├── conftest.py     # Shared fixtures
│   │   ├── test_api.py
│   │   ├── test_database.py
│   │   └── test_rag.py
│   ├── main.py             # FastAPI application
│   ├── rag_system.py       # RAG system logic
│   ├── config.py           # Configuration constants
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── contexts/       # React contexts
│   │   ├── services/       # API services
│   │   ├── utils/          # Utility functions
│   │   └── themes/         # Theme definitions
│   └── public/
│       └── config/         # Static config files (YAML)
└── README.md
```

### Key Principles

- **Separation of Concerns**: Database logic in `database/`, API in `main.py`, RAG logic in `rag_system.py`
- **Isolated Packages**: Database package is self-contained with its own README
- **Test Organization**: Tests mirror source structure in `tests/` directory
- **Static Config**: Frontend config files in `public/` for runtime loading

---

## 📦 Code Organization

### Backend Organization

1. **Database Package** (`backend/database/`)
   - **MUST** contain all database-related code
   - **MUST** have `DatabaseManager` class for all DB operations
   - **MUST** use data classes (`models.py`) for business logic
   - **MUST** use ORM models (`database_manager.py`) for database operations
   - **MUST NOT** store text in Milvus (embeddings only)
   - **MUST** convert UUID strings to int64 for Milvus IDs

2. **RAG System** (`backend/rag_system.py`)
   - **MUST** delegate all database operations to `DatabaseManager`
   - **MUST** handle chunking, embedding generation, and similarity search
   - **MUST NOT** directly access databases (use `db_manager`)

3. **API Layer** (`backend/main.py`)
   - **MUST** use FastAPI for all endpoints
   - **MUST** validate input using Pydantic models
   - **MUST** return consistent response formats
   - **MUST** handle errors gracefully with appropriate HTTP status codes

### Frontend Organization

1. **Components** (`frontend/src/components/`)
   - **MUST** be reusable and self-contained
   - **MUST** use CSS variables for theming
   - **MUST** follow React best practices (hooks, props, state)

2. **Services** (`frontend/src/services/`)
   - **MUST** handle all API communication
   - **MUST** use axios for HTTP requests
   - **MUST** handle errors consistently

3. **Configuration** (`frontend/public/config/`)
   - **MUST** use YAML for configuration files
   - **MUST** be loadable at runtime (no rebuild required)

---

## 🏷️ Naming Conventions

### Python (Backend)

- **Classes**: `PascalCase` (e.g., `DatabaseManager`, `RAGSystem`)
- **Functions/Methods**: `snake_case` (e.g., `store_document`, `get_session`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `CHUNK_SIZE`, `EMBEDDING_DIM`)
- **Private Methods**: `_snake_case` with leading underscore (e.g., `_init_postgres`, `_uuid_to_int64`)
- **Variables**: `snake_case` (e.g., `doc_id`, `chunk_text`)

### JavaScript/React (Frontend)

- **Components**: `PascalCase` (e.g., `SuggestionDropdown`, `ThemeSwitcher`)
- **Functions**: `camelCase` (e.g., `handleInputChange`, `searchSuggestions`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `API_URL`, `DEFAULT_THEME`)
- **Variables**: `camelCase` (e.g., `suggestionQuery`, `showSuggestions`)
- **Files**: `PascalCase.jsx` for components, `camelCase.js` for utilities

### Database

- **Tables**: `snake_case`, plural (e.g., `documents`, `chunks`)
- **Columns**: `snake_case` (e.g., `document_id`, `chunk_index`)
- **Collections**: `snake_case` (e.g., `chatbox_vectors`)

---

## 🗄️ Database Patterns

### PostgreSQL (Text Storage)

1. **Text Storage Rule**
   - ✅ **MUST** store all text in PostgreSQL
   - ❌ **MUST NOT** store text in Milvus
   - ✅ **MUST** use `full_text` column for document content
   - ✅ **MUST** use `text` column for chunk content

2. **Document Model**
   ```python
   class Document(Base):
       id = Column(String, primary_key=True)  # UUID string
       filename = Column(String, nullable=False)
       full_text = Column(Text, nullable=False)
       file_hash = Column(String, nullable=False, unique=True)
       created_at = Column(DateTime, default=datetime.utcnow)
       chunk_count = Column(Integer, default=0)
   ```

3. **Chunk Model**
   ```python
   class Chunk(Base):
       id = Column(String, primary_key=True)  # UUID string
       document_id = Column(String, nullable=False, index=True)
       chunk_index = Column(Integer, nullable=False)
       text = Column(Text, nullable=False)
       created_at = Column(DateTime, default=datetime.utcnow)
   ```

### Milvus Lite (Vector Storage)

1. **Vector Storage Rule**
   - ✅ **MUST** store only embeddings in Milvus
   - ❌ **MUST NOT** store text in Milvus
   - ✅ **MUST** use int64 IDs (hashed from UUID strings)
   - ✅ **MUST** store `document_id` and `chunk_index` as metadata

2. **ID Conversion**
   ```python
   @staticmethod
   def _uuid_to_int64(uuid_str: str) -> int:
       """Convert UUID string to int64 for Milvus (uses MD5 hash)"""
       hash_bytes = hashlib.md5(uuid_str.encode()).digest()[:8]
       return struct.unpack('>q', hash_bytes)[0]
   ```

3. **Collection Schema**
   - `id`: int64 (hashed from chunk UUID)
   - `vector`: List[float] (embedding)
   - `document_id`: str (reference to PostgreSQL)
   - `chunk_index`: int (chunk position)

### DatabaseManager Usage

1. **Initialization**
   ```python
   db_manager = DatabaseManager()
   db_manager.initialize()  # MUST call before use
   ```

2. **Session Management**
   ```python
   db = db_manager.get_session()
   try:
       # Use session
   finally:
       db.close()  # MUST close session
   ```

3. **Operations**
   - ✅ **MUST** use `DatabaseManager` methods for all DB operations
   - ❌ **MUST NOT** access databases directly
   - ✅ **MUST** use ORM models through `get_session()`
   - ✅ **MUST** use data classes for business logic

4. **Synchronization**
   - ✅ **MUST** verify synchronization before critical operations
   - ✅ **MUST** use `verify()` method to check database state
   - ✅ **MUST** use `resync_databases()` to fix synchronization issues

---

## 🌐 API Patterns

### Endpoint Structure

1. **Health Checks**
   - `GET /` - Root health check
   - `GET /api/health` - API health check (with RAG status)
   - `GET /health` - Direct health check

2. **Chat Endpoints**
   - `POST /api/chat` - Send chat message (with RAG context if enabled)

3. **Document Endpoints**
   - `POST /api/upload` - Upload and process file
   - `GET /api/documents` - List all documents
   - `GET /api/documents/search` - Search documents (for suggestions)
   - `DELETE /api/documents/{document_id}` - Delete specific document
   - `DELETE /api/documents` - Clean all documents

4. **Synchronization Endpoints**
   - `GET /api/documents/sync` - Check synchronization status
   - `POST /api/documents/resync` - Resynchronize databases

### Request/Response Patterns

1. **Request Validation**
   ```python
   class ChatRequest(BaseModel):
       messages: List[Message]
       model: Optional[str] = None
   ```

2. **Response Format**
   ```python
   {
       "status": "ok",
       "data": {...},
       "message": "Optional message"
   }
   ```

3. **Error Responses**
   ```python
   {
       "detail": "Error message"
   }
   ```

### HTTP Status Codes

- `200 OK` - Success
- `400 Bad Request` - Client error (e.g., RAG not enabled)
- `401 Unauthorized` - Authentication failed
- `413 Request Entity Too Large` - File too large
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service unavailable
- `504 Gateway Timeout` - Request timeout

### Model Selection Logic

```python
# Priority order:
# 1. Request model parameter
# 2. Azure deployment name (if Azure OpenAI)
# 3. Default model (gpt-3.5-turbo or gpt-35-turbo)
```

---

## ⚠️ Error Handling

### Backend Error Handling

1. **Database Errors**
   ```python
   try:
       # Database operation
   except Exception as e:
       db.rollback()  # MUST rollback on error
       print(f"Error: {e}")
       raise
   finally:
       db.close()  # MUST close session
   ```

2. **API Errors**
   ```python
   try:
       # API operation
   except HTTPException:
       raise  # Re-raise HTTP exceptions
   except Exception as e:
       raise HTTPException(
           status_code=500,
           detail=f"Unexpected error: {str(e)}"
       )
   ```

3. **RAG Errors**
   - ✅ **MUST** continue without RAG if storage fails
   - ✅ **MUST** log errors but not crash the application
   - ✅ **MUST** return empty results on search errors

### Frontend Error Handling

1. **API Errors**
   ```javascript
   try {
       const response = await axios.get(url);
       return response.data;
   } catch (error) {
       if (error.response) {
           console.error(`Response error: ${error.response.status}`);
       } else if (error.request) {
           console.error('No response received');
       } else {
           console.error(`Error: ${error.message}`);
       }
       return [];  // Return safe default
   }
   ```

2. **User Feedback**
   - ✅ **MUST** show user-friendly error messages
   - ✅ **MUST** log detailed errors to console (development)
   - ✅ **MUST** handle network errors gracefully

---

## 🧪 Testing Conventions

### Test Structure

1. **Test Organization**
   - Tests in `backend/tests/` directory
   - Test files: `test_*.py`
   - Test classes: `Test*`
   - Test methods: `test_*`

2. **Test Markers**
   ```python
   @pytest.mark.api          # API endpoint tests
   @pytest.mark.database     # Database operation tests
   @pytest.mark.rag          # RAG system tests
   @pytest.mark.unit         # Unit tests (fast)
   @pytest.mark.integration  # Integration tests
   @pytest.mark.slow         # Slow-running tests
   ```

3. **Fixtures**
   - ✅ **MUST** use `conftest.py` for shared fixtures
   - ✅ **MUST** use temporary databases for tests
   - ✅ **MUST** mock external APIs (OpenAI)
   - ✅ **MUST** clean up after tests

4. **Test Patterns**
   ```python
   def test_operation(self, fixture):
       # Arrange
       # Act
       result = operation()
       # Assert
       assert result is not None
   ```

### Database Testing

1. **ORM Usage in Tests**
   ```python
   # ✅ CORRECT: Use ORM directly
   db = test_db_manager.get_session()
   try:
       doc = db.query(Document).filter(Document.id == doc_id).first()
   finally:
       db.close()
   
   # ❌ WRONG: Use non-existent methods
   doc = test_db_manager.get_document(doc_id)  # Method doesn't exist
   ```

2. **Data Class Testing**
   ```python
   # ✅ CORRECT: Test data class structure
   result = VerificationResult(
       postgres_connected=True,
       milvus_connected=True,
       synchronized=True,
       postgres_documents=10,
       postgres_chunks=10,
       milvus_vectors=10,
       issues=[],
       details={}
   )
   ```

### API Testing

1. **Client Fixtures**
   ```python
   # ✅ CORRECT: Use test client with mocked dependencies
   def test_endpoint(client):
       response = client.get("/api/health")
       assert response.status_code == 200
   ```

2. **Environment Mocking**
   ```python
   # ✅ CORRECT: Mock environment variables
   with patch('main.use_azure', False):
       with patch('main.azure_deployment', None):
           # Test code
   ```

---

## 📚 Documentation Standards

### Code Documentation

1. **Docstrings**
   ```python
   def function_name(param: str) -> str:
       """
       Brief description of function.
       
       Args:
           param: Description of parameter
       
       Returns:
           Description of return value
       
       Raises:
           ExceptionType: When this exception occurs
       """
   ```

2. **Type Hints**
   - ✅ **MUST** use type hints for all function parameters and returns
   - ✅ **MUST** use `Optional[T]` for nullable types
   - ✅ **MUST** use `List[T]` for lists

3. **Comments**
   - ✅ **MUST** explain "why", not "what"
   - ✅ **MUST** use comments for complex logic
   - ❌ **MUST NOT** comment obvious code

### README Files

1. **Package READMEs**
   - ✅ **MUST** have README.md in each major package
   - ✅ **MUST** include usage examples
   - ✅ **MUST** include API documentation
   - ✅ **MUST** include troubleshooting section

2. **Code Examples**
   ```python
   # ✅ CORRECT: Include working examples
   from database import DatabaseManager
   
   db = DatabaseManager()
   db.initialize()
   result = db.verify()
   ```

---

## ⚙️ Environment Configuration

### Environment Variables

1. **Backend (.env)**
   ```bash
   # OpenAI Configuration
   OPENAI_API_KEY=sk-...
   AZURE_OPENAI_API_KEY=...
   AZURE_OPENAI_ENDPOINT=...
   AZURE_OPENAI_DEPLOYMENT_NAME=...
   
   # Database Configuration
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=chatbox_rag
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   
   # Milvus Configuration
   MILVUS_LITE_PATH=./milvus_lite.db
   
   # Feature Flags
   RAG_ENABLED=true
   ```

2. **Frontend (.env)**
   ```bash
   VITE_API_URL=http://localhost:8000
   ```

3. **Configuration Rules**
   - ✅ **MUST** use `config.py` for all configuration constants
   - ✅ **MUST** load from environment variables with defaults
   - ✅ **MUST** never commit `.env` files
   - ✅ **MUST** provide `env.example` as template

---

## 🔒 Security Practices

### API Security

1. **Input Validation**
   - ✅ **MUST** validate all input using Pydantic models
   - ✅ **MUST** check file sizes before processing
   - ✅ **MUST** sanitize file content

2. **Error Messages**
   - ✅ **MUST** not expose internal details in error messages
   - ✅ **MUST** log detailed errors server-side
   - ✅ **MUST** return user-friendly messages to clients

3. **CORS Configuration**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000", "http://localhost:5173"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### Database Security

1. **Connection Security**
   - ✅ **MUST** use environment variables for credentials
   - ✅ **MUST** use connection pooling
   - ✅ **MUST** close connections properly

2. **Data Protection**
   - ✅ **MUST** use parameterized queries (SQLAlchemy ORM)
   - ✅ **MUST** validate UUIDs before database operations
   - ✅ **MUST** check permissions before operations

---

## 🎨 Frontend Conventions

### React Patterns

1. **Component Structure**
   ```javascript
   import React, { useState, useEffect } from 'react'
   
   const Component = ({ prop1, prop2 }) => {
       const [state, setState] = useState(null)
       
       useEffect(() => {
           // Side effects
       }, [dependencies])
       
       return (
           <div>
               {/* JSX */}
           </div>
       )
   }
   
   export default Component
   ```

2. **State Management**
   - ✅ **MUST** use `useState` for local state
   - ✅ **MUST** use `useContext` for global state (themes)
   - ✅ **MUST** use `useRef` for DOM references
   - ✅ **MUST** use `useEffect` for side effects

3. **API Calls**
   - ✅ **MUST** use `axios` for HTTP requests
   - ✅ **MUST** debounce search requests (300ms)
   - ✅ **MUST** handle loading and error states
   - ✅ **MUST** use try-catch for error handling

### Theming

1. **CSS Variables**
   ```css
   :root {
       --color-primary: #007bff;
       --color-background: #ffffff;
       --color-text: #000000;
   }
   
   [data-theme="dark"] {
       --color-background: #1a1a1a;
       --color-text: #ffffff;
   }
   ```

2. **Theme Usage**
   - ✅ **MUST** use CSS variables for all colors
   - ✅ **MUST** support theme switching
   - ✅ **MUST** persist theme in localStorage

### Configuration

1. **YAML Configuration**
   ```yaml
   suggestions:
     - symbol: "@"
       name: "Documents"
       provider: "documents"
       enabled: true
       api:
         endpoint: "/api/documents/search"
   ```

2. **Config Loading**
   - ✅ **MUST** load config from `public/config/`
   - ✅ **MUST** handle config loading errors
   - ✅ **MUST** provide default config fallback

---

## 🔍 Code Review Checklist

### Backend Checklist

- [ ] Uses `DatabaseManager` for all database operations
- [ ] Text stored only in PostgreSQL, embeddings only in Milvus
- [ ] UUIDs converted to int64 for Milvus
- [ ] Sessions properly closed in finally blocks
- [ ] Errors handled with appropriate HTTP status codes
- [ ] Type hints used for all functions
- [ ] Docstrings provided for public methods
- [ ] Environment variables loaded from `.env`
- [ ] Tests written and passing

### Frontend Checklist

- [ ] Uses CSS variables for theming
- [ ] API calls use axios with error handling
- [ ] Components are reusable and self-contained
- [ ] State management follows React best practices
- [ ] Config files in `public/config/` for runtime loading
- [ ] Debouncing used for search requests
- [ ] Loading and error states handled

### Database Checklist

- [ ] All operations use `DatabaseManager`
- [ ] Synchronization verified before critical operations
- [ ] Text never stored in Milvus
- [ ] UUID to int64 conversion used for Milvus IDs
- [ ] Sessions properly managed (get, use, close)
- [ ] Data classes used for business logic
- [ ] ORM models used for database operations

---

## 📝 Common Patterns

### Database Operation Pattern

```python
db = db_manager.get_session()
try:
    # Operation
    db.commit()
except Exception as e:
    db.rollback()
    raise
finally:
    db.close()
```

### API Endpoint Pattern

```python
@app.get("/api/endpoint")
async def endpoint():
    if not rag_system:
        raise HTTPException(status_code=400, detail="RAG not enabled")
    
    try:
        # Operation
        return {"status": "ok", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Test Pattern

```python
def test_operation(fixture):
    # Arrange
    setup_data()
    
    # Act
    result = operation()
    
    # Assert
    assert result is not None
    assert result.property == expected_value
```

---

## 🚫 Anti-Patterns (Don't Do This)

1. ❌ **Direct Database Access**
   ```python
   # ❌ WRONG
   db.query(Document).all()  # Outside DatabaseManager
   
   # ✅ CORRECT
   db_manager.get_session().query(Document).all()
   ```

2. ❌ **Storing Text in Milvus**
   ```python
   # ❌ WRONG
   milvus_data = {"id": 1, "vector": [...], "text": "..."}
   
   # ✅ CORRECT
   milvus_data = {"id": 1, "vector": [...], "document_id": "...", "chunk_index": 0}
   # Text retrieved from PostgreSQL
   ```

3. ❌ **Not Closing Sessions**
   ```python
   # ❌ WRONG
   db = db_manager.get_session()
   doc = db.query(Document).first()
   # Session not closed
   
   # ✅ CORRECT
   db = db_manager.get_session()
   try:
       doc = db.query(Document).first()
   finally:
       db.close()
   ```

4. ❌ **Hardcoded Values**
   ```python
   # ❌ WRONG
   chunk_size = 500
   
   # ✅ CORRECT
   chunk_size = CHUNK_SIZE  # From config.py
   ```

5. ❌ **Exposing Internal Errors**
   ```python
   # ❌ WRONG
   raise HTTPException(detail=str(internal_error))
   
   # ✅ CORRECT
   print(f"Internal error: {internal_error}")  # Log server-side
   raise HTTPException(detail="User-friendly message")
   ```

---

## 📖 Additional Resources

- [Backend Database README](backend/database/README.md)
- [Test Suite README](backend/tests/README.md)
- [FAQ](FAQ.md)
- [Installation Guide](INSTALLATION.md)

---

## 🔄 Version History

- **v1.0.0** (2024-12-04): Initial conventions document
  - Database patterns
  - API patterns
  - Testing conventions
  - Frontend patterns

---

**Last Updated**: 2024-12-04
**Maintained By**: Chatbox App Development Team

