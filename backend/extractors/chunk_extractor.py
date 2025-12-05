"""
Text Chunking Extractor
Provides various chunking strategies for text processing
"""
import re
from typing import List, Optional, Dict, Tuple

from config import (
    CHUNK_SIZE, CHUNK_OVERLAP, CHUNK_MIN_SIZE, EMBEDDING_MAX_LENGTH
)

try:
    from extractors.toc_extractor import extract_toc
    from database.models import TOCItem  # Data class in models.py (following convention)
except ImportError:
    extract_toc = None
    TOCItem = None


class ChunkExtractor:
    """
    Text chunking extractor with multiple strategies
    Follows convention: PascalCase for class name
    """
    
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        embedding_max_length: Optional[int] = None
    ):
        """
        Initialize chunk extractor
        
        Args:
            chunk_size: Default chunk size in characters
            chunk_overlap: Default overlap between chunks
            embedding_max_length: Maximum length for embedding model
        """
        self.chunk_size = chunk_size or CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or CHUNK_OVERLAP
        self.embedding_max_length = embedding_max_length or EMBEDDING_MAX_LENGTH
    
    def chunk_text_simple(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[str]:
        """
        Simple chunking strategy: split text into overlapping chunks
        Uses config values if parameters not provided
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk (default: from config)
            chunk_overlap: Overlap between chunks (default: from config)
            
        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        
        if not text or len(text) <= chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary if not at end
            if end < len(text):
                # Look for sentence endings
                for break_char in ['. ', '.\n', '! ', '!\n', '? ', '?\n', '\n\n']:
                    last_break = chunk.rfind(break_char)
                    if last_break > chunk_size * 0.5:  # Only break if we're past halfway
                        chunk = chunk[:last_break + len(break_char)]
                        end = start + len(chunk)
                        break
            
            # Only add chunk if it meets minimum size requirement
            chunk_text = chunk.strip()
            if len(chunk_text) >= CHUNK_MIN_SIZE or start == 0:  # Always include first chunk
                chunks.append(chunk_text)
            
            # Move start position with overlap
            start = end - chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def chunk_text_toc_aware(
        self,
        text: str,
        filename: str
    ) -> Tuple[List[str], Optional[List[Dict]]]:
        """
        TOC-aware chunking strategy that aligns chunks with TOC sections
        - Each chunk belongs to only one TOC element
        - Long sections are split at paragraph boundaries
        - Respects embedding model max length (8000 characters)
        
        Args:
            text: Document text content
            filename: Original filename (for format detection)
            
        Returns:
            Tuple of (chunks: List[str], toc: Optional[List[Dict]])
        """
        if not text:
            return [], None
        
        # Extract TOC first
        toc_data = None
        toc_items = None
        if extract_toc:
            try:
                toc_items_dict = extract_toc(text, filename)
                if toc_items_dict:
                    # Convert dict to TOCItem objects for processing
                    def dict_to_toc_item(d: Dict) -> TOCItem:
                        item = TOCItem(
                            title=d['title'],
                            level=d['level'],
                            position=d['position']
                        )
                        item.children = [dict_to_toc_item(child) for child in d.get('children', [])]
                        return item
                    
                    toc_items = [dict_to_toc_item(item) for item in toc_items_dict]
                    toc_data = toc_items_dict
            except Exception as e:
                print(f"⚠️  Failed to extract TOC for chunking: {e}")
        
        # If no TOC, fall back to regular chunking
        if not toc_items:
            chunks = self.chunk_text_simple(text)
            return chunks, None
        
        # Flatten TOC to get all individual items (not sections) with their boundaries
        # This ensures each TOC item gets its own chunk(s)
        def flatten_toc_items(
            items: List[TOCItem],
            all_items: List[Tuple[int, int, str, TOCItem]] = None
        ) -> List[Tuple[int, int, str, TOCItem]]:
            """Flatten TOC to get (start_pos, end_pos, title, item) tuples for each individual item"""
            if all_items is None:
                all_items = []
            
            # First, collect all items recursively (including children) to find boundaries
            def collect_all_items(items_list: List[TOCItem], collected: List[TOCItem] = None) -> List[TOCItem]:
                """Recursively collect all TOC items"""
                if collected is None:
                    collected = []
                for item in items_list:
                    collected.append(item)
                    if item.children:
                        collect_all_items(item.children, collected)
                return collected
            
            all_toc_items_flat = collect_all_items(items)
            
            for item in items:
                # Find end position (next sibling at same or higher level)
                end_pos = len(text)  # Default to end of document
                
                # Find next item at same or higher level
                for other_item in all_toc_items_flat:
                    if other_item.position > item.position and other_item.level <= item.level:
                        end_pos = min(end_pos, other_item.position)
                
                all_items.append((item.position, end_pos, item.title, item))
                
                # Process children recursively (they will have their own boundaries)
                if item.children:
                    flatten_toc_items(item.children, all_items)
            
            return all_items
        
        # Get all individual TOC items (not sections)
        all_toc_items = flatten_toc_items(toc_items)
        
        # Sort by position
        all_toc_items.sort(key=lambda x: x[0])
        
        # Don't filter out items - each TOC item should get its own chunk
        # Adjust end positions to next item start to avoid overlap
        processed_items = []
        for i, (start, end, title, item) in enumerate(all_toc_items):
            # Adjust end position to next item start (at same or higher level)
            actual_end = end
            for other_start, _, _, other_item in all_toc_items:
                # Only consider items at same or higher level
                if other_start > start and other_item.level <= item.level:
                    actual_end = min(actual_end, other_start)
            
            processed_items.append((start, actual_end, title, item))
        
        # Sort processed items by start position
        processed_items.sort(key=lambda x: x[0])
        
        chunks = []
        chunk_to_toc_map = []  # Track which TOC item each chunk belongs to (item_key, chunk_index_in_item)
        # Structure: (item_key, chunk_index_in_item) where item_key is (position, title) and chunk_index_in_item is 0-based within that item
        
        for item_start, item_end, item_title, item in processed_items:
            item_text = text[item_start:item_end].strip()
            
            if not item_text:
                continue
            
            # Each TOC item gets its own chunk(s) - never combine multiple TOC items
            # Create a unique key for this item (position, title)
            item_key = (item_start, item_title)
            
            # If item fits within embedding limit, use as single chunk
            if len(item_text) <= self.embedding_max_length:
                chunks.append(item_text)
                chunk_to_toc_map.append((item_key, 0))  # First (and only) chunk of this item
            else:
                # Item is too long - split at paragraph boundaries
                # Each resulting chunk will be part of the same TOC item
                paragraphs = item_text.split('\n\n')
                current_chunk = ""
                chunk_index_in_item = 0
                
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue
                    
                    # If adding this paragraph would exceed limit, finalize current chunk
                    if current_chunk and len(current_chunk) + len(para) + 2 > self.embedding_max_length:
                        if current_chunk:
                            chunks.append(current_chunk)
                            chunk_to_toc_map.append((item_key, chunk_index_in_item))
                            chunk_index_in_item += 1
                        current_chunk = para
                    else:
                        # Add paragraph to current chunk
                        if current_chunk:
                            current_chunk += "\n\n" + para
                        else:
                            current_chunk = para
                    
                    # If single paragraph exceeds limit, split it at sentence boundaries
                    if len(current_chunk) > self.embedding_max_length:
                        # Split the oversized paragraph
                        sentences = re.split(r'([.!?]\s+|[.!?]\n+)', current_chunk)
                        temp_chunk = ""
                        
                        for i in range(0, len(sentences), 2):
                            sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
                            
                            if temp_chunk and len(temp_chunk) + len(sentence) > self.embedding_max_length:
                                if temp_chunk:
                                    chunks.append(temp_chunk.strip())
                                    chunk_to_toc_map.append((item_key, chunk_index_in_item))
                                    chunk_index_in_item += 1
                                temp_chunk = sentence
                            else:
                                temp_chunk += sentence
                        
                        current_chunk = temp_chunk
                
                # Add remaining chunk
                if current_chunk:
                    chunks.append(current_chunk)
                    chunk_to_toc_map.append((item_key, chunk_index_in_item))
        
        # If no chunks were created (no TOC sections), fall back to regular chunking
        if not chunks:
            chunks = self.chunk_text_simple(text)
            return chunks, toc_data
        
        # Map TOC items to chunks - ensure 1 TOC item = 1 chunk (or multiple chunks for same item if too long)
        if toc_items and chunks:
            # Create a mapping from item keys to TOC items
            item_key_to_item = {}  # (position, title) -> TOCItem
            def build_item_map(items: List[TOCItem]):
                """Build mapping from item keys to TOC items"""
                for item in items:
                    item_key_to_item[(item.position, item.title)] = item
                    if item.children:
                        build_item_map(item.children)
            
            build_item_map(toc_items)
            
            # Group chunks by TOC item key
            item_chunks = {}  # item_key -> list of (chunk_idx, chunk_index_in_item)
            for chunk_idx, (item_key, chunk_index_in_item) in enumerate(chunk_to_toc_map):
                if item_key not in item_chunks:
                    item_chunks[item_key] = []
                item_chunks[item_key].append((chunk_idx, chunk_index_in_item))
            
            # Create new TOC items: one per chunk (or multiple for long items)
            def process_toc_items(items: List[TOCItem]) -> List[TOCItem]:
                """Process TOC items and create one TOC item per chunk"""
                result = []
                for item in items:
                    item_key = (item.position, item.title)
                    if item_key in item_chunks:
                        # This item has chunks - create one TOC item per chunk
                        item_chunk_list = sorted(item_chunks[item_key], key=lambda x: x[1])
                        
                        for chunk_idx, chunk_index_in_item in item_chunk_list:
                            # Create a new TOC item for this chunk
                            chunk_toc_item = TOCItem(
                                title=item.title if chunk_index_in_item == 0 else f"{item.title} (Part {chunk_index_in_item + 1})",
                                level=item.level,
                                position=item.position if chunk_index_in_item == 0 else None,
                                chunk_start=chunk_idx,
                                chunk_end=chunk_idx  # 1 chunk per TOC item
                            )
                            
                            # Process children if this is the first chunk
                            if chunk_index_in_item == 0 and item.children:
                                chunk_toc_item.children = process_toc_items(item.children)
                            
                            result.append(chunk_toc_item)
                    else:
                        # No chunks found for this item, keep original structure
                        new_item = TOCItem(
                            title=item.title,
                            level=item.level,
                            position=item.position,
                            chunk_start=None,
                            chunk_end=None
                        )
                        if item.children:
                            new_item.children = process_toc_items(item.children)
                        result.append(new_item)
                
                return result
            
            # Process all TOC items
            processed_toc_items = process_toc_items(toc_items)
            
            # Convert back to dict format
            def toc_item_to_dict(item: TOCItem) -> Dict:
                """Convert TOCItem to dict"""
                result = {
                    'title': item.title,
                    'level': item.level,
                    'position': item.position,
                    'chunk_start': item.chunk_start,
                    'chunk_end': item.chunk_end
                }
                if item.children:
                    result['children'] = [toc_item_to_dict(child) for child in item.children]
                return result
            
            toc_data = [toc_item_to_dict(item) for item in processed_toc_items]
        
        return chunks, toc_data


# Module-level convenience functions (following convention: snake_case)
def chunk_text_simple(
    text: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> List[str]:
    """
    Convenience function for simple chunking
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    extractor = ChunkExtractor()
    return extractor.chunk_text_simple(text, chunk_size, chunk_overlap)


def chunk_text_toc_aware(
    text: str,
    filename: str
) -> Tuple[List[str], Optional[List[Dict]]]:
    """
    Convenience function for TOC-aware chunking
    
    Args:
        text: Document text content
        filename: Original filename (for format detection)
        
    Returns:
        Tuple of (chunks: List[str], toc: Optional[List[Dict]])
    """
    extractor = ChunkExtractor()
    return extractor.chunk_text_toc_aware(text, filename)

