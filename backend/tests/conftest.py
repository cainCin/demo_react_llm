"""
Pytest configuration and fixtures for Chatbox App tests
"""
import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from openai import OpenAI, AzureOpenAI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import application components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from database import DatabaseManager, Base
from rag_system import RAGSystem
from config import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
    MILVUS_LITE_PATH, MILVUS_COLLECTION
)


# ============================================
# Test Configuration
# ============================================

# Use test databases
TEST_POSTGRES_DB = f"{POSTGRES_DB}_test"
TEST_MILVUS_PATH = None  # Will be set in fixture


# ============================================
# Mock OpenAI Client Fixtures
# ============================================

@pytest.fixture
def mock_openai_client():
    """Create a mocked OpenAI client for testing"""
    mock_client = Mock(spec=OpenAI)
    
    # Mock embeddings
    mock_embedding_response = Mock()
    mock_embedding_response.data = [Mock(embedding=[0.1] * 1536)]  # 1536-dim embedding
    mock_client.embeddings = Mock()
    mock_client.embeddings.create = Mock(return_value=mock_embedding_response)
    
    # Mock chat completions
    mock_chat_response = Mock()
    mock_chat_response.choices = [Mock(message=Mock(content="Test response"))]
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = Mock(return_value=mock_chat_response)
    
    # Mock models list (for connection test)
    mock_client.models = Mock()
    mock_client.models.list = Mock(return_value=[])
    
    return mock_client


@pytest.fixture
def mock_azure_openai_client():
    """Create a mocked Azure OpenAI client for testing"""
    mock_client = Mock(spec=AzureOpenAI)
    
    # Mock embeddings
    mock_embedding_response = Mock()
    mock_embedding_response.data = [Mock(embedding=[0.1] * 1536)]
    mock_client.embeddings = Mock()
    mock_client.embeddings.create = Mock(return_value=mock_embedding_response)
    
    # Mock chat completions
    mock_chat_response = Mock()
    mock_chat_response.choices = [Mock(message=Mock(content="Test Azure response"))]
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = Mock(return_value=mock_chat_response)
    
    # Mock models list
    mock_client.models = Mock()
    mock_client.models.list = Mock(return_value=[])
    
    return mock_client


# ============================================
# Database Fixtures
# ============================================

@pytest.fixture(scope="function")
def temp_milvus_path():
    """Create a temporary Milvus database file for testing"""
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "test_milvus.db")
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except:
            pass
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


@pytest.fixture(scope="function")
def test_db_manager(temp_milvus_path):
    """Create a test DatabaseManager with temporary databases"""
    # Override environment variables for test
    original_milvus_path = os.getenv("MILVUS_LITE_PATH")
    original_postgres_db = os.getenv("POSTGRES_DB")
    
    try:
        # Set test database paths
        os.environ["MILVUS_LITE_PATH"] = temp_milvus_path
        os.environ["POSTGRES_DB"] = TEST_POSTGRES_DB
        
        # Create database manager
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        yield db_manager
        
        # Cleanup
        try:
            db_manager.clean_all()
        except:
            pass
        try:
            if db_manager.milvus_client:
                db_manager.milvus_client.drop_collection(MILVUS_COLLECTION)
        except:
            pass
    finally:
        # Restore original environment
        if original_milvus_path:
            os.environ["MILVUS_LITE_PATH"] = original_milvus_path
        elif "MILVUS_LITE_PATH" in os.environ:
            del os.environ["MILVUS_LITE_PATH"]
        
        if original_postgres_db:
            os.environ["POSTGRES_DB"] = original_postgres_db
        elif "POSTGRES_DB" in os.environ:
            del os.environ["POSTGRES_DB"]


@pytest.fixture(scope="function")
def test_rag_system(mock_openai_client, test_db_manager):
    """Create a test RAGSystem with mocked OpenAI client"""
    rag = RAGSystem(mock_openai_client, embedding_model="text-embedding-ada-002", use_azure=False)
    # Replace db_manager with test one
    rag.db_manager = test_db_manager
    return rag


# ============================================
# FastAPI Test Client Fixtures
# ============================================

