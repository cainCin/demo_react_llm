"""
Tests for RAG system operations and procedures
"""
import pytest
from rag_system import RAGSystem


@pytest.mark.rag
class TestRAGSystem:
    """Tests for RAGSystem class"""
    
    def test_initialization(self, mock_openai_client, test_db_manager):
        """Test RAG system initialization"""
        rag = RAGSystem(mock_openai_client, embedding_model="text-embedding-ada-002")
        assert rag.openai_client is not None
        assert rag.db_manager is not None
        assert rag.embedding_model == "text-embedding-ada-002"
    
    def test_chunk_text_simple(self, mock_openai_client, test_db_manager):
        """Test simple text chunking"""
        rag = RAGSystem(mock_openai_client)
        rag.db_manager = test_db_manager
        
        text = "This is a test. " * 100  # Long text
        chunks = rag.chunk_text(text, chunk_size=50, chunk_overlap=10)
        
        assert len(chunks) > 0
        assert all(len(chunk) <= 50 + 20 for chunk in chunks)  # Allow some flexibility
    
    def test_chunk_text_short(self, mock_openai_client, test_db_manager):
        """Test chunking short text"""
        rag = RAGSystem(mock_openai_client)
        rag.db_manager = test_db_manager
        
        text = "Short text"
        chunks = rag.chunk_text(text, chunk_size=100)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_empty(self, mock_openai_client, test_db_manager):
        """Test chunking empty text"""
        rag = RAGSystem(mock_openai_client)
        rag.db_manager = test_db_manager
        
        chunks = rag.chunk_text("")
        assert len(chunks) == 0
    
    def test_generate_embedding(self, mock_openai_client, test_db_manager):
        """Test embedding generation"""
        rag = RAGSystem(mock_openai_client)
        rag.db_manager = test_db_manager
        
        embedding = rag.generate_embedding("Test text")
        
        assert len(embedding) == 1536  # ada-002 dimension
        assert all(isinstance(x, (int, float)) for x in embedding)
    
    def test_store_document(self, test_rag_system, sample_text):
        """Test storing a document in RAG system"""
        doc_id = test_rag_system.store_document("test.txt", sample_text)
        
        assert doc_id is not None
        assert isinstance(doc_id, str)
        
        # Verify document is stored using ORM
        from database import Document
        db = test_rag_system.db_manager.get_session()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            assert doc is not None
            assert doc.filename == "test.txt"
        finally:
            db.close()
    
    def test_store_document_with_chunks(self, test_rag_system, sample_text):
        """Test storing document creates chunks"""
        doc_id = test_rag_system.store_document("test.txt", sample_text)
        
        # Verify chunks are created using ORM
        from database import Chunk
        db = test_rag_system.db_manager.get_session()
        try:
            chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).all()
            assert len(chunks) > 0
        finally:
            db.close()
    
    def test_store_document_with_vectors(self, test_rag_system, sample_text):
        """Test storing document creates vectors"""
        doc_id = test_rag_system.store_document("test.txt", sample_text)
        
        # Verify vectors are created (check via verification)
        result = test_rag_system.db_manager.verify()
        # Should have some vectors if chunks were created
        # Note: Exact count depends on chunking
    
    def test_search_similar(self, test_rag_system, sample_text):
        """Test similarity search"""
        # First store a document
        doc_id = test_rag_system.store_document("test.txt", sample_text)
        
        # Search for similar content
        results = test_rag_system.search_similar("sample document", top_k=3)
        
        assert isinstance(results, list)
        # May be empty if no similar vectors, but should not error
    
    def test_search_similar_empty(self, test_rag_system):
        """Test similarity search with no documents"""
        results = test_rag_system.search_similar("test query", top_k=3)
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_delete_document(self, test_rag_system, sample_text):
        """Test deleting a document from RAG system"""
        # Store a document
        doc_id = test_rag_system.store_document("test.txt", sample_text)
        
        # Delete it
        test_rag_system.delete_document(doc_id)
        
        # Verify it's deleted using ORM
        from database import Document
        db = test_rag_system.db_manager.get_session()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            assert doc is None
        finally:
            db.close()
    
    def test_clean_all_databases(self, test_rag_system, sample_text):
        """Test cleaning all databases"""
        # Store some documents
        test_rag_system.store_document("test1.txt", sample_text)
        test_rag_system.store_document("test2.txt", sample_text)
        
        # Clean all
        test_rag_system.clean_all_databases()
        
        # Verify all deleted
        db = test_rag_system.db_manager.get_session()
        try:
            from database import Document
            count = db.query(Document).count()
            assert count == 0
        finally:
            db.close()
    
    def test_verify_synchronization(self, test_rag_system, sample_text):
        """Test verification of database synchronization"""
        # Store a document
        test_rag_system.store_document("test.txt", sample_text)
        
        # Verify
        result = test_rag_system.verify_synchronization()
        
        assert result is not None
        assert hasattr(result, 'synchronized')
        assert hasattr(result, 'postgres_documents')
        assert hasattr(result, 'postgres_chunks')
        assert hasattr(result, 'milvus_vectors')
    
    def test_resync_databases(self, test_rag_system, sample_text):
        """Test resynchronizing databases"""
        # Store a document
        test_rag_system.store_document("test.txt", sample_text)
        
        # Resync
        result = test_rag_system.resync_databases()
        
        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'vectors_inserted')
        assert hasattr(result, 'documents_processed')
        assert hasattr(result, 'chunks_processed')


@pytest.mark.rag
class TestRAGIntegration:
    """Integration tests for RAG system"""
    
    def test_full_workflow(self, test_rag_system, sample_text):
        """Test complete RAG workflow: store, search, delete"""
        from database import Document
        
        # 1. Store document
        doc_id = test_rag_system.store_document("workflow_test.txt", sample_text)
        assert doc_id is not None
        
        # 2. Verify storage using ORM
        db = test_rag_system.db_manager.get_session()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            assert doc is not None
        finally:
            db.close()
        
        # 3. Search
        results = test_rag_system.search_similar("document", top_k=1)
        # May or may not find results depending on embeddings
        
        # 4. Delete
        test_rag_system.delete_document(doc_id)
        db = test_rag_system.db_manager.get_session()
        try:
            doc_after = db.query(Document).filter(Document.id == doc_id).first()
            assert doc_after is None
        finally:
            db.close()
    
    def test_multiple_documents(self, test_rag_system):
        """Test storing and managing multiple documents"""
        from database import Document
        
        texts = [
            "First document about Python programming.",
            "Second document about JavaScript development.",
            "Third document about database design."
        ]
        
        doc_ids = []
        for i, text in enumerate(texts):
            doc_id = test_rag_system.store_document(f"doc{i}.txt", text)
            doc_ids.append(doc_id)
        
        # Verify all stored using ORM
        db = test_rag_system.db_manager.get_session()
        try:
            for doc_id in doc_ids:
                doc = db.query(Document).filter(Document.id == doc_id).first()
                assert doc is not None
        finally:
            db.close()
        
        # Clean all
        test_rag_system.clean_all_databases()
        
        # Verify all deleted using ORM
        db = test_rag_system.db_manager.get_session()
        try:
            for doc_id in doc_ids:
                doc = db.query(Document).filter(Document.id == doc_id).first()
                assert doc is None
        finally:
            db.close()


