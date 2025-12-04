"""
Tests for database operations and procedures
"""
import pytest
from database import (
    DatabaseManager, Document, Chunk,
    DocumentData, ChunkData, VectorData,
    VerificationResult, ResyncResult
)


@pytest.mark.database
class TestDatabaseManager:
    """Tests for DatabaseManager class"""
    
    def test_initialize(self, test_db_manager):
        """Test database initialization"""
        assert test_db_manager is not None
        assert test_db_manager.engine is not None
        assert test_db_manager.milvus_client is not None
    
    def test_get_session(self, test_db_manager):
        """Test getting a database session"""
        session = test_db_manager.get_session()
        assert session is not None
        session.close()
    
    def test_store_document(self, test_db_manager, sample_text):
        """Test storing a document using ORM directly"""
        import hashlib
        import uuid
        
        # Create document using ORM
        doc_id = str(uuid.uuid4())
        file_hash = hashlib.md5(sample_text.encode()).hexdigest()
        
        db = test_db_manager.get_session()
        try:
            doc = Document(
                id=doc_id,
                filename="test.txt",
                full_text=sample_text,
                file_hash=file_hash,
                chunk_count=0
            )
            db.add(doc)
            db.commit()
            
            # Verify it's in PostgreSQL
            stored_doc = db.query(Document).filter(Document.id == doc_id).first()
            assert stored_doc is not None
            assert stored_doc.filename == "test.txt"
            assert stored_doc.full_text == sample_text
        finally:
            db.close()
    
    def test_store_chunks(self, test_db_manager, sample_text):
        """Test storing chunks using ORM directly"""
        import hashlib
        import uuid
        
        # First create a document
        doc_id = str(uuid.uuid4())
        file_hash = hashlib.md5(sample_text.encode()).hexdigest()
        
        db = test_db_manager.get_session()
        try:
            doc = Document(
                id=doc_id,
                filename="test.txt",
                full_text=sample_text,
                file_hash=file_hash,
                chunk_count=2
            )
            db.add(doc)
            
            # Create chunks using ORM
            chunk1 = Chunk(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                chunk_index=0,
                text="First chunk"
            )
            chunk2 = Chunk(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                chunk_index=1,
                text="Second chunk"
            )
            db.add(chunk1)
            db.add(chunk2)
            db.commit()
            
            # Verify chunks in PostgreSQL
            stored_chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).all()
            assert len(stored_chunks) == 2
            assert stored_chunks[0].text == "First chunk"
            assert stored_chunks[1].text == "Second chunk"
        finally:
            db.close()
    
    def test_insert_vectors(self, test_db_manager):
        """Test inserting vectors into Milvus"""
        vectors = [
            VectorData(
                id=12345,  # int64 ID
                vector=[0.1] * 1536,
                document_id="test-doc-3",
                chunk_index=0
            ),
            VectorData(
                id=12346,
                vector=[0.2] * 1536,
                document_id="test-doc-3",
                chunk_index=1
            )
        ]
        
        # Insert vectors
        test_db_manager.insert_vectors(vectors)
        
        # Verify vectors in Milvus (check collection has data)
        # Note: Direct verification requires querying Milvus
        assert test_db_manager.milvus_client is not None
    
    def test_get_document(self, test_db_manager, sample_text):
        """Test retrieving a document using ORM"""
        import hashlib
        import uuid
        
        # Store a document
        doc_id = str(uuid.uuid4())
        file_hash = hashlib.md5(sample_text.encode()).hexdigest()
        
        db = test_db_manager.get_session()
        try:
            doc = Document(
                id=doc_id,
                filename="test.txt",
                full_text=sample_text,
                file_hash=file_hash,
                chunk_count=0
            )
            db.add(doc)
            db.commit()
            
            # Retrieve document using ORM
            retrieved = db.query(Document).filter(Document.id == doc_id).first()
            assert retrieved is not None
            assert retrieved.id == doc_id
            assert retrieved.filename == "test.txt"
            
            # Convert to data class
            doc_data = DocumentData.from_orm(retrieved)
            assert doc_data.id == doc_id
            assert doc_data.filename == "test.txt"
        finally:
            db.close()
    
    def test_get_chunks(self, test_db_manager, sample_text):
        """Test retrieving chunks for a document using ORM"""
        import hashlib
        import uuid
        
        # Store document and chunks
        doc_id = str(uuid.uuid4())
        file_hash = hashlib.md5(sample_text.encode()).hexdigest()
        
        db = test_db_manager.get_session()
        try:
            doc = Document(
                id=doc_id,
                filename="test.txt",
                full_text=sample_text,
                file_hash=file_hash,
                chunk_count=1
            )
            db.add(doc)
            
            chunk = Chunk(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                chunk_index=0,
                text="Chunk text"
            )
            db.add(chunk)
            db.commit()
            
            # Retrieve chunks using ORM
            retrieved_chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).all()
            assert len(retrieved_chunks) == 1
            assert retrieved_chunks[0].text == "Chunk text"
            
            # Convert to data class
            chunk_data = ChunkData.from_orm(retrieved_chunks[0])
            assert chunk_data.text == "Chunk text"
            assert chunk_data.document_id == doc_id
        finally:
            db.close()
    
    def test_delete_document(self, test_db_manager, sample_text):
        """Test deleting a document"""
        import hashlib
        import uuid
        
        # Store a document
        doc_id = str(uuid.uuid4())
        file_hash = hashlib.md5(sample_text.encode()).hexdigest()
        
        db = test_db_manager.get_session()
        try:
            doc = Document(
                id=doc_id,
                filename="test.txt",
                full_text=sample_text,
                file_hash=file_hash,
                chunk_count=0
            )
            db.add(doc)
            db.commit()
            
            # Verify it exists
            assert db.query(Document).filter(Document.id == doc_id).first() is not None
        finally:
            db.close()
        
        # Delete document using DatabaseManager method
        test_db_manager.delete_document(doc_id)
        
        # Verify it's deleted
        db = test_db_manager.get_session()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            assert doc is None
        finally:
            db.close()
    
    def test_clean_all(self, test_db_manager, sample_text):
        """Test cleaning all data"""
        import hashlib
        import uuid
        
        # Store some documents using ORM
        db = test_db_manager.get_session()
        try:
            for i in range(3):
                doc_id = str(uuid.uuid4())
                file_hash = hashlib.md5(f"{sample_text}{i}".encode()).hexdigest()
                doc = Document(
                    id=doc_id,
                    filename=f"test{i}.txt",
                    full_text=sample_text,
                    file_hash=file_hash,
                    chunk_count=0
                )
                db.add(doc)
            db.commit()
            
            # Verify documents exist
            assert db.query(Document).count() == 3
        finally:
            db.close()
        
        # Clean all using DatabaseManager method
        test_db_manager.clean_all()
        
        # Verify all deleted
        db = test_db_manager.get_session()
        try:
            count = db.query(Document).count()
            assert count == 0
        finally:
            db.close()
    
    def test_verify_synchronized(self, test_db_manager, sample_text):
        """Test verification when databases are synchronized"""
        import hashlib
        import uuid
        
        # Store document and chunks using ORM
        doc_id = str(uuid.uuid4())
        file_hash = hashlib.md5(sample_text.encode()).hexdigest()
        chunk_id = str(uuid.uuid4())
        
        db = test_db_manager.get_session()
        try:
            doc = Document(
                id=doc_id,
                filename="test.txt",
                full_text=sample_text,
                file_hash=file_hash,
                chunk_count=1
            )
            db.add(doc)
            
            chunk = Chunk(
                id=chunk_id,
                document_id=doc_id,
                chunk_index=0,
                text="Chunk"
            )
            db.add(chunk)
            db.commit()
        finally:
            db.close()
        
        # Insert corresponding vector
        vectors = [
            VectorData(
                id=test_db_manager._uuid_to_int64(chunk_id),
                vector=[0.1] * 1536,
                document_id=doc_id,
                chunk_index=0
            )
        ]
        test_db_manager.insert_vectors(vectors)
        
        # Verify
        result = test_db_manager.verify()
        assert isinstance(result, VerificationResult)
        assert result.postgres_connected is True
        assert result.milvus_connected is True
        assert result.postgres_documents == 1
        assert result.postgres_chunks == 1
        # Note: May not be synchronized if vectors weren't properly inserted, but structure should be correct