@pytest.fixture(scope="function")
def client(mock_openai_client, test_db_manager):
    """Create a test client for FastAPI app"""
    # Save original environment variables
    original_azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    original_azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    original_azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    original_openai_key = os.getenv("OPENAI_API_KEY")
    
    try:
        # Clear Azure environment variables to ensure standard OpenAI behavior
        env_vars_to_clear = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT_NAME",
            "AZURE_OPENAI_API_KEY"
        ]
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
        
        # Set a dummy OpenAI key if not present
        if "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = "test-key-12345"
        
        # Create a mock RAG system
        mock_rag_system = Mock(spec=RAGSystem)
        mock_rag_system.db_manager = test_db_manager
        mock_rag_system.store_document = Mock(return_value="test-doc-id-123")
        mock_rag_system.delete_document = Mock()
        mock_rag_system.clean_all_databases = Mock()
        mock_rag_system.resync_databases = Mock(return_value=Mock(
            success=True,
            to_dict=Mock(return_value={"success": True, "message": "Resync completed"})
        ))
        mock_rag_system.search_similar = Mock(return_value=[])
        mock_rag_system.db_manager.verify = Mock(return_value=Mock(
            synchronized=True,
            to_dict=Mock(return_value={"synchronized": True, "postgres_count": 0, "milvus_count": 0})
        ))
        
        # Patch the global variables in main module
        # These need to be patched to override environment-based initialization
        with patch('main.openai_client', mock_openai_client):
            with patch('main.rag_system', mock_rag_system):
                with patch('main.use_azure', False):
                    with patch('main.azure_deployment', None):
                        with TestClient(app) as test_client:
                            yield test_client
    finally:
        # Restore original environment variables
        if original_azure_endpoint:
            os.environ["AZURE_OPENAI_ENDPOINT"] = original_azure_endpoint
        elif "AZURE_OPENAI_ENDPOINT" in os.environ:
            del os.environ["AZURE_OPENAI_ENDPOINT"]
            
        if original_azure_deployment:
            os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = original_azure_deployment
        elif "AZURE_OPENAI_DEPLOYMENT_NAME" in os.environ:
            del os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]
            
        if original_azure_api_key:
            os.environ["AZURE_OPENAI_API_KEY"] = original_azure_api_key
        elif "AZURE_OPENAI_API_KEY" in os.environ:
            del os.environ["AZURE_OPENAI_API_KEY"]
            
        if original_openai_key:
            os.environ["OPENAI_API_KEY"] = original_openai_key
        elif "OPENAI_API_KEY" in os.environ and os.environ["OPENAI_API_KEY"] == "test-key-12345":
            del os.environ["OPENAI_API_KEY"]


@pytest.fixture(scope="function")
def client_with_rag(mock_openai_client, test_rag_system):
    """Create a test client with a real RAG system (for integration tests)"""
    with patch('main.openai_client', mock_openai_client):
        with patch('main.rag_system', test_rag_system):
            with TestClient(app) as test_client:
                # Store RAG system reference for tests
                test_client.app.state.rag_system = test_rag_system
                yield test_client


# ============================================
# Test Data Fixtures
# ============================================

@pytest.fixture
def sample_text():
    """Sample text for testing document storage"""
    return """
    This is a sample document for testing purposes.
    It contains multiple sentences and paragraphs.
    
    The RAG system should be able to chunk this text
    and store it in both PostgreSQL and Milvus.
    
    This is the second paragraph with more content.
    It helps test the chunking and embedding generation.
    """


@pytest.fixture
def sample_file_content():
    """Sample file content for upload testing"""
    return b"This is a test file content.\nIt has multiple lines.\nFor testing file uploads."


@pytest.fixture
def sample_chat_messages():
    """Sample chat messages for testing"""
    return [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
        {"role": "user", "content": "What is the weather today?"}
    ]


# ============================================
# Utility Functions
# ============================================

def skip_if_no_openai_key():
    """Skip test if OpenAI API key is not available"""
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("AZURE_OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not available")


def skip_if_no_postgres():
    """Skip test if PostgreSQL is not available"""
    try:
        from database import DatabaseManager
        db = DatabaseManager()
        db.initialize()
        db.get_session().close()
    except Exception:
        pytest.skip("PostgreSQL not available")

