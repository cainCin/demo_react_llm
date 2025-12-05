"""
Table of Contents (TOC) Extraction Utility
Extracts headings and structure from documents to create a navigable table of contents

Follows convention rules:
- snake_case for functions (extract_toc, extract_toc_markdown, etc.)
- Type hints for all function parameters and returns
- Docstrings for all public methods
- Data classes are in database/models.py (TOCItem imported from there)
"""
import re
from typing import List, Dict, Optional, Tuple

# Import TOCItem from database/models.py (following convention: data classes in models.py)
from database.models import TOCItem


def extract_toc_markdown(text: str) -> List[TOCItem]:
    """
    Extract table of contents from Markdown text
    Supports # headings and alternative heading syntax (underlined)
    
    Args:
        text: Markdown document text
        
    Returns:
        List of TOCItem objects representing the document structure
    """
    toc_items = []
    lines = text.split('\n')
    
    for line_num, line in enumerate(lines):
        # Markdown heading: # Heading, ## Subheading, etc.
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            # Calculate position (approximate)
            position = sum(len(l) + 1 for l in lines[:line_num])
            toc_items.append(TOCItem(
                title=title,
                level=level,
                position=position
            ))
        # Alternative markdown heading (underlined)
        elif line_num > 0 and line.strip() and lines[line_num - 1].strip():
            # Check if current line is underline (=== or ---)
            if re.match(r'^[=\-]{3,}$', line.strip()):
                title = lines[line_num - 1].strip()
                level = 1 if line.strip().startswith('=') else 2
                position = sum(len(l) + 1 for l in lines[:line_num - 1])
                # Avoid duplicates
                if not any(item.title == title and item.position == position for item in toc_items):
                    toc_items.append(TOCItem(
                        title=title,
                        level=level,
                        position=position
                    ))
    
    return toc_items


def extract_toc_python(text: str) -> List[TOCItem]:
    """
    Extract table of contents from Python code
    Identifies classes, methods, and functions as TOC items
    
    Args:
        text: Python source code
        
    Returns:
        List of TOCItem objects representing code structure
    """
    toc_items = []
    lines = text.split('\n')
    
    for line_num, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        
        # Calculate position
        position = sum(len(l) + 1 for l in lines[:line_num])
        
        # Check indentation to determine if it's a method (inside class) or function
        indent_level = len(line) - len(line.lstrip())
        is_method = indent_level > 0
        
        # Pattern 1: Class definition (level 1)
        class_match = re.match(r'^class\s+(\w+)(?:\([^)]+\))?\s*:', stripped)
        if class_match:
            class_name = class_match.group(1)
            toc_items.append(TOCItem(
                title=f"class {class_name}",
                level=1,
                position=position
            ))
            continue  # Skip function matching for class definition line
        
        # Pattern 2: Function or method definition
        func_match = re.match(r'^def\s+(\w+)\s*\([^)]*\)\s*:', stripped)
        if func_match:
            func_name = func_match.group(1)
            
            # Determine level based on indentation
            if is_method:
                # Method inside class - level 2
                level = 2
                title = f"def {func_name}()"
            else:
                # Top-level function - level 1
                level = 1
                title = f"def {func_name}()"
            
            toc_items.append(TOCItem(
                title=title,
                level=level,
                position=position
            ))
            continue
        
        # Pattern 3: Async function/method
        async_func_match = re.match(r'^async\s+def\s+(\w+)\s*\([^)]*\)\s*:', stripped)
        if async_func_match:
            func_name = async_func_match.group(1)
            
            if is_method:
                level = 2
                title = f"async def {func_name}()"
            else:
                level = 1
                title = f"async def {func_name}()"
            
            toc_items.append(TOCItem(
                title=title,
                level=level,
                position=position
            ))
    
    return toc_items


