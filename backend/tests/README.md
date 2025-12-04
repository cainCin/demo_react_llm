# Test Suite for Chatbox App

Comprehensive test suite for the Chatbox App backend, covering API endpoints, database operations, and RAG system functionality.

## 📋 Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Writing Tests](#writing-tests)
- [Test Launcher](#test-launcher)
- [Coverage](#coverage)

## 🎯 Overview

The test suite includes:

- **API Tests** (`test_api.py`): Tests for all FastAPI endpoints
- **Database Tests** (`test_database.py`): Tests for database operations and data classes
- **RAG Tests** (`test_rag.py`): Tests for RAG system functionality
- **Fixtures** (`conftest.py`): Shared test fixtures and utilities

## 🚀 Setup

### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- `pytest>=7.4.0` - Test framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-mock>=3.11.0` - Mocking utilities

### Environment Setup

Tests use temporary databases, but you may need PostgreSQL running for integration tests:

```bash
# Start PostgreSQL (if not already running)
docker start chatbox-postgres
```

## 🧪 Running Tests

### Using pytest directly

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v

# Run tests with specific marker
pytest tests/ -v -m api
pytest tests/ -v -m database
pytest tests/ -v -m rag

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Using the test launcher

```bash
# Run all tests
python tests/run_tests.py all

# Run specific test categories
python tests/run_tests.py api
python tests/run_tests.py database
python tests/run_tests.py rag

# Run with coverage
python tests/run_tests.py coverage

# Launch application (backend + frontend)
python tests/run_tests.py launch
```

## 📁 Test Structure

```
backend/tests/
├── __init__.py          # Test package
├── conftest.py          # Shared fixtures
├── test_api.py          # API endpoint tests
├── test_database.py     # Database operation tests
├── test_rag.py          # RAG system tests
├── run_tests.py         # Test launcher script
└── README.md            # This file
```

## ✍️ Writing Tests

### Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.database` - Database operation tests
- `@pytest.mark.rag` - RAG system tests
- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests

### Example Test

```python
import pytest
from fastapi import status

@pytest.mark.api
class TestMyEndpoint:
    """Tests for my endpoint"""
    
    def test_endpoint_success(self, client):
        """Test successful request"""
        response = client.get("/api/my-endpoint")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "expected_field" in data
```

### Available Fixtures

- `mock_openai_client` - Mocked OpenAI client
- `mock_azure_openai_client` - Mocked Azure OpenAI client
- `test_db_manager` - Test DatabaseManager with temporary databases
- `test_rag_system` - Test RAGSystem with mocked OpenAI client
- `client` - FastAPI test client with mocked RAG system
- `client_with_rag` - FastAPI test client with real RAG system
- `sample_text` - Sample text for testing
- `sample_file_content` - Sample file content
- `sample_chat_messages` - Sample chat messages

## 🎮 Test Launcher

The `run_tests.py` script provides convenient commands:

```bash
python tests/run_tests.py <command>
```

### Commands

- `all` - Run all tests
- `api` - Run API tests only
- `database` - Run database tests only
- `rag` - Run RAG tests only
- `unit` - Run unit tests (fast)
- `integration` - Run integration tests
- `coverage` - Run tests with coverage report
- `launch` - Launch application (backend + frontend)
- `backend` - Launch backend only
- `frontend` - Launch frontend only
- `help` - Show help message

## 📊 Coverage

Generate coverage reports:

```bash
# Terminal report
pytest tests/ --cov=. --cov-report=term

# HTML report
pytest tests/ --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

## 🔍 Test Categories

### API Tests (`test_api.py`)

Tests for all FastAPI endpoints:

- Health check endpoints (`/`, `/api/health`, `/health`)
- Chat endpoint (`POST /api/chat`)
- File upload (`POST /api/upload`)
- Document management (`GET /api/documents`, `DELETE /api/documents/{id}`)
- Document search (`GET /api/documents/search`)
- Synchronization (`GET /api/documents/sync`, `POST /api/documents/resync`)
- CORS configuration

### Database Tests (`test_database.py`)

Tests for database operations:

- DatabaseManager initialization
- Document storage and retrieval
- Chunk storage and retrieval
- Vector insertion
- Document deletion
- Database cleanup
- Verification and synchronization
- Data class functionality
- UUID to int64 conversion

### RAG Tests (`test_rag.py`)

Tests for RAG system:

- RAG system initialization
- Text chunking
- Embedding generation
- Document storage with chunks and vectors
- Similarity search
- Document deletion
- Database synchronization
- Full workflow integration

## 🐛 Debugging Tests

### Run with verbose output

```bash
pytest tests/ -vv
```

### Run specific test

```bash
pytest tests/test_api.py::TestChatEndpoint::test_chat_endpoint_success -v
```

### Run with print statements

```bash
pytest tests/ -v -s
```

### Stop on first failure

```bash
pytest tests/ -x
```

## ⚠️ Notes

1. **Test Databases**: Tests use temporary databases (separate from production)
2. **Mocking**: OpenAI API calls are mocked to avoid API costs
3. **Isolation**: Each test runs in isolation with fresh fixtures
4. **Cleanup**: Test fixtures automatically clean up temporary files and databases

## 📝 Best Practices

1. **Use fixtures**: Leverage existing fixtures instead of creating new ones
2. **Mark tests**: Use appropriate markers for test categorization
3. **Test edge cases**: Include tests for error conditions and edge cases
4. **Keep tests fast**: Unit tests should run quickly (< 1 second each)
5. **Isolate tests**: Tests should not depend on each other
6. **Clear assertions**: Use descriptive assertion messages

## 🔗 Related Documentation

- [Main README](../../README.md)
- [Database Documentation](../database/README.md)
- [FAQ](../../FAQ.md)
- [API Documentation](http://localhost:8000/docs) (when backend is running)

## 🆘 Troubleshooting

### Import errors

If you see import errors, ensure you're in the `backend` directory:

```bash
cd backend
pytest tests/
```

### Database connection errors

Tests use temporary databases, but if you see connection errors:

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Start if needed
docker start chatbox-postgres
```

### Module not found

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```


