import React from 'react'
import './ContextChunks.css'

const ContextChunks = ({ chunks, selectedChunks, onToggleChunk, onViewChunk, onResend, messageId, isLoading }) => {
  if (!chunks || chunks.length === 0) {
    return null
  }

  // Ensure consistent string comparison for chunk IDs
  const allSelected = chunks.every(chunk => selectedChunks.has(String(chunk.id)))
  const someSelected = chunks.some(chunk => selectedChunks.has(String(chunk.id)))

  const handleSelectAll = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (allSelected) {
      // Deselect all
      chunks.forEach(chunk => {
        if (selectedChunks.has(String(chunk.id))) {
          onToggleChunk(chunk.id)
        }
      })
    } else {
      // Select all
      chunks.forEach(chunk => {
        if (!selectedChunks.has(String(chunk.id))) {
          onToggleChunk(chunk.id)
        }
      })
    }
  }

  return (
    <div className="context-chunks-container">
      <div className="context-chunks-header">
        <div className="context-chunks-title">
          <span className="context-icon">📄</span>
          <span>Context Chunks ({chunks.length})</span>
        </div>
        <div className="context-chunks-actions">
          <button
            type="button"
            className="select-all-button"
            onClick={handleSelectAll}
            title={allSelected ? "Deselect all" : "Select all"}
          >
            {allSelected ? "☑" : someSelected ? "☐" : "☐"} All
          </button>
          <button
            type="button"
            className="resend-button"
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              const chunkIds = Array.from(selectedChunks)
              console.log('Re-send button clicked:', { messageId, chunkIds, chunkCount: chunkIds.length })
              onResend(messageId, chunkIds)
            }}
            disabled={selectedChunks.size === 0 || isLoading}
            title="Re-send query with selected chunks"
          >
            🔄 Re-send
          </button>
        </div>
      </div>
      <div className="context-chunks-list">
        {chunks.map((chunk, index) => {
          const isSelected = selectedChunks.has(String(chunk.id))
          
          return (
            <div
              key={chunk.id || index}
              className={`context-chunk-item ${isSelected ? 'selected' : ''}`}
            >
              <div className="chunk-checkbox-wrapper">
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={(e) => {
                    e.stopPropagation()
                    onToggleChunk(chunk.id)
                  }}
                  onClick={(e) => e.stopPropagation()}
                  className="chunk-checkbox"
                  id={`chunk-checkbox-${chunk.id || index}`}
                />
                <label 
                  htmlFor={`chunk-checkbox-${chunk.id || index}`}
                  className="chunk-checkbox-label"
                  onClick={(e) => e.stopPropagation()}
                >
                  {/* Label is only for checkbox accessibility, no content */}
                </label>
              </div>
              <div className="chunk-content">
                <div className="chunk-header">
                  <span className="chunk-index">#{index + 1}</span>
                  {chunk.score !== undefined && (
                    <span className="chunk-score">
                      Score: {(chunk.score * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
                <div 
                  className="chunk-text"
                  onClick={(e) => {
                    e.stopPropagation()
                    if (onViewChunk) {
                      onViewChunk(chunk)
                    }
                  }}
                  title="Click to view full content"
                >
                  {!chunk.text || 
                   chunk.text === '[Chunk text not available]' || 
                   chunk.text === '[Chunk text requires database access]' ? (
                    <span className="chunk-text-placeholder">
                      [Click to load content from database]
                    </span>
                  ) : chunk.text.length > 200 ? (
                    `${chunk.text.substring(0, 200)}...`
                  ) : (
                    chunk.text
                  )}
                </div>
                {chunk.document_id && (
                  <div className="chunk-metadata">
                    <span className="chunk-doc-id">Doc: {chunk.document_id.substring(0, 8)}...</span>
                    {chunk.chunk_index !== undefined && (
                      <span className="chunk-index-badge">Chunk {chunk.chunk_index}</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ContextChunks

