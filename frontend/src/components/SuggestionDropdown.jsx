import React, { useEffect, useRef } from 'react'
import './SuggestionDropdown.css'

/**
 * Generic Suggestion Dropdown Component
 * Works with any suggestion type based on configuration
 */
const SuggestionDropdown = ({ 
  suggestions, 
  selectedIndex, 
  onSelect, 
  onClose,
  position,
  displayInfo
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

  if (!displayInfo) {
    console.warn('SuggestionDropdown: No displayInfo provided')
    return null
  }
  
  if (!suggestions || suggestions.length === 0) {
    // Show empty state instead of hiding
    const style = position ? {
      top: `${position.top}px`,
      left: `${position.left}px`,
      width: `${position.width}px`
    } : {}
    
    return (
      <div className="suggestion-dropdown" style={style} ref={listRef}>
        <div className="suggestion-header">
          <span className="suggestion-header-icon">{displayInfo.icon}</span>
          <span className="suggestion-header-title">{displayInfo.title}</span>
          <span className="suggestion-header-count">0</span>
        </div>
        <div className="suggestion-list">
          <div className="suggestion-item" style={{ cursor: 'default', opacity: 0.6, padding: '15px' }}>
            <div className="suggestion-item-content" style={{ textAlign: 'center', width: '100%' }}>
              <div className="suggestion-item-title" style={{ marginBottom: '5px' }}>No documents found</div>
              <div className="suggestion-item-meta" style={{ fontSize: '11px', opacity: 0.7 }}>
                Upload a document to see suggestions
              </div>
            </div>
          </div>
        </div>
        <div className="suggestion-footer">
          <span className="suggestion-hint">Esc to close</span>
        </div>
      </div>
    )
  }

  const style = position ? {
    top: `${position.top}px`,
    left: `${position.left}px`,
    width: `${position.width}px`
  } : {}

  return (
    <div className="suggestion-dropdown" style={style} ref={listRef}>
      <div className="suggestion-header">
        <span className="suggestion-header-icon">{displayInfo.icon}</span>
        <span className="suggestion-header-title">{displayInfo.title}</span>
        <span className="suggestion-header-count">{suggestions.length}</span>
      </div>
      <div className="suggestion-list">
        {suggestions.map((item, index) => (
          <div
            key={item.id || index}
            ref={index === selectedIndex ? selectedRef : null}
            className={`suggestion-item ${index === selectedIndex ? 'selected' : ''}`}
            onClick={() => onSelect(item)}
          >
            <span className="suggestion-item-icon">{displayInfo.icon}</span>
            <div className="suggestion-item-content">
              <div className="suggestion-item-title">
                {item.formattedTitle || item.name || item.filename || item.title || 'Unknown'}
              </div>
              {item.metadata && item.metadata.length > 0 && (
                <div className="suggestion-item-meta">
                  {item.metadata.map((meta, metaIndex) => (
                    <span key={metaIndex} className="suggestion-meta-item">
                      {meta.label && `${meta.label}: `}
                      {meta.value}
                      {metaIndex < item.metadata.length - 1 && ' • '}
                    </span>
                  ))}
                </div>
              )}
            </div>
            {index === selectedIndex && (
              <span className="suggestion-indicator">→</span>
            )}
          </div>
        ))}
      </div>
      <div className="suggestion-footer">
        <span className="suggestion-hint">
          ↑↓ to navigate • Enter to select • Esc to close
        </span>
      </div>
    </div>
  )
}

export default SuggestionDropdown

