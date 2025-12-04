import React from 'react'
import './ChunkViewer.css'

const ChunkViewer = ({ chunk, onClose }) => {
  if (!chunk) {
    return (
      <div className="chunk-viewer-container empty">
        <div className="chunk-viewer-placeholder">
          <div className="placeholder-icon">📄</div>
          <div className="placeholder-text">
            <h3>Chunk Viewer</h3>
            <p>Select a chunk from the chat to view its full content here</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="chunk-viewer-container">
      <div className="chunk-viewer-header">
        <div className="chunk-viewer-title">
          <span className="viewer-icon">📄</span>
          <span>Chunk Content</span>
        </div>
        <button
          type="button"
          className="chunk-viewer-close"
          onClick={onClose}
          title="Close viewer"
        >
          ×
        </button>
      </div>
      <div className="chunk-viewer-content">
        <div className="chunk-viewer-metadata">
          {chunk.document_id && (
            <div className="metadata-item">
              <span className="metadata-label">Document ID:</span>
              <span className="metadata-value">{chunk.document_id}</span>
            </div>
          )}
          {chunk.chunk_index !== undefined && (
            <div className="metadata-item">
              <span className="metadata-label">Chunk Index:</span>
              <span className="metadata-value">{chunk.chunk_index}</span>
            </div>
          )}
          {chunk.score !== undefined && (
            <div className="metadata-item">
              <span className="metadata-label">Similarity Score:</span>
              <span className="metadata-value">{(chunk.score * 100).toFixed(2)}%</span>
            </div>
          )}
          {chunk.distance !== undefined && (
            <div className="metadata-item">
              <span className="metadata-label">Distance:</span>
              <span className="metadata-value">{chunk.distance.toFixed(4)}</span>
            </div>
          )}
        </div>
        <div className="chunk-viewer-text">
          {!chunk.text || 
           chunk.text === '[Chunk text not available]' || 
           chunk.text === '[Chunk text requires database access]' ? (
            <div className="chunk-loading-placeholder">
              <p>Loading content from database...</p>
              <p className="loading-hint">If content doesn't load, the chunk may have been deleted from the database.</p>
            </div>
          ) : (
            chunk.text
          )}
        </div>
      </div>
    </div>
  )
}

export default ChunkViewer

