import React, { useEffect, useRef } from 'react'
import './DocumentSuggestions.css'

const DocumentSuggestions = ({ 
  suggestions, 
  selectedIndex, 
  onSelect, 
  onClose,
  position 
}) => {
  const listRef = useRef(null)
  const selectedRef = useRef(null)

  // Scroll selected item into view
  useEffect(() => {
    if (selectedRef.current && listRef.current) {
      const listRect = listRef.current.getBoundingClientRect()
      const selectedRect = selectedRef.current.getBoundingClientRect()
      
      if (selectedRect.bottom > listRect.bottom) {
        selectedRef.current.scrollIntoView({ block: 'nearest' })
      } else if (selectedRect.top < listRect.top) {
        selectedRef.current.scrollIntoView({ block: 'nearest' })
      }
    }
  }, [selectedIndex])

  if (!suggestions || suggestions.length === 0) {
    return null
  }

  const style = position ? {
    top: `${position.top}px`,
    left: `${position.left}px`,
    width: `${position.width}px`
  } : {}

  return (
    <div className="document-suggestions" style={style} ref={listRef}>
      <div className="suggestions-header">
        <span className="suggestions-icon">📄</span>
        <span className="suggestions-title">Documents</span>
        <span className="suggestions-count">{suggestions.length}</span>
      </div>
      <div className="suggestions-list">
        {suggestions.map((doc, index) => (
          <div
            key={doc.id}
            ref={index === selectedIndex ? selectedRef : null}
            className={`suggestion-item ${index === selectedIndex ? 'selected' : ''}`}
            onClick={() => onSelect(doc)}
            onMouseEnter={() => {
              // Optional: highlight on hover
            }}
          >
            <span className="suggestion-icon">📄</span>
            <div className="suggestion-content">
              <div className="suggestion-filename">{doc.filename}</div>
              <div className="suggestion-meta">
                {doc.chunk_count} {doc.chunk_count === 1 ? 'chunk' : 'chunks'}
                {doc.created_at && (
                  <span className="suggestion-date">
                    • {new Date(doc.created_at).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>
            {index === selectedIndex && (
              <span className="suggestion-indicator">→</span>
            )}
          </div>
        ))}
      </div>
      <div className="suggestions-footer">
        <span className="suggestions-hint">↑↓ to navigate • Enter to select • Esc to close</span>
      </div>
    </div>
  )
}

export default DocumentSuggestions