def extract_toc_paragraphs(text: str) -> List[TOCItem]:
    """
    Extract table of contents from plain text based on paragraphs
    Identifies paragraph breaks and uses first sentences as headings
    
    Args:
        text: Plain text document
        
    Returns:
        List of TOCItem objects based on paragraph structure
    """
    toc_items = []
    
    # Split into paragraphs (double newline or significant spacing)
    paragraphs = re.split(r'\n\s*\n+', text)
    
    cumulative_pos = 0
    for para_idx, paragraph in enumerate(paragraphs):
        para = paragraph.strip()
        if not para or len(para) < 20:  # Skip very short paragraphs
            cumulative_pos += len(paragraph) + 2  # +2 for newlines
            continue
        
        # Extract first sentence or first line as heading
        first_line = para.split('\n')[0].strip()
        
        # Try to extract first sentence (up to 100 chars or until period)
        if len(first_line) > 100:
            # Find sentence boundary
            sentence_end = re.search(r'[.!?]\s+', first_line[:100])
            if sentence_end:
                title = first_line[:sentence_end.end()].strip()
            else:
                title = first_line[:100].strip() + "..."
        else:
            title = first_line
        
        # Clean up title (remove extra whitespace, limit length)
        title = re.sub(r'\s+', ' ', title).strip()
        if len(title) > 150:
            title = title[:147] + "..."
        
        if title:
            toc_items.append(TOCItem(
                title=title,
                level=1,
                position=cumulative_pos
            ))
        
        cumulative_pos += len(paragraph) + 2  # +2 for newlines
    
    return toc_items


def extract_toc_html(text: str) -> List[TOCItem]:
    """
    Extract table of contents from HTML
    Identifies heading tags (h1-h6) and uses their content as TOC items
    
    Args:
        text: HTML document text
        
    Returns:
        List of TOCItem objects representing HTML structure
    """
    toc_items = []
    
    # Pattern to match HTML heading tags: <h1>...</h1>, <h2>...</h2>, etc.
    # Also handles self-closing or malformed tags
    heading_pattern = re.compile(
        r'<h([1-6])[^>]*>(.*?)</h[1-6]>',
        re.IGNORECASE | re.DOTALL
    )
    
    for match in heading_pattern.finditer(text):
        level = int(match.group(1))
        content = match.group(2)
        
        # Extract text content, removing nested HTML tags
        text_content = re.sub(r'<[^>]+>', '', content).strip()
        
        # Decode HTML entities (basic)
        text_content = text_content.replace('&nbsp;', ' ')
        text_content = text_content.replace('&amp;', '&')
        text_content = text_content.replace('&lt;', '<')
        text_content = text_content.replace('&gt;', '>')
        text_content = text_content.replace('&quot;', '"')
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        if text_content:
            toc_items.append(TOCItem(
                title=text_content,
                level=level,
                position=match.start()
            ))
    
    # Also check for alternative heading patterns (id attributes, etc.)
    # Pattern for headings with IDs that might be used as anchors
    id_heading_pattern = re.compile(
        r'<h([1-6])[^>]*id=["\']([^"\']+)["\'][^>]*>(.*?)</h[1-6]>',
        re.IGNORECASE | re.DOTALL
    )
    
    for match in id_heading_pattern.finditer(text):
        level = int(match.group(1))
        heading_id = match.group(2)
        content = match.group(3)
        
        # Extract text content
        text_content = re.sub(r'<[^>]+>', '', content).strip()
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        if text_content:
            # Check if we already have this heading (avoid duplicates)
            position = match.start()
            if not any(item.position == position for item in toc_items):
                toc_items.append(TOCItem(
                    title=text_content,
                    level=level,
                    position=position
                ))
    
    return toc_items


def extract_toc_text(text: str) -> List[TOCItem]:
    """
    Extract table of contents from plain text
    Looks for lines that appear to be headings (all caps, numbered sections, etc.)
    
    Args:
        text: Plain text document
        
    Returns:
        List of TOCItem objects
    """
    toc_items = []
    lines = text.split('\n')
    
    for line_num, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        
        # Pattern 1: All caps line (likely heading)
        if stripped.isupper() and len(stripped) > 3 and len(stripped) < 100:
            position = sum(len(l) + 1 for l in lines[:line_num])
            toc_items.append(TOCItem(
                title=stripped,
                level=1,
                position=position
            ))
        # Pattern 2: Numbered sections (1., 1.1, 1.1.1, etc.)
        elif re.match(r'^\d+(\.\d+)*\.?\s+[A-Z]', stripped):
            level = stripped.count('.') + 1
            title = re.sub(r'^\d+(\.\d+)*\.?\s+', '', stripped)
            position = sum(len(l) + 1 for l in lines[:line_num])
            toc_items.append(TOCItem(
                title=title,
                level=min(level, 3),  # Cap at level 3
                position=position
            ))
        # Pattern 3: Lines ending with colon (common in structured text)
        elif stripped.endswith(':') and len(stripped) < 80 and line_num < len(lines) - 1:
            # Check if next line is not empty (likely a section header)
            if line_num + 1 < len(lines) and lines[line_num + 1].strip():
                position = sum(len(l) + 1 for l in lines[:line_num])
                toc_items.append(TOCItem(
                    title=stripped.rstrip(':'),
                    level=2,
                    position=position
                ))
    
    return toc_items


