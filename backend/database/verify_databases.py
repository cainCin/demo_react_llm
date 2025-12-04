#!/usr/bin/env python3
"""
Verification script to check contents of PostgreSQL and Milvus databases
Shows all documents, chunks, and vector data stored in the RAG system
Exports synchronized data to CSV
"""
import os
import sys
import csv
from datetime import datetime
from dotenv import load_dotenv
from pymilvus import MilvusClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
    MILVUS_LITE_PATH, MILVUS_COLLECTION
)
from database.database_manager import Document, Chunk, DatabaseManager
from database import VerificationResult, DocumentListItem

# Load environment variables
load_dotenv()


def export_to_csv(db_manager, output_file="database_verification.csv"):
    """
    Export all synchronized data from PostgreSQL and Milvus to CSV
    Creates a synchronized view matching records by document_id and chunk_index
    """
    print(f"\n📊 Exporting synchronized data to {output_file}...")
    
    db = db_manager.get_session()
    csv_data = []
    
    try:
        # Get all documents from PostgreSQL
        documents = db.query(Document).order_by(Document.created_at).all()
        
        # Get all chunks from PostgreSQL
        all_chunks = db.query(Chunk).order_by(Chunk.document_id, Chunk.chunk_index).all()
        
        # Create a mapping of chunk_id (string) to chunk data
        postgres_chunks_map = {}
        for chunk in all_chunks:
            key = (chunk.document_id, chunk.chunk_index)
            postgres_chunks_map[key] = {
                'chunk_id': chunk.id,
                'document_id': chunk.document_id,
                'chunk_index': chunk.chunk_index,
                'text': chunk.text,
                'created_at': chunk.created_at.isoformat() if chunk.created_at else ''
            }
        
        # Get document info mapping
        documents_map = {doc.id: doc for doc in documents}
        
        # Get all vectors from Milvus
        milvus_vectors_map = {}
        if db_manager.milvus_client and db_manager.milvus_client.has_collection(db_manager.collection_name):
            try:
                # Note: Milvus only stores embeddings, not text. Text is in PostgreSQL.
                milvus_vectors = db_manager.milvus_client.query(
                    collection_name=db_manager.collection_name,
                    filter="",
                    limit=10000,
                    output_fields=["id", "document_id", "chunk_index"]  # No text field
                )
                
                if milvus_vectors:
                    for vector in milvus_vectors:
                        if isinstance(vector, dict):
                            doc_id = vector.get('document_id', '')
                            chunk_idx = vector.get('chunk_index', -1)
                            key = (doc_id, chunk_idx)
                            milvus_vectors_map[key] = {
                                'vector_id': vector.get('id', ''),
                                'document_id': doc_id,
                                'chunk_index': chunk_idx
                                # Note: text is NOT in Milvus, only in PostgreSQL
                            }
            except Exception as e:
                print(f"   ⚠️  Could not query Milvus vectors: {e}")
        
        # Create synchronized records
        # Get all unique keys from both databases
        all_keys = set(postgres_chunks_map.keys()) | set(milvus_vectors_map.keys())
        
        # CSV Headers - synchronized view
        headers = [
            # Document info
            'document_id',
            'document_filename',
            'document_created_at',
            'document_file_hash',
            'document_chunk_count',
            'document_full_text_length',
            # PostgreSQL Chunk info
            'postgres_chunk_id',
            'postgres_chunk_index',
            'postgres_chunk_text',
            'postgres_chunk_created_at',
            'postgres_exists',
            # Milvus Vector info (embeddings only, no text)
            'milvus_vector_id',
            'milvus_chunk_index',
            'milvus_exists',
            # Synchronization status
            'synchronized',
            'sync_notes'
        ]
        
        # Create rows
        for key in sorted(all_keys):
            doc_id, chunk_idx = key
            
            # Get document info
            doc = documents_map.get(doc_id, None)
            doc_filename = doc.filename if doc else 'N/A'
            doc_created_at = doc.created_at.isoformat() if doc and doc.created_at else 'N/A'
            doc_file_hash = doc.file_hash if doc else 'N/A'
            doc_chunk_count = doc.chunk_count if doc else 0
            doc_text_length = len(doc.full_text) if doc and doc.full_text else 0
            
            # Get PostgreSQL chunk data
            postgres_chunk = postgres_chunks_map.get(key, None)
            postgres_exists = 'Yes' if postgres_chunk else 'No'
            postgres_chunk_id = postgres_chunk['chunk_id'] if postgres_chunk else ''
            postgres_chunk_index = postgres_chunk['chunk_index'] if postgres_chunk else chunk_idx
            postgres_chunk_text = postgres_chunk['text'] if postgres_chunk else ''
            postgres_chunk_created_at = postgres_chunk['created_at'] if postgres_chunk else ''
            
            # Get Milvus vector data (embeddings only, no text)
            milvus_vector = milvus_vectors_map.get(key, None)
            milvus_exists = 'Yes' if milvus_vector else 'No'
            milvus_vector_id = str(milvus_vector['vector_id']) if milvus_vector else ''
            milvus_chunk_index = milvus_vector['chunk_index'] if milvus_vector else chunk_idx
            # Note: text is NOT stored in Milvus, only embeddings
            
            # Check synchronization
            synchronized = 'Yes' if (postgres_chunk and milvus_vector) else 'No'
            sync_notes = ''
            if not postgres_chunk and milvus_vector:
                sync_notes = 'Missing in PostgreSQL'
            elif postgres_chunk and not milvus_vector:
                sync_notes = 'Missing in Milvus'
            elif postgres_chunk and milvus_vector:
                # Both exist - synchronization OK
                # Note: text is only in PostgreSQL, not in Milvus (which only has embeddings)
                sync_notes = 'OK'
            
            # Create row
            row = [
                doc_id,
                doc_filename,
                doc_created_at,
                doc_file_hash,
                doc_chunk_count,
                doc_text_length,
                postgres_chunk_id,
                postgres_chunk_index,
                postgres_chunk_text,
                postgres_chunk_created_at,
                postgres_exists,
                milvus_vector_id,
                milvus_chunk_index,
                milvus_exists,
                synchronized,
                sync_notes
            ]
            
            csv_data.append(row)
        
        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(csv_data)
        
        print(f"✅ Exported {len(csv_data)} synchronized records to {output_file}")
        print(f"   PostgreSQL chunks: {len(postgres_chunks_map)}")
        print(f"   Milvus vectors: {len(milvus_vectors_map)}")
        print(f"   Synchronized records: {sum(1 for row in csv_data if row[headers.index('synchronized')] == 'Yes')}")
        print(f"   Missing in PostgreSQL: {sum(1 for row in csv_data if 'Missing in PostgreSQL' in row[headers.index('sync_notes')])}")
        print(f"   Missing in Milvus: {sum(1 for row in csv_data if 'Missing in Milvus' in row[headers.index('sync_notes')])}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error exporting to CSV: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

def verify_postgres():
    """Verify and display PostgreSQL database contents"""
    print("=" * 80)
    print("📊 PostgreSQL Database Verification")
    print("=" * 80)
    
    try:
        # Use DatabaseManager for verification
        db_manager = DatabaseManager()
        db_manager._init_postgres()
        db = db_manager.get_session()
        
        # Count documents
        doc_count = db.query(Document).count()
        print(f"\n📄 Documents: {doc_count}")
        
        if doc_count > 0:
            print("\n" + "-" * 80)
            documents = db.query(Document).order_by(Document.created_at.desc()).all()
            for doc in documents:
                print(f"\n📄 Document ID: {doc.id}")
                print(f"   Filename: {doc.filename}")
                print(f"   Created: {doc.created_at}")
                print(f"   Chunks: {doc.chunk_count}")
                print(f"   File Hash: {doc.file_hash}")
                print(f"   Text Preview: {doc.full_text[:200]}..." if len(doc.full_text) > 200 else f"   Text: {doc.full_text}")
            
            # Count chunks
            chunk_count = db.query(Chunk).count()
            print(f"\n\n📦 Total Chunks: {chunk_count}")
            
            # Show chunk distribution by document
            print("\n" + "-" * 80)
            print("📦 Chunks by Document:")
            for doc in documents:
                chunks = db.query(Chunk).filter(Chunk.document_id == doc.id).order_by(Chunk.chunk_index).all()
                print(f"\n   Document: {doc.filename} ({len(chunks)} chunks)")
                for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                    preview = chunk.text[:100] + "..." if len(chunk.text) > 100 else chunk.text
                    print(f"      Chunk {chunk.chunk_index}: {preview}")
                if len(chunks) > 3:
                    print(f"      ... and {len(chunks) - 3} more chunks")
        else:
            print("\n   No documents found in PostgreSQL database.")
        
        db.close()
        print("\n✅ PostgreSQL verification complete")
        return True
        
    except Exception as e:
        print(f"\n❌ Error connecting to PostgreSQL: {e}")
        print(f"   Connection details:")
        print(f"   Host: {POSTGRES_HOST}")
        print(f"   Port: {POSTGRES_PORT}")
        print(f"   Database: {POSTGRES_DB}")
        print(f"   User: {POSTGRES_USER}")
        return False


def verify_milvus():
    """Verify and display Milvus Lite database contents"""
    print("\n" + "=" * 80)
    print("🔍 Milvus Lite Database Verification")
    print("=" * 80)
    
    try:
        # Convert relative path to absolute path
        milvus_path = os.path.abspath(MILVUS_LITE_PATH)
        
        # Ensure the path ends with .db
        if not milvus_path.endswith('.db'):
            milvus_path = os.path.join(milvus_path, 'milvus_lite.db')
        
        print(f"\n📁 Milvus Lite Path: {milvus_path}")
        
        if not os.path.exists(milvus_path):
            print(f"⚠️  Milvus Lite database file not found at: {milvus_path}")
            print("   The database will be created when the first document is stored.")
            return False
        
        # Connect to Milvus Lite
        milvus_client = MilvusClient(uri=milvus_path)
        
        # Check if collection exists
        if not milvus_client.has_collection(MILVUS_COLLECTION):
            print(f"\n⚠️  Collection '{MILVUS_COLLECTION}' does not exist in Milvus Lite.")
            print("   The collection will be created when the first document is stored.")
            return False
        
        print(f"✅ Collection '{MILVUS_COLLECTION}' exists")
        
        # Get collection info
        collection_info = milvus_client.describe_collection(MILVUS_COLLECTION)
        print(f"\n📊 Collection Info:")
        print(f"   Name: {collection_info.get('collection_name', 'N/A')}")
        print(f"   Description: {collection_info.get('description', 'N/A')}")
        
        # Count entities and get data
        try:
            # Query all entities - Milvus Lite query method
            # Try different query approaches based on pymilvus version
            all_data = []
            try:
                # Method 1: Query with empty filter (newer API)
                # Note: Milvus only stores embeddings, not text. Text is in PostgreSQL.
                all_data = milvus_client.query(
                    collection_name=MILVUS_COLLECTION,
                    filter="",
                    limit=10000,
                    output_fields=["id", "document_id", "chunk_index"]  # No text field
                )
            except Exception as e1:
                try:
                    # Method 2: Query with expr parameter
                    all_data = milvus_client.query(
                        collection_name=MILVUS_COLLECTION,
                        expr="id != ''",  # Expression that matches all
                        limit=10000,
                        output_fields=["id", "document_id", "chunk_index"]  # No text field
                    )
                except Exception as e2:
                    try:
                        # Method 3: Query without filter (may work in some versions)
                        all_data = milvus_client.query(
                            collection_name=MILVUS_COLLECTION,
                            limit=10000,
                            output_fields=["id", "document_id", "chunk_index"]  # No text field
                        )
                    except Exception as e3:
                        # If all query methods fail, try to get collection stats
                        print(f"   ⚠️  Could not query entities directly: {e3}")
                        print("   Trying alternative method...")
                        # We'll show what we can from collection info
                        all_data = []
            
            entity_count = len(all_data) if all_data else 0
            print(f"\n📦 Total Vectors: {entity_count}")
            
            if entity_count == 0:
                print("\n   No vectors found in Milvus Lite collection.")
                print("   This is normal if no documents have been uploaded yet.")
            elif entity_count > 0:
                # Group by document_id
                from collections import defaultdict
                doc_chunks = defaultdict(list)
                for item in all_data:
                    # Handle both dict and object-like responses
                    if isinstance(item, dict):
                        doc_id = item.get('document_id', 'unknown')
                        doc_chunks[doc_id].append(item)
                    else:
                        doc_id = getattr(item, 'document_id', 'unknown')
                        doc_chunks[doc_id].append({
                            'chunk_index': getattr(item, 'chunk_index', 'N/A')
                            # Note: text is NOT in Milvus, only embeddings
                        })
                
                print(f"\n📄 Vectors by Document:")
                for doc_id, chunks in doc_chunks.items():
                    print(f"\n   Document ID: {doc_id} ({len(chunks)} vectors)")
                    # Show first few chunks
                    sorted_chunks = sorted(chunks, key=lambda x: x.get('chunk_index', 0) if isinstance(x, dict) else getattr(x, 'chunk_index', 0))
                    for chunk in sorted_chunks[:3]:
                        if isinstance(chunk, dict):
                            chunk_idx = chunk.get('chunk_index', 'N/A')
                        else:
                            chunk_idx = getattr(chunk, 'chunk_index', 'N/A')
                        # Note: text is NOT in Milvus, only embeddings. Text is in PostgreSQL.
                        print(f"      Chunk {chunk_idx}: [Embedding only - text in PostgreSQL]")
                    if len(chunks) > 3:
                        print(f"      ... and {len(chunks) - 3} more vectors")
                
                # Show sample vector info (vectors aren't returned in query, only metadata)
                if all_data:
                    sample = all_data[0]
                    print(f"\n📐 Sample Entity Info:")
                    if isinstance(sample, dict):
                        print(f"   Entity ID: {sample.get('id', 'N/A')}")
                        print(f"   Document ID: {sample.get('document_id', 'N/A')}")
                        print(f"   Chunk Index: {sample.get('chunk_index', 'N/A')}")
                    else:
                        print(f"   Entity ID: {getattr(sample, 'id', 'N/A')}")
                        print(f"   Document ID: {getattr(sample, 'document_id', 'N/A')}")
                        print(f"   Chunk Index: {getattr(sample, 'chunk_index', 'N/A')}")
            else:
                print("\n   No vectors found in Milvus Lite collection.")
        
        except Exception as e:
            print(f"\n⚠️  Could not query collection: {e}")
            print("   Collection exists but may be empty or have access issues.")
            import traceback
            print(f"   Error details: {traceback.format_exc()}")
        
        print("\n✅ Milvus Lite verification complete")
        return True
        
    except Exception as e:
        print(f"\n❌ Error connecting to Milvus Lite: {e}")
        print(f"   Path: {MILVUS_LITE_PATH}")
        return False




def main():
    """Main verification function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify and export RAG system databases')
    parser.add_argument('--output', '-o', default='database_verification.csv',
                       help='Output CSV file path (default: database_verification.csv)')
    parser.add_argument('--no-export', action='store_true',
                       help='Skip CSV export, only show console output')
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("🔍 RAG System Database Verification")
    print("=" * 80)
    print(f"\nChecking databases for RAG system...")
    print(f"PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    print(f"Milvus Lite: {MILVUS_LITE_PATH}")
    
    postgres_ok = False
    milvus_ok = False
    db_manager = None
    
    # Use DatabaseManager for comprehensive verification
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        # Run general verification
        print("\n" + "=" * 80)
        print("🔄 Database Verification (using DatabaseManager)")
        print("=" * 80)
        verification_result = db_manager.verify()
        
        print(f"\n📊 Verification Results:")
        print(f"   PostgreSQL: {'✅ Connected' if verification_result.postgres_connected else '❌ Failed'}")
        print(f"   Milvus: {'✅ Connected' if verification_result.milvus_connected else '❌ Failed'}")
        print(f"   Synchronized: {'✅ Yes' if verification_result.synchronized else '❌ No'}")
        print(f"\n📈 Counts:")
        print(f"   PostgreSQL documents: {verification_result.postgres_documents}")
        print(f"   PostgreSQL chunks: {verification_result.postgres_chunks}")
        print(f"   Milvus vectors: {verification_result.milvus_vectors}")
        
        if verification_result.issues:
            print(f"\n⚠️  Issues found:")
            for issue in verification_result.issues:
                print(f"   - {issue}")
        
        postgres_ok = verification_result.postgres_connected
        milvus_ok = verification_result.milvus_connected
        
        # Export to CSV if requested
        if not args.no_export and db_manager:
            export_to_csv(db_manager, args.output)
        
        # Also run detailed verification
        print("\n" + "=" * 80)
        print("📋 Detailed Verification")
        print("=" * 80)
        postgres_ok = verify_postgres()
        milvus_ok = verify_milvus()
    
    except Exception as e:
        print(f"   ⚠️  Could not perform verification: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("📋 Summary")
    print("=" * 80)
    print(f"PostgreSQL: {'✅ Connected' if postgres_ok else '❌ Failed'}")
    print(f"Milvus Lite: {'✅ Connected' if milvus_ok else '❌ Failed'}")
    print("\n💡 Tips:")
    print("   - Use DELETE /api/documents to clean all databases")
    print("   - Use GET /api/documents/sync to check synchronization")
    print("   - Use POST /api/documents/resync to resynchronize databases")
    if not args.no_export:
        print(f"   - CSV export saved to: {args.output}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

