#!/usr/bin/env python3
"""
Synchronization Verification Script
Verifies that all data classes are properly synchronized with ORM models
and that all required methods are implemented correctly.
"""
import sys
import os
import inspect
from typing import get_type_hints, get_origin, get_args
from dataclasses import fields

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database.database_manager import Document, Chunk
    from database.models import (
        DocumentData, ChunkData, VectorData, SearchResult,
        VerificationResult, ResyncResult, DocumentListItem
    )
except ImportError as e:
    print(f"⚠️  Warning: Could not import database modules: {e}")
    print("   This script requires the database package to be installed.")
    print("   Run: pip install -r requirements.txt")
    sys.exit(1)


def get_orm_fields(orm_class):
    """Extract field names and types from SQLAlchemy ORM model"""
    fields_dict = {}
    for column in orm_class.__table__.columns:
        fields_dict[column.name] = {
            'type': str(column.type),
            'nullable': column.nullable,
            'primary_key': column.primary_key
        }
    return fields_dict


def get_dataclass_fields(dataclass_type):
    """Extract field names and types from dataclass"""
    fields_dict = {}
    for field_obj in fields(dataclass_type):
        field_type = field_obj.type
        # Handle Optional types
        if get_origin(field_type) is type(None) or (hasattr(field_type, '__origin__') and field_type.__origin__ is type(None)):
            field_type = get_args(field_type)[0] if get_args(field_type) else field_type
        elif hasattr(field_type, '__origin__'):
            field_type = field_type.__origin__
        
        fields_dict[field_obj.name] = {
            'type': str(field_type),
            'default': field_obj.default if field_obj.default is not inspect.Parameter.empty else None,
            'default_factory': field_obj.default_factory if field_obj.default_factory is not inspect.Parameter.empty else None
        }
    return fields_dict


def check_synchronization(orm_class, dataclass_type, dataclass_name):
    """Check if dataclass fields match ORM model fields"""
    print(f"\n{'='*60}")
    print(f"Checking: {dataclass_name} vs {orm_class.__name__}")
    print(f"{'='*60}")
    
    orm_fields = get_orm_fields(orm_class)
    dataclass_fields = get_dataclass_fields(dataclass_type)
    
    issues = []
    
    # Check all ORM fields exist in dataclass
    for orm_field_name, orm_info in orm_fields.items():
        if orm_field_name not in dataclass_fields:
            issues.append(f"❌ Missing field in {dataclass_name}: {orm_field_name} (from ORM)")
        else:
            print(f"✅ {orm_field_name}: ORM → {dataclass_name}")
    
    # Check for extra fields in dataclass (warn but allow)
    for dc_field_name in dataclass_fields:
        if dc_field_name not in orm_fields:
            print(f"⚠️  Extra field in {dataclass_name}: {dc_field_name} (not in ORM - may be computed)")
    
    # Check for from_orm method
    if hasattr(dataclass_type, 'from_orm'):
        print(f"✅ {dataclass_name}.from_orm() method exists")
    else:
        issues.append(f"❌ Missing from_orm() method in {dataclass_name}")
    
    # Check for to_dict method
    if hasattr(dataclass_type, 'to_dict'):
        print(f"✅ {dataclass_name}.to_dict() method exists")
    else:
        issues.append(f"❌ Missing to_dict() method in {dataclass_name}")
    
    return issues


def check_dataclass_completeness(dataclass_type, dataclass_name):
    """Check if dataclass has required methods"""
    print(f"\n{'='*60}")
    print(f"Checking: {dataclass_name} completeness")
    print(f"{'='*60}")
    
    issues = []
    
    # Check for to_dict method
    if hasattr(dataclass_type, 'to_dict'):
        print(f"✅ {dataclass_name}.to_dict() method exists")
    else:
        issues.append(f"❌ Missing to_dict() method in {dataclass_name}")
    
    # Check fields
    dc_fields = get_dataclass_fields(dataclass_type)
    print(f"✅ {dataclass_name} has {len(dc_fields)} fields:")
    for field_name, field_info in dc_fields.items():
        default_info = ""
        if field_info['default'] is not None:
            default_info = f" (default: {field_info['default']})"
        elif field_info['default_factory'] is not None:
            default_info = f" (default_factory: {field_info['default_factory']})"
        print(f"   - {field_name}: {field_info['type']}{default_info}")
    
    return issues


def main():
    """Run all synchronization checks"""
    print("🔍 Database Synchronization Verification")
    print("=" * 60)
    
    all_issues = []
    
    # Check DocumentData vs Document
    issues = check_synchronization(Document, DocumentData, "DocumentData")
    all_issues.extend(issues)
    
    # Check ChunkData vs Chunk
    issues = check_synchronization(Chunk, ChunkData, "ChunkData")
    all_issues.extend(issues)
    
    # Check DocumentListItem (subset of Document)
    print(f"\n{'='*60}")
    print(f"Checking: DocumentListItem (subset of Document)")
    print(f"{'='*60}")
    doc_fields = get_orm_fields(Document)
    listitem_fields = get_dataclass_fields(DocumentListItem)
    for field_name in listitem_fields:
        if field_name in doc_fields:
            print(f"✅ {field_name}: Document → DocumentListItem")
        else:
            all_issues.append(f"❌ DocumentListItem has field {field_name} not in Document")
    if hasattr(DocumentListItem, 'from_orm'):
        print(f"✅ DocumentListItem.from_orm() method exists")
    if hasattr(DocumentListItem, 'to_dict'):
        print(f"✅ DocumentListItem.to_dict() method exists")
    
    # Check standalone data classes
    issues = check_dataclass_completeness(VectorData, "VectorData")
    all_issues.extend(issues)
    
    issues = check_dataclass_completeness(SearchResult, "SearchResult")
    all_issues.extend(issues)
    
    issues = check_dataclass_completeness(VerificationResult, "VerificationResult")
    all_issues.extend(issues)
    
    issues = check_dataclass_completeness(ResyncResult, "ResyncResult")
    all_issues.extend(issues)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if all_issues:
        print(f"❌ Found {len(all_issues)} synchronization issue(s):")
        for issue in all_issues:
            print(f"   {issue}")
        return 1
    else:
        print("✅ All data classes are properly synchronized!")
        print("\n✅ All required methods (from_orm, to_dict) are implemented")
        print("✅ All ORM fields are represented in data classes")
        return 0


if __name__ == "__main__":
    sys.exit(main())