def build_toc_hierarchy(flat_items: List[TOCItem]) -> List[TOCItem]:
    """
    Build hierarchical structure from flat list of TOC items
    Groups items by their level to create a tree structure
    
    Args:
        flat_items: Flat list of TOC items sorted by position
        
    Returns:
        Hierarchical list of TOC items with children
    """
    if not flat_items:
        return []
    
    # Sort by position
    sorted_items = sorted(flat_items, key=lambda x: x.position)
    
    # Build hierarchy
    root_items = []
    stack = []  # Stack of (item, level) tuples
    
    for item in sorted_items:
        # Pop items from stack until we find the parent
        while stack and stack[-1][1] >= item.level:
            stack.pop()
        
        if not stack:
            # Root level item
            root_items.append(item)
        else:
            # Add as child of top stack item
            parent = stack[-1][0]
            parent.children.append(item)
        
        # Push current item to stack
        stack.append((item, item.level))
    
    return root_items


def map_toc_to_chunks(
    toc_items: List[TOCItem],
    chunks: List[str],
    chunk_positions: Optional[List[int]] = None
) -> List[TOCItem]:
    """
    Map TOC items to chunk indices
    Determines which chunks correspond to each TOC section
    
    Args:
        toc_items: List of TOC items (hierarchical)
        chunks: List of chunk texts
        chunk_positions: Optional list of character positions for each chunk start
        
    Returns:
        TOC items with chunk_start and chunk_end populated
    """
    if not toc_items or not chunks:
        return toc_items
    
    # If chunk_positions not provided, estimate based on cumulative length
    if chunk_positions is None:
        chunk_positions = []
        cumulative = 0
        for chunk in chunks:
            chunk_positions.append(cumulative)
            cumulative += len(chunk) + 1  # +1 for newline
    
    # Flatten TOC items for processing
    def flatten_items(items: List[TOCItem]) -> List[TOCItem]:
        result = []
        for item in items:
            result.append(item)
            result.extend(flatten_items(item.children))
        return result
    
    flat_toc = flatten_items(toc_items)
    
    # Map each TOC item to chunks
    for item in flat_toc:
        # Find chunk that contains this position
        chunk_start_idx = None
        
        # Find the chunk that contains or is closest before this position
        for i in range(len(chunk_positions)):
            if chunk_positions[i] <= item.position:
                chunk_start_idx = i
            else:
                break
        
        # If position is before first chunk, use first chunk
        if chunk_start_idx is None:
            chunk_start_idx = 0
        
        # Find end chunk (next TOC item position or end of document)
        chunk_end_idx = None
        
        # Find next TOC item at same or higher level
        next_item_pos = None
        for other_item in flat_toc:
            if other_item.position > item.position and other_item.level <= item.level:
                next_item_pos = other_item.position
                break
        
        # Find chunk containing next position
        if next_item_pos is not None:
            for i in range(chunk_start_idx, len(chunk_positions)):
                if chunk_positions[i] >= next_item_pos:
                    chunk_end_idx = max(i - 1, chunk_start_idx)  # Ensure end >= start
                    break
            if chunk_end_idx is None:
                chunk_end_idx = len(chunks) - 1
        else:
            chunk_end_idx = len(chunks) - 1
        
        # Ensure end >= start
        if chunk_end_idx < chunk_start_idx:
            chunk_end_idx = chunk_start_idx
        
        item.chunk_start = chunk_start_idx
        item.chunk_end = chunk_end_idx
    
    return toc_items


