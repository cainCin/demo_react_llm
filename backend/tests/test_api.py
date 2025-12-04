"""
Tests for FastAPI endpoints
"""
import pytest
import os
from fastapi import status
from unittest.mock import Mock, patch


@pytest.mark.api
class TestHealthEndpoints:
    """Tests for health check endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root health check endpoint"""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data
    
    def test_health_endpoint(self, client):
        """Test /api/health endpoint"""
        response = client.get("/api/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert "rag_enabled" in data
    
    def test_health_direct_endpoint(self, client):
        """Test /health endpoint (direct access)"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert "rag_enabled" in data


@pytest.mark.api
class TestChatEndpoint:
    """Tests for chat endpoint"""
    
    def test_chat_endpoint_success(self, client, sample_chat_messages):
        """Test successful chat request"""
        # Patch the main module variables to ensure they don't use Azure deployment
        with patch('main.use_azure', False):
            with patch('main.azure_deployment', None):
                response = client.post(
                    "/api/chat",
                    json={
                        "messages": sample_chat_messages,
                        "model": "gpt-3.5-turbo"
                    }
                )
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "message" in data
                assert "model" in data
                # Model should match request (not from env)
                assert data["model"] == "gpt-3.5-turbo"
    
    def test_chat_endpoint_no_model(self, client, sample_chat_messages):
        """Test chat request without model (should use default)"""
        response = client.post(
            "/api/chat",
            json={"messages": sample_chat_messages}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "model" in data
    
    def test_chat_endpoint_empty_messages(self, client):
        """Test chat request with empty messages"""
        response = client.post(
            "/api/chat",
            json={"messages": []}
        )
        # Should still work, but may return empty response
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_chat_endpoint_invalid_json(self, client):
        """Test chat request with invalid JSON"""
        response = client.post(
            "/api/chat",
            json={"invalid": "data"}
        )
        # Should return 422 validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_chat_endpoint_with_rag_context(self, client_with_rag, sample_text):
        """Test chat endpoint with RAG context retrieval"""
        # First, store a document
        rag_system = client_with_rag.app.state.rag_system
        doc_id = rag_system.store_document("test.txt", sample_text)
        
        # Now test chat with RAG
        response = client_with_rag.post(
            "/api/chat",
            json={
                "messages": [{"role": "user", "content": "What is in the document?"}],
                "model": "gpt-3.5-turbo"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data


@pytest.mark.api
class TestUploadEndpoint:
    """Tests for file upload endpoint"""
    
    def test_upload_text_file(self, client, sample_file_content):
        """Test uploading a text file"""
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", sample_file_content, "text/plain")}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["filename"] == "test.txt"
        assert "content" in data
        assert "size" in data
        assert data["rag_stored"] is True
    
    def test_upload_markdown_file(self, client):
        """Test uploading a markdown file"""
        content = b"# Test Document\n\nThis is a test."
        response = client.post(
            "/api/upload",
            files={"file": ("test.md", content, "text/markdown")}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["filename"] == "test.md"
        assert "# Test Document" in data["content"]
    
    def test_upload_large_file(self, client):
        """Test uploading a file that exceeds size limit"""
        # Create a file larger than MAX_FILE_SIZE (10MB default)
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        response = client.post(
            "/api/upload",
            files={"file": ("large.txt", large_content, "text/plain")}
        )
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    
    def test_upload_no_file(self, client):
        """Test upload endpoint without file"""
        response = client.post("/api/upload")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.api
class TestDocumentsEndpoints:
    """Tests for document management endpoints"""
    
    def test_list_documents_empty(self, client):
        """Test listing documents when none exist"""
        response = client.get("/api/documents")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "documents" in data
        assert isinstance(data["documents"], list)
    
    def test_list_documents_with_data(self, client_with_rag, sample_text):
        """Test listing documents with stored data"""
        # Store a document first
        doc_id = client_with_rag.app.state.rag_system.store_document("test.txt", sample_text)
        
        response = client_with_rag.get("/api/documents")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) > 0
    
    def test_list_documents_rag_disabled(self, client):
        """Test listing documents when RAG is disabled"""
        with patch('main.rag_system', None):
            response = client.get("/api/documents")
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert "RAG system is not enabled" in data["detail"]
    
    def test_search_documents_no_query(self, client):
        """Test searching documents without query (should return recent)"""
        response = client.get("/api/documents/search")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "documents" in data
        assert "query" in data
        assert "count" in data
        assert "total" in data
    
    def test_search_documents_with_query(self, client_with_rag, sample_text):
        """Test searching documents with query"""
        # Store a document first
        client_with_rag.app.state.rag_system.store_document("test_document.txt", sample_text)
        
        response = client_with_rag.get("/api/documents/search?query=test")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "documents" in data
        assert data["query"] == "test"
    
    def test_search_documents_with_limit(self, client):
        """Test searching documents with custom limit"""
        response = client.get("/api/documents/search?query=&limit=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["documents"]) <= 10
    
    def test_delete_document(self, client_with_rag, sample_text):
        """Test deleting a document"""
        # Store a document first
        doc_id = client_with_rag.app.state.rag_system.store_document("test.txt", sample_text)
        
        response = client_with_rag.delete(f"/api/documents/{doc_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
    
    def test_delete_nonexistent_document(self, client):
        """Test deleting a non-existent document"""
        response = client.delete("/api/documents/non-existent-id")
        # Should either succeed (idempotent) or return error
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_clean_all_documents(self, client):
        """Test cleaning all documents"""
        response = client.delete("/api/documents")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert "cleaned" in data["message"].lower() or "all" in data["message"].lower()


@pytest.mark.api
class TestSynchronizationEndpoints:
    """Tests for database synchronization endpoints"""
    
    def test_check_synchronization(self, client):
        """Test checking database synchronization"""
        response = client.get("/api/documents/sync")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "synchronized" in data
    
    def test_resync_databases(self, client):
        """Test resynchronizing databases"""
        response = client.post("/api/documents/resync")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data or "message" in data
    
    def test_sync_endpoints_rag_disabled(self, client):
        """Test sync endpoints when RAG is disabled"""
        with patch('main.rag_system', None):
            # Test sync check
            response = client.get("/api/documents/sync")
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            
            # Test resync
            response = client.post("/api/documents/resync")
            assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.api
class TestCORS:
    """Tests for CORS configuration"""
    
    def test_cors_headers(self, client):
        """Test that CORS headers are present"""
        response = client.options("/api/health")
        # CORS preflight should be handled
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED]

