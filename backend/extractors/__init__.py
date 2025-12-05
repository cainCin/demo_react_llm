"""
Extractors Package
Contains all text extraction and processing utilities:
- TOC (Table of Contents) extraction
- Text chunking strategies

Follows convention rules:
- PascalCase for classes
- snake_case for functions
- Type hints for all functions
- Docstrings for all public methods
- Data classes are in database/models.py (TOCItem imported from there)
"""
# Import TOCItem from database/models.py (following convention: data classes in models.py)
from database.models import TOCItem

from extractors.toc_extractor import (
    extract_toc,
    extract_toc_markdown,
    extract_toc_text,
    extract_toc_python,
    extract_toc_paragraphs,
    extract_toc_html,
    build_toc_hierarchy,
    map_toc_to_chunks
)
from extractors.chunk_extractor import (
    ChunkExtractor,
    chunk_text_simple,
    chunk_text_toc_aware
)

__all__ = [
    # TOC extractor
    'TOCItem',
    'extract_toc',
    'extract_toc_markdown',
    'extract_toc_text',
    'extract_toc_python',
    'extract_toc_paragraphs',
    'extract_toc_html',
    'build_toc_hierarchy',
    'map_toc_to_chunks',
    # Chunk extractor
    'ChunkExtractor',
    'chunk_text_simple',
    'chunk_text_toc_aware'
]