def detect_toc_sections(text: str) -> List[Tuple[int, int]]:
    """
    Detect existing TOC sections in the document
    Returns list of (start_position, end_position) tuples for TOC sections
    
    Args:
        text: Document text content
        
    Returns:
        List of (start_pos, end_pos) tuples representing TOC section boundaries
    """
    toc_sections = []
    lines = text.split('\n')
    
    # Common TOC heading patterns (case-insensitive)
    toc_heading_patterns = [
        r'^#+\s*(table\s+of\s+contents|contents|toc|index|overview)\s*$',
        r'^#+\s*(table\s+of\s+contents|contents|toc|index|overview)\s*:?\s*$',
        r'^\s*(table\s+of\s+contents|contents|toc|index|overview)\s*$',
        r'^\s*(table\s+of\s+contents|contents|toc|index|overview)\s*:?\s*$',
    ]
    
    # Common TOC indicators
    toc_indicators = [
        'table of contents',
        'contents',
        'toc',
        'index',
        'overview'
    ]
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        line_lower = line.lower()
        
        # Check if this line matches a TOC heading pattern
        is_toc_heading = False
        for pattern in toc_heading_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                is_toc_heading = True
                break
        
        # Also check if line contains TOC indicators (as standalone or in heading)
        if not is_toc_heading:
            for indicator in toc_indicators:
                # Check if indicator appears as a heading (all caps, or with # prefix, or standalone)
                if (indicator in line_lower and 
                    (line_lower.startswith('#') or 
                     line_lower == indicator or 
                     line_lower.startswith(indicator + ':') or
                     line_lower.startswith(indicator + ' ') or
                     line_lower == indicator.upper())):
                    is_toc_heading = True
                    break
        
        if is_toc_heading:
            # Found a TOC heading - find where the TOC section ends
            toc_start = sum(len(l) + 1 for l in lines[:i])
            toc_end = toc_start
            
            # Look ahead to find the end of TOC section
            # TOC typically ends when we hit:
            # 1. A major heading (same or higher level) that's not a TOC entry
            # 2. A blank line followed by substantial content
            # 3. End of document
            
            j = i + 1
            toc_content_lines = 0
            max_toc_lines = 200  # TOC shouldn't be more than 200 lines
            consecutive_content_lines = 0
            consecutive_blank_lines = 0
            
            while j < len(lines) and toc_content_lines < max_toc_lines:
                next_line = lines[j].strip()
                
                # Check if we hit a major heading (likely end of TOC)
                heading_match = re.match(r'^(#{1,6})\s+(.+)$', next_line)
                if heading_match:
                    heading_level = len(heading_match.group(1))
                    heading_text = heading_match.group(2).strip()
                    # If it's a substantial heading (not just a TOC entry), end TOC section
                    if len(heading_text) > 10 and heading_level <= 3:
                        # Check if next few lines have substantial content (not just TOC entries)
                        has_content = False
                        for k in range(j + 1, min(j + 3, len(lines))):
                            check_line = lines[k].strip()
                            if check_line and len(check_line) > 50:
                                # Make sure it's not a TOC entry
                                if not (re.match(r'^\d+[\.\)]\s+', check_line) or
                                        re.match(r'^[-*+]\s+', check_line) or
                                        ('[' in check_line and ']' in check_line)):
                                    has_content = True
                                    break
                        if has_content:
                            break
                
                # Check if we hit blank lines followed by substantial content
                if not next_line:
                    consecutive_blank_lines += 1
                    if consecutive_blank_lines >= 2 and j + 1 < len(lines):
                        following_line = lines[j + 1].strip()
                        if following_line and len(following_line) > 50:
                            # Check if it's not a TOC entry (numbered, list item, etc.)
                            if not (re.match(r'^\d+[\.\)]\s+', following_line) or
                                    re.match(r'^[-*+]\s+', following_line) or
                                    ('[' in following_line and ']' in following_line)):
                                # Likely end of TOC, start of content
                                break
                else:
                    consecutive_blank_lines = 0
                
                # Count TOC-like lines (short lines, links, numbered items)
                if next_line:
                    # TOC entries are typically short lines with links or numbers
                    is_toc_entry = (
                        (len(next_line) < 100 and 
                         (re.match(r'^\d+[\.\)]\s+', next_line) or  # Numbered
                          '[' in next_line and ']' in next_line or  # Markdown links
                          re.match(r'^[-*+]\s+', next_line))) or  # List items
                        (len(next_line) < 80 and re.match(r'^[A-Z][a-z]+', next_line))  # Short capitalized lines
                    )
                    
                    if is_toc_entry:
                        toc_content_lines += 1
                        consecutive_content_lines = 0
                    elif len(next_line) > 100:
                        # Long line - likely not TOC, end of TOC section
                        consecutive_content_lines += 1
                        if consecutive_content_lines >= 2:
                            break
                    else:
                        consecutive_content_lines += 1
                        if consecutive_content_lines >= 3:
                            # Multiple non-TOC lines, end of TOC section
                            break
                else:
                    consecutive_content_lines = 0
                
                j += 1
            
            # Calculate end position
            toc_end = sum(len(l) + 1 for l in lines[:j])
            
            # Only add if TOC section is reasonable size (not entire document)
            # and has some content (at least 20 chars)
            toc_size = toc_end - toc_start
            if toc_size > 20 and toc_size < len(text) * 0.3:  # TOC shouldn't be more than 30% of document
                toc_sections.append((toc_start, toc_end))
            
            i = j
        else:
            i += 1
    
    return toc_sections


