import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './TableOfContents.css'

const API_URL = import.meta.env.VITE_API_URL || ''

const TableOfContents = ({ 
  documentIds = [], 
  documents = [], 
  onChunkSelect, 
  selectedChunkIds = new Set(),
  onToggleChunk,
  chunkScores = {},
  onViewChunk,
  onResend,
  isLoading = false
}) => {
  const [tocs, setTocs] = useState({}) // documentId -> toc data
  const [loading, setLoading] = useState({}) // documentId -> loading state
  const [errors, setErrors] = useState({}) // documentId -> error message
  const [expandedFiles, setExpandedFiles] = useState(new Set()) // Set of expanded document IDs
  const [expandedItems, setExpandedItems] = useState({}) // documentId -> Set of expanded TOC item IDs
  const [chunkData, setChunkData] = useState({}) // (docId, chunkIndex) -> chunk data with score

  // Load TOC for all documents
  useEffect(() => {
    if (documentIds && documentIds.length > 0) {
      documentIds.forEach(docId => {
        if (!tocs[docId] && !loading[docId] && !errors[docId]) {
          loadTOC(docId)
        }
      })
    } else {
      setTocs({})
    }
  }, [documentIds])
  
  // Update chunk data when chunks are loaded
  useEffect(() => {
    // This effect will trigger re-renders when chunkData changes
  }, [chunkData])

  // Auto-expand TOC items that contain selected chunks
  useEffect(() => {
    if (selectedChunkIds.size === 0 || Object.keys(tocs).length === 0) {
      return
    }

    // Find all TOC items that contain selected chunks and expand them
    const itemsToExpand = new Map() // docId -> Set of item IDs to expand
    const filesToExpand = new Set() // docIds to expand

    // Parse selected chunk IDs to get document IDs and chunk indices
    const selectedChunksByDoc = new Map() // docId -> Set of chunk indices
    selectedChunkIds.forEach(tocChunkId => {
      const parts = tocChunkId.split('-chunk-')
      if (parts.length === 2) {
        const docId = parts[0]
        const chunkIdx = parseInt(parts[1])
        if (!isNaN(chunkIdx)) {
          if (!selectedChunksByDoc.has(docId)) {
            selectedChunksByDoc.set(docId, new Set())
          }
          selectedChunksByDoc.get(docId).add(chunkIdx)
        }
      }
    })

    // Helper function to recursively find items containing chunks
    const findItemsWithChunks = (docId, items, parentId = '', level = 0) => {
      const foundItems = []
      items.forEach((item, index) => {
        const itemId = `${parentId}-${index}`
        const hasChunks = item.chunk_start !== null && item.chunk_start !== undefined
        const selectedChunkIndices = selectedChunksByDoc.get(docId) || new Set()
        
        if (hasChunks) {
          const chunkStart = item.chunk_start
          const chunkEnd = item.chunk_end !== null && item.chunk_end !== undefined ? item.chunk_end : item.chunk_start
          
          // Check if any selected chunk is in this item's range
          const hasSelectedChunk = Array.from(selectedChunkIndices).some(idx => 
            idx >= chunkStart && idx <= chunkEnd
          )
          
          if (hasSelectedChunk) {
            foundItems.push(itemId)
            // Also expand all parent items
            if (parentId) {
              foundItems.push(parentId)
            }
          }
        }
        
        // Recursively check children
        if (item.children && item.children.length > 0) {
          const childItems = findItemsWithChunks(docId, item.children, itemId, level + 1)
          if (childItems.length > 0) {
            foundItems.push(itemId) // Expand parent if child has selected chunks
            foundItems.push(...childItems)
          }
        }
      })
      return foundItems
    }

    // For each document with selected chunks, find and expand relevant items
    selectedChunksByDoc.forEach((chunkIndices, docId) => {
      if (tocs[docId] && tocs[docId].toc) {
        filesToExpand.add(docId)
        const itemsToExpandForDoc = findItemsWithChunks(docId, tocs[docId].toc)
        if (itemsToExpandForDoc.length > 0) {
          itemsToExpand.set(docId, new Set(itemsToExpandForDoc))
        }
      }
    })

    // Update expanded files
    if (filesToExpand.size > 0) {
      setExpandedFiles(prev => {
        const next = new Set(prev)
        filesToExpand.forEach(docId => next.add(docId))
        return next
      })
    }

    // Update expanded items
    if (itemsToExpand.size > 0) {
      setExpandedItems(prev => {
        const next = { ...prev }
        itemsToExpand.forEach((itemIds, docId) => {
          if (!next[docId]) {
            next[docId] = new Set()
          }
          const itemSet = new Set(next[docId])
          itemIds.forEach(itemId => itemSet.add(itemId))
          next[docId] = itemSet
        })
        return next
      })
    }
  }, [selectedChunkIds, tocs])

  const loadTOC = async (docId) => {
    setLoading(prev => ({ ...prev, [docId]: true }))
    setErrors(prev => {
      const next = { ...prev }
      delete next[docId]
      return next
    })
    
    try {
      const url = API_URL ? `${API_URL}/api/documents/${docId}/toc` : `/api/documents/${docId}/toc`
      const response = await axios.get(url, { timeout: 5000 })
      
      if (response.data && response.data.data && response.data.data.toc) {
        setTocs(prev => ({
          ...prev,
          [docId]: {
            toc: response.data.data.toc,
            filename: response.data.data.filename || docId.substring(0, 8) + '...'
          }
        }))
        // Auto-expand first level items for this document
        const firstLevelIds = response.data.data.toc.map((item, idx) => `toc-${docId}-${idx}`)
        setExpandedItems(prev => ({
          ...prev,
          [docId]: new Set(firstLevelIds)
        }))
      } else {
        setTocs(prev => ({
          ...prev,
          [docId]: {
            toc: [],
            filename: response.data?.data?.filename || docId.substring(0, 8) + '...'
          }
        }))
      }
    } catch (err) {
      console.error(`Error loading TOC for document ${docId}:`, err)
      setErrors(prev => ({
        ...prev,
        [docId]: 'Failed to load table of contents'
      }))
      // Set empty TOC on error
      setTocs(prev => ({
        ...prev,
        [docId]: {
          toc: [],
          filename: documents.find(d => d.id === docId)?.filename || docId.substring(0, 8) + '...'
        }
      }))
    } finally {
      setLoading(prev => {
        const next = { ...prev }
        delete next[docId]
        return next
      })
    }
  }

  const toggleFileExpand = (docId) => {
    setExpandedFiles(prev => {
      const next = new Set(prev)
      if (next.has(docId)) {
        next.delete(docId)
      } else {
        next.add(docId)
      }
      return next
    })
  }

  const toggleTOCItemExpand = (docId, itemId) => {
    setExpandedItems(prev => {
      const next = { ...prev }
      if (!next[docId]) {
        next[docId] = new Set()
      }
      const itemSet = new Set(next[docId])
      if (itemSet.has(itemId)) {
        itemSet.delete(itemId)
      } else {
        itemSet.add(itemId)
      }
      next[docId] = itemSet
      return next
    })
  }

  const loadChunksForItem = async (docId, item) => {
    if (item.chunk_start === null || item.chunk_start === undefined) return null
    
    const chunkStart = item.chunk_start
    const chunkEnd = item.chunk_end !== null && item.chunk_end !== undefined ? item.chunk_end : item.chunk_start
    
    // Check if we already have this data
    const key = `${docId}-${chunkStart}-${chunkEnd}`
    if (chunkData[key]) {
      return chunkData[key]
    }
    
    try {
      const url = API_URL ? `${API_URL}/api/documents/${docId}/chunks` : `/api/documents/${docId}/chunks`
      const response = await axios.get(url, {
        params: {
          start: chunkStart,
          end: chunkEnd
        },
        timeout: 5000
      })
      
      if (response.data && response.data.chunks) {
        // Store chunk data
        setChunkData(prev => ({
          ...prev,
          [key]: response.data.chunks
        }))
        return response.data.chunks
      }
    } catch (error) {
      console.error('Error loading chunks for TOC item:', error)
    }
    
    return null
  }

  const handleItemClick = async (docId, item) => {
    if (item.chunk_start !== null && item.chunk_start !== undefined) {
      // Load chunks for this item
      const loadedChunks = await loadChunksForItem(docId, item)
      
      // Notify parent to load chunks for this section
      if (onChunkSelect) {
        onChunkSelect({
          documentId: docId,
          chunkStart: item.chunk_start,
          chunkEnd: item.chunk_end !== null && item.chunk_end !== undefined ? item.chunk_end : item.chunk_start,
          title: item.title
        })
      }
      
      // Display first chunk in viewer if available
      if (loadedChunks && loadedChunks.length > 0 && onViewChunk) {
        const firstChunk = loadedChunks[0]
        onViewChunk({
          ...firstChunk,
          document_id: docId
        })
      }
    }
  }
  
  const handleChunkToggle = (e, docId, chunkIndex) => {
    e.stopPropagation()
    const chunkId = `${docId}-chunk-${chunkIndex}`
    if (onToggleChunk) {
      onToggleChunk(chunkId)
    }
  }
  
  const getChunkScore = (docId, chunkIndex) => {
    const chunkId = `${docId}-chunk-${chunkIndex}`
    return chunkScores[chunkId] || null
  }
  
  const isChunkSelected = (docId, chunkIndex) => {
    const chunkId = `${docId}-chunk-${chunkIndex}`
    return selectedChunkIds.has(chunkId)
  }

  const renderTOCItem = (docId, item, index, level = 0, parentId = '') => {
    const itemId = `${parentId}-${index}`
    const hasChildren = item.children && item.children.length > 0
    const itemExpanded = expandedItems[docId]?.has(itemId) || false
    const hasChunks = item.chunk_start !== null && item.chunk_start !== undefined
    const indentLevel = level * 20 // 20px per level
    
    // Get chunk indices for this item
    const chunkStart = item.chunk_start
    const chunkEnd = item.chunk_end !== null && item.chunk_end !== undefined ? item.chunk_end : item.chunk_start
    const chunkIndices = []
    for (let i = chunkStart; i <= chunkEnd; i++) {
      chunkIndices.push(i)
    }
    
    // Check if any chunks in this item are selected
    const hasSelectedChunks = hasChunks && chunkIndices.some(idx => isChunkSelected(docId, idx))
    const allChunksSelected = hasChunks && chunkIndices.length > 0 && chunkIndices.every(idx => isChunkSelected(docId, idx))

    return (
      <div key={itemId} className="toc-item">
        <div
          className={`toc-item-header ${hasChunks ? 'clickable' : ''} ${hasSelectedChunks ? 'has-selected' : ''}`}
          style={{ paddingLeft: `${indentLevel}px` }}
          onClick={() => hasChunks && handleItemClick(docId, item)}
        >
          {hasChunks && (
            <input
              type="checkbox"
              checked={allChunksSelected}
              onChange={(e) => {
                e.stopPropagation()
                // Toggle all chunks in this item
                chunkIndices.forEach(idx => {
                  if (onToggleChunk) {
                    const chunkId = `${docId}-chunk-${idx}`
                    if (allChunksSelected) {
                      // Deselect all
                      if (selectedChunkIds.has(chunkId)) {
                        onToggleChunk(chunkId)
                      }
                    } else {
                      // Select all
                      if (!selectedChunkIds.has(chunkId)) {
                        onToggleChunk(chunkId)
                      }
                    }
                  }
                })
              }}
              onClick={(e) => e.stopPropagation()}
              className="toc-chunk-checkbox"
            />
          )}
          {hasChildren && (
            <button
              className="toc-expand-btn"
              onClick={(e) => {
                e.stopPropagation()
                toggleTOCItemExpand(docId, itemId)
              }}
              aria-label={itemExpanded ? 'Collapse' : 'Expand'}
            >
              {itemExpanded ? '▼' : '▶'}
            </button>
          )}
          {!hasChildren && !hasChunks && <span className="toc-spacer" />}
          <span className="toc-title" title={item.title}>
            {item.title}
          </span>
          {hasChunks && (
            <span className="toc-chunk-info">
              {chunkIndices.map((chunkIdx, idx) => {
                const isSelected = isChunkSelected(docId, chunkIdx)
                const score = getChunkScore(docId, chunkIdx)
                return (
                  <span key={chunkIdx} className={`toc-chunk-badge ${isSelected ? 'selected' : ''}`}>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => handleChunkToggle(e, docId, chunkIdx)}
                      onClick={(e) => e.stopPropagation()}
                      className="toc-chunk-checkbox-small"
                    />
                    <span className="toc-chunk-number">#{chunkIdx}</span>
                    {isSelected && score !== null && (
                      <span className="toc-chunk-score">{(score * 100).toFixed(1)}%</span>
                    )}
                  </span>
                )
              })}
            </span>
          )}
        </div>
        {hasChildren && itemExpanded && (
          <div className="toc-children">
            {item.children.map((child, childIndex) =>
              renderTOCItem(docId, child, childIndex, level + 1, itemId)
            )}
          </div>
        )}
      </div>
    )
  }

  const getDocumentFilename = (docId) => {
    const doc = documents.find(d => d.id === docId)
    if (doc && doc.filename) {
      return doc.filename
    }
    if (tocs[docId] && tocs[docId].filename) {
      return tocs[docId].filename
    }
    return docId.substring(0, 8) + '...'
  }

  if (!documentIds || documentIds.length === 0) {
    return (
      <div className="table-of-contents">
        <div className="toc-header">
          <h3>Table of Contents</h3>
        </div>
        <div className="toc-placeholder">
          <p>No documents selected</p>
          <p className="toc-hint">Reference chunks will appear here when available</p>
        </div>
      </div>
    )
  }

  const handleResend = () => {
    if (onResend && selectedChunkIds.size > 0) {
      const chunkIds = Array.from(selectedChunkIds)
      onResend(chunkIds)
    }
  }

  return (
    <div className="table-of-contents">
      <div className="toc-header">
        <h3>Reference Files ({documentIds.length})</h3>
        {selectedChunkIds.size > 0 && (
          <div className="toc-header-actions">
            <button
              type="button"
              className="toc-resend-button"
              onClick={handleResend}
              disabled={isLoading || selectedChunkIds.size === 0}
              title="Re-send query with selected chunks"
            >
              🔄 Re-send ({selectedChunkIds.size})
            </button>
          </div>
        )}
      </div>
      <div className="toc-content">
        {documentIds.map((docId) => {
          const isFileExpanded = expandedFiles.has(docId)
          const docToc = tocs[docId]
          const isLoading = loading[docId]
          const error = errors[docId]
          const filename = getDocumentFilename(docId)

          return (
            <div key={docId} className="toc-file-section">
              <div
                className="toc-file-header"
                onClick={() => toggleFileExpand(docId)}
              >
                <button
                  className="toc-file-expand-btn"
                  aria-label={isFileExpanded ? 'Collapse file' : 'Expand file'}
                >
                  {isFileExpanded ? '▼' : '▶'}
                </button>
                <span className="toc-file-name" title={filename}>
                  📄 {filename}
                </span>
                {isLoading && <span className="toc-loading-indicator">⏳</span>}
              </div>
              
              {isFileExpanded && (
                <div className="toc-file-content">
                  {isLoading && (
                    <div className="toc-loading">
                      <p>Loading table of contents...</p>
                    </div>
                  )}
                  
                  {error && (
                    <div className="toc-error">
                      <p>{error}</p>
                    </div>
                  )}
                  
                  {!isLoading && !error && docToc && (
                    <>
                      {docToc.toc && docToc.toc.length > 0 ? (
                        <div className="toc-items">
                          {docToc.toc.map((item, index) =>
                            renderTOCItem(docId, item, index)
                          )}
                        </div>
                      ) : (
                        <div className="toc-placeholder">
                          <p>No table of contents available</p>
                          <p className="toc-hint">This document doesn't have a structured table of contents</p>
                        </div>
                      )}
                    </>
                  )}
                  
                  {!isLoading && !error && !docToc && (
                    <div className="toc-placeholder">
                      <p>Loading...</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default TableOfContents