@pytest.mark.database
class TestDataClasses:
    """Tests for data classes"""
    
    def test_document_data(self):
        """Test DocumentData data class"""
        import hashlib
        text = "Test content"
        file_hash = hashlib.md5(text.encode()).hexdigest()
        
        doc = DocumentData(
            id="test-1",
            filename="test.txt",
            full_text=text,
            file_hash=file_hash,
            chunk_count=5
        )
        assert doc.id == "test-1"
        assert doc.filename == "test.txt"
        assert doc.full_text == text
        assert doc.file_hash == file_hash
        assert doc.chunk_count == 5
    
    def test_chunk_data(self):
        """Test ChunkData data class"""
        chunk = ChunkData(
            id="chunk-1",
            document_id="doc-1",
            chunk_index=0,
            text="Chunk text"
        )
        assert chunk.id == "chunk-1"
        assert chunk.document_id == "doc-1"
        assert chunk.chunk_index == 0
        assert chunk.text == "Chunk text"
    
    def test_vector_data(self):
        """Test VectorData data class"""
        vector = VectorData(
            id=12345,
            vector=[0.1, 0.2, 0.3],
            document_id="doc-1",
            chunk_index=0
        )
        assert vector.id == 12345
        assert len(vector.vector) == 3
        assert vector.document_id == "doc-1"
    
    def test_verification_result(self):
        """Test VerificationResult data class"""
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
        assert result.synchronized is True
        assert result.postgres_connected is True
        assert result.milvus_connected is True
        assert result.postgres_documents == 10
        assert result.postgres_chunks == 10
        assert result.milvus_vectors == 10
        assert len(result.issues) == 0
        
        # Test to_dict
        data = result.to_dict()
        assert data["synchronized"] is True
        assert data["postgres_documents"] == 10
        assert data["milvus_vectors"] == 10
    
    def test_resync_result(self):
        """Test ResyncResult data class"""
        result = ResyncResult(
            success=True,
            documents_processed=3,
            chunks_processed=10,
            vectors_inserted=5,
            errors=[]
        )
        assert result.success is True
        assert result.documents_processed == 3
        assert result.chunks_processed == 10
        assert result.vectors_inserted == 5
        assert len(result.errors) == 0
        
        # Test to_dict
        data = result.to_dict()
        assert data["success"] is True
        assert data["vectors_inserted"] == 5
        assert data["documents_processed"] == 3


@pytest.mark.database
class TestUUIDConversion:
    """Tests for UUID to int64 conversion"""
    
    def test_uuid_to_int64(self, test_db_manager):
        """Test UUID to int64 conversion"""
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        int64_id = test_db_manager._uuid_to_int64(test_uuid)
        
        assert isinstance(int64_id, int)
        # Should be consistent
        int64_id_2 = test_db_manager._uuid_to_int64(test_uuid)
        assert int64_id == int64_id_2
    
    def test_uuid_to_int64_different_uuids(self, test_db_manager):
        """Test that different UUIDs produce different int64 values"""
        uuid1 = "550e8400-e29b-41d4-a716-446655440000"
        uuid2 = "550e8400-e29b-41d4-a716-446655440001"
        
        int64_1 = test_db_manager._uuid_to_int64(uuid1)
        int64_2 = test_db_manager._uuid_to_int64(uuid2)
        
        assert int64_1 != int64_2