def filter_toc_duplicates(flat_items: List[TOCItem], text: str) -> List[TOCItem]:
    """
    Filter out TOC items that fall within existing TOC sections
    
    Args:
        flat_items: List of extracted TOC items
        text: Document text content
        
    Returns:
        Filtered list of TOC items with duplicates removed
    """
    if not flat_items:
        return flat_items
    
    # Detect existing TOC sections
    toc_sections = detect_toc_sections(text)
    
    if not toc_sections:
        # No TOC sections detected, return all items
        return flat_items
    
    # Filter out items that fall within TOC sections
    filtered_items = []
    for item in flat_items:
        # Check if this item's position is within any TOC section
        is_in_toc_section = False
        for toc_start, toc_end in toc_sections:
            if toc_start <= item.position < toc_end:
                is_in_toc_section = True
                break
        
        if not is_in_toc_section:
            filtered_items.append(item)
    
    return filtered_items


def extract_toc(text: str, filename: str) -> List[Dict]:
    """
    Main function to extract TOC from a document
    Automatically detects format and extracts appropriate structure
    
    Supports:
    - Markdown (.md, .markdown)
    - Python (.py) - extracts classes, methods, functions
    - HTML (.html, .htm) - extracts heading tags (h1-h6)
    - Plain text (.txt) - extracts paragraphs or structured headings
    
    Args:
        text: Document text content
        filename: Original filename (for format detection)
        
    Returns:
        List of TOC items as dictionaries (hierarchical structure)
    """
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Extract based on file type
    flat_items = []
    
    if file_ext in ['md', 'markdown']:
        # Markdown files
        flat_items = extract_toc_markdown(text)
    
    elif file_ext == 'py':
        # Python files - extract code structure
        flat_items = extract_toc_python(text)
    
    elif file_ext in ['html', 'htm']:
        # HTML files - extract heading tags
        flat_items = extract_toc_html(text)
    
    elif file_ext == 'txt':
        # Plain text files - try paragraph-based extraction
        flat_items = extract_toc_paragraphs(text)
        # Fallback to structured text extraction if paragraph extraction yields few results
        if len(flat_items) < 3:
            text_items = extract_toc_text(text)
            if len(text_items) > len(flat_items):
                flat_items = text_items
    
    else:
        # Unknown file type - try multiple strategies
        # Try markdown first
        flat_items = extract_toc_markdown(text)
        
        # If few markdown headings, try other strategies
        if len(flat_items) < 3:
            # Try Python (in case it's Python code without .py extension)
            python_items = extract_toc_python(text)
            if len(python_items) > len(flat_items):
                flat_items = python_items
        
        if len(flat_items) < 3:
            # Try HTML (in case it's HTML without .html extension)
            html_items = extract_toc_html(text)
            if len(html_items) > len(flat_items):
                flat_items = html_items
        
        if len(flat_items) < 3:
            # Try paragraph-based extraction
            para_items = extract_toc_paragraphs(text)
            if len(para_items) > len(flat_items):
                flat_items = para_items
        
        if len(flat_items) < 3:
            # Final fallback to structured text extraction
            text_items = extract_toc_text(text)
            if len(text_items) > len(flat_items):
                flat_items = text_items
    
    # Filter out TOC items that are within existing TOC sections
    flat_items = filter_toc_duplicates(flat_items, text)
    
    # Build hierarchy
    hierarchical_items = build_toc_hierarchy(flat_items)
    
    # Convert to dictionaries
    return [item.to_dict() for item in hierarchical_items]

