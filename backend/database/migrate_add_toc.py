#!/usr/bin/env python3
"""
Migration script to add 'toc' column to documents table
This adds the table of contents column that was introduced for the TOC feature
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
)

# Load environment variables
load_dotenv()


def migrate_add_toc_column():
    """Add toc column to documents table if it doesn't exist"""
    db_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        inspector = inspect(engine)
        
        # Check if documents table exists
        if not inspector.has_table("documents"):
            print("❌ Documents table does not exist. Please initialize the database first.")
            return False
        
        # Check if toc column already exists
        columns = [col['name'] for col in inspector.get_columns("documents")]
        if 'toc' in columns:
            print("✅ Column 'toc' already exists in documents table")
            return True
        
        # Add the toc column
        print("🔄 Adding 'toc' column to documents table...")
        with engine.connect() as conn:
            # PostgreSQL JSON column
            conn.execute(text("ALTER TABLE documents ADD COLUMN toc JSON"))
            conn.commit()
        
        print("✅ Successfully added 'toc' column to documents table")
        return True
        
    except Exception as e:
        print(f"❌ Error adding 'toc' column: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'engine' in locals():
            engine.dispose()


if __name__ == "__main__":
    print("🚀 Running migration: Add TOC column to documents table")
    print("=" * 60)
    success = migrate_add_toc_column()
    print("=" * 60)
    if success:
        print("✅ Migration completed successfully")
        sys.exit(0)
    else:
        print("❌ Migration failed")
        sys.exit(1)



