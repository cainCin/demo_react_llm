import React, { useState, useRef, useEffect, useCallback } from 'react'
import axios from 'axios'
import { useTheme } from './contexts/ThemeContext'
import ThemeSwitcher from './components/ThemeSwitcher'
import SuggestionDropdown from './components/SuggestionDropdown'
import ContextChunks from './components/ContextChunks'
import ChunkViewer from './components/ChunkViewer'
import SessionPanel from './components/SessionPanel'
import { detectSuggestionTrigger } from './utils/suggestionConfig'
import { searchSuggestions, getSuggestionDisplayInfo } from './services/suggestionService'
import './App.css'

// Use relative URL to leverage Vite proxy, or full URL if VITE_API_URL is set
const API_URL = import.meta.env.VITE_API_URL || ''

function App() {
  const [messages, setMessages] = useState([
    {
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content: 'Hello! I\'m your AI assistant. How can I help you today?',
      chunks: null
    }
  ])
  const [selectedChunks, setSelectedChunks] = useState(new Map()) // messageId -> Set of chunk IDs
  const [viewingChunk, setViewingChunk] = useState(null) // Currently viewed chunk for display
  const [sessionId, setSessionId] = useState(() => {
    // Try to load session_id from localStorage on mount
    const saved = localStorage.getItem('chatbox_session_id')
    return saved || null
  })
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [backendConnected, setBackendConnected] = useState(null)
  const [healthStatus, setHealthStatus] = useState({
    connected: null,
    ragEnabled: false,
    lastCheck: null,
    error: null
  })
  const [attachedFiles, setAttachedFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(0)
  const [suggestionQuery, setSuggestionQuery] = useState('')
  const [suggestionSymbol, setSuggestionSymbol] = useState(null)
  const [suggestionConfig, setSuggestionConfig] = useState(null)
  const [suggestionDisplayInfo, setSuggestionDisplayInfo] = useState(null)
  const [suggestionPosition, setSuggestionPosition] = useState(null)
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)
  const healthCheckIntervalRef = useRef(null)
  const inputRef = useRef(null)
  const suggestionsTimeoutRef = useRef(null)
  const { currentTheme } = useTheme()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Real-time health check - runs every second
  useEffect(() => {
    const checkBackend = async () => {
      try {
        // Use health endpoint through proxy
        const healthUrl = API_URL ? `${API_URL}/api/health` : '/api/health'
        const response = await axios.get(healthUrl, { timeout: 2000 })
        if (response.data && response.data.status === 'ok') {
          setBackendConnected(true)
          setHealthStatus({
            connected: true,
            ragEnabled: response.data.rag_enabled || false,
            lastCheck: new Date(),
            error: null
          })
        } else {
          setBackendConnected(false)
          setHealthStatus(prev => ({
            ...prev,
            connected: false,
            lastCheck: new Date(),
            error: 'Invalid response'
          }))
        }
      } catch (error) {
        console.warn('Backend connection check failed:', error)
        setBackendConnected(false)
        setHealthStatus(prev => ({
          ...prev,
          connected: false,
          lastCheck: new Date(),
          error: error.code === 'ECONNABORTED' ? 'Timeout' : 
                 error.code === 'ERR_NETWORK' ? 'Network Error' : 
                 'Connection Failed'
        }))
      }
    }

    // Initial check
    checkBackend()

    // Set up interval to check every second
    healthCheckIntervalRef.current = setInterval(checkBackend, 1000)

    // Cleanup interval on unmount
    return () => {
      if (healthCheckIntervalRef.current) {
        clearInterval(healthCheckIntervalRef.current)
      }
    }
  }, [])

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files)
    if (files.length === 0) return

    setIsUploading(true)
    const uploadedFiles = []

    try {
      for (const file of files) {
        // Check file size (10MB limit)
        if (file.size > 10 * 1024 * 1024) {
          alert(`File ${file.name} is too large. Maximum size is 10MB.`)
          continue
        }

        const formData = new FormData()
        formData.append('file', file)

        const uploadUrl = API_URL ? `${API_URL}/api/upload` : '/api/upload'
        const uploadResponse = await axios.post(uploadUrl, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 30000,
        })

        uploadedFiles.push({
          filename: uploadResponse.data.filename,
          content: uploadResponse.data.content,
          size: uploadResponse.data.size,
          content_type: uploadResponse.data.content_type
        })
      }

      setAttachedFiles(prev => [...prev, ...uploadedFiles])
    } catch (error) {
      console.error('Error uploading file:', error)
      alert(`Error uploading file: ${error.response?.data?.detail || error.message}`)
    } finally {
      setIsUploading(false)
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const removeFile = (index) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index))
  }

  // Handle input change and detect suggestion triggers (config-based)
  const handleInputChange = async (e) => {
    const value = e.target.value
    setInput(value)

    // Detect suggestion trigger using configuration
    try {
      const trigger = await detectSuggestionTrigger(value)
      console.log('🔍 Trigger detection result:', trigger)
      
      if (trigger) {
        console.log(`✅ Trigger detected: ${trigger.symbol} with query: "${trigger.query}"`)
      setSuggestionQuery(trigger.query)
      setSuggestionSymbol(trigger.symbol)
      setSuggestionConfig(trigger.config)
      
      // Get display info for the suggestion type
      const displayInfo = await getSuggestionDisplayInfo(trigger.symbol)
      setSuggestionDisplayInfo(displayInfo)
      
      // Clear previous timeout
      if (suggestionsTimeoutRef.current) {
        clearTimeout(suggestionsTimeoutRef.current)
      }

      // Debounce search
      suggestionsTimeoutRef.current = setTimeout(async () => {
        // Check if RAG is enabled for document suggestions
        if (trigger.symbol === '@' && !healthStatus.ragEnabled) {
          console.log('⚠️ RAG not enabled - showing empty suggestions dropdown')
          setSuggestions([])
          // Still show dropdown to indicate the feature is working
          if (inputRef.current) {
            const inputRect = inputRef.current.getBoundingClientRect()
            setSuggestionPosition({
              top: inputRect.top - 100,
              left: inputRect.left,
              width: inputRect.width
            })
            setShowSuggestions(true)
          }
          return
        }
        
        console.log(`🔍 Searching suggestions for "${trigger.symbol}" with query: "${trigger.query}"`)
        const results = await searchSuggestions(trigger.symbol, trigger.query)
        console.log(`📋 Found ${results.length} suggestions`)
        setSuggestions(results)
        setSelectedSuggestionIndex(0)
        
        // Calculate position for suggestions dropdown (fixed positioning)
        if (inputRef.current) {
          const inputRect = inputRef.current.getBoundingClientRect()
          // Position above the input field with some margin
          // Estimate dropdown height: header (~40px) + items (~60px each) + footer (~30px)
          const itemCount = Math.max(1, results.length) // At least 1 for empty state
          const estimatedDropdownHeight = Math.min(300, 40 + (itemCount * 60) + 30)
          setSuggestionPosition({
            top: inputRect.top - estimatedDropdownHeight - 8,
            left: inputRect.left,
            width: inputRect.width
          })
          setShowSuggestions(true)
          console.log('✅ Showing suggestions dropdown with', results.length, 'results')
        } else {
          console.warn('⚠️ inputRef.current is null, cannot show suggestions')
          setShowSuggestions(false)
        }
      }, 300) // 300ms debounce
      } else {
        setShowSuggestions(false)
        setSuggestions([])
        setSuggestionSymbol(null)
        setSuggestionConfig(null)
        setSuggestionDisplayInfo(null)
        if (suggestionsTimeoutRef.current) {
          clearTimeout(suggestionsTimeoutRef.current)
        }
      }
    } catch (error) {
      console.error('Error in handleInputChange:', error)
      setShowSuggestions(false)
      setSuggestions([])
    }
  }

  // Handle keyboard navigation in suggestions (config-based)
  const handleKeyDown = async (e) => {
    if (!showSuggestions || suggestions.length === 0 || !suggestionConfig) {
      if (e.key === 'Enter' && !e.shiftKey) {
        sendMessage(e)
      }
      return
    }

    const keyboardConfig = suggestionConfig.keyboard || {}
    const selectKey = keyboardConfig.selectKey || 'Enter'
    const closeKey = keyboardConfig.closeKey || 'Escape'
    const navigateKeys = keyboardConfig.navigateKeys || ['ArrowUp', 'ArrowDown']

    switch (e.key) {
      case 'ArrowDown':
        if (navigateKeys.includes('ArrowDown')) {
          e.preventDefault()
          setSelectedSuggestionIndex(prev => 
            prev < suggestions.length - 1 ? prev + 1 : prev
          )
        }
        break
      case 'ArrowUp':
        if (navigateKeys.includes('ArrowUp')) {
          e.preventDefault()
          setSelectedSuggestionIndex(prev => prev > 0 ? prev - 1 : 0)
        }
        break
      case 'Enter':
        if (selectKey === 'Enter') {
          e.preventDefault()
          if (suggestions[selectedSuggestionIndex]) {
            await handleSuggestionSelect(suggestions[selectedSuggestionIndex])
          }
        }
        break
      case 'Escape':
        if (closeKey === 'Escape') {
          e.preventDefault()
          setShowSuggestions(false)
          setSuggestions([])
          setSuggestionSymbol(null)
          setSuggestionConfig(null)
          setSuggestionDisplayInfo(null)
        }
        break
      default:
        // Allow normal typing
        break
    }
  }

  // Handle suggestion selection (generic, works with any suggestion type)
  const handleSuggestionSelect = async (item) => {
    if (!suggestionConfig || !suggestionSymbol) return
    
    // Find the trigger position in input
    const trigger = await detectSuggestionTrigger(input)
    if (!trigger) return
    
    // Get the replacement value (filename, name, title, etc.)
    const replacement = item.filename || item.name || item.title || item.formattedTitle || ''
    
    // Replace the trigger with the selected item
    const beforeTrigger = input.substring(0, trigger.index)
    const afterTrigger = input.substring(trigger.index + 1 + trigger.query.length)
    const newInput = `${beforeTrigger}${suggestionSymbol}${replacement}${afterTrigger}`
    
    setInput(newInput)
    setShowSuggestions(false)
    setSuggestions([])
    setSuggestionQuery('')
    setSuggestionSymbol(null)
    setSuggestionConfig(null)
    setSuggestionDisplayInfo(null)
    
    // Focus back on input
    if (inputRef.current) {
      inputRef.current.focus()
      // Move cursor to end of replacement
      const cursorPos = beforeTrigger.length + suggestionSymbol.length + replacement.length
      inputRef.current.setSelectionRange(cursorPos, cursorPos)
    }
  }

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        inputRef.current &&
        !inputRef.current.contains(event.target) &&
        !event.target.closest('.suggestion-dropdown')
      ) {
        setShowSuggestions(false)
        setSuggestionSymbol(null)
        setSuggestionConfig(null)
        setSuggestionDisplayInfo(null)
      }
    }

    if (showSuggestions) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
      }
    }
  }, [showSuggestions])

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (suggestionsTimeoutRef.current) {
        clearTimeout(suggestionsTimeoutRef.current)
      }
    }
  }, [])

  const sendMessage = async (e, selectedChunkIds = null, originalMessageId = null) => {
    if (e) e.preventDefault()
    // Allow re-sending even without input if originalMessageId is provided
    if ((!input.trim() && attachedFiles.length === 0 && !originalMessageId) || isLoading) return

    const messageId = `msg-${Date.now()}`
    let userMessage = {
      id: messageId,
      role: 'user',
      content: input.trim() || '[No text message]',
      attachments: attachedFiles.length > 0 ? attachedFiles : undefined
    }
    
    // If re-sending, find the original user message and build conversation history
    let messagesToSend = []
    if (originalMessageId && selectedChunkIds) {
      // Find the original user message index
      const originalUserMsgIndex = messages.findIndex(m => m.id === originalMessageId && m.role === 'user')
      if (originalUserMsgIndex !== -1) {
        // Use the original message content
        userMessage.content = messages[originalUserMsgIndex].content
        userMessage.attachments = messages[originalUserMsgIndex].attachments
        
        // Include conversation history up to (but not including) the assistant response
        // This means all messages before the assistant response that followed the original user message
        messagesToSend = messages.slice(0, originalUserMsgIndex + 1)
      } else {
        // Fallback: use all messages if original not found
        messagesToSend = [...messages]
      }
    } else {
      // Normal send: include all previous messages
      messagesToSend = [...messages]
    }
    
    setMessages(prev => [...prev, userMessage])
    if (!originalMessageId) {
      setInput('')
      setAttachedFiles([])
    }
    setIsLoading(true)

    try {
      const url = API_URL ? `${API_URL}/api/chat` : '/api/chat'
      
      // Convert messages to API format (remove id and chunks fields)
      const apiMessages = messagesToSend.map(msg => ({
        role: msg.role,
        content: msg.content,
        attachments: msg.attachments
      }))
      
      // Add the new user message
      apiMessages.push({
        role: userMessage.role,
        content: userMessage.content,
        attachments: userMessage.attachments
      })
      
      const requestBody = {
        messages: apiMessages,
        selected_chunks: selectedChunkIds && selectedChunkIds.length > 0 ? selectedChunkIds : undefined
      }
      
      // Only include session_id if it exists (don't send null)
      if (sessionId) {
        requestBody.session_id = sessionId
      }
      
      console.log('📤 Sending chat request:', {
        messageCount: apiMessages.length,
        hasSessionId: !!requestBody.session_id,
        sessionId: requestBody.session_id
      })
      
      console.log('Sending request:', { 
        messageCount: apiMessages.length, 
        hasSelectedChunks: !!requestBody.selected_chunks,
        selectedChunksCount: selectedChunkIds?.length || 0
      })
      const response = await axios.post(url, requestBody, {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 30000, // 30 second timeout
      })

      const assistantMessage = {
        id: response.data.message_id || `msg-${Date.now()}`,
        role: 'assistant',
        content: response.data.message,
        chunks: response.data.chunks || null
      }
      
      setMessages(prev => [...prev, assistantMessage])
      
      // Update session ID if returned from backend (auto-created or existing)
      console.log('📥 Full response data:', response.data)
      if (response.data.session_id) {
        const newSessionId = response.data.session_id
        setSessionId(newSessionId)
        // Persist session_id to localStorage
        localStorage.setItem('chatbox_session_id', newSessionId)
        console.log('✅ Session ID received and set:', newSessionId)
      } else {
        console.warn('⚠️ No session_id in response:', {
          hasSessionId: !!response.data.session_id,
          sessionId: response.data.session_id,
          responseKeys: Object.keys(response.data)
        })
      }
      
      // Initialize selected chunks for this message (all selected by default)
      if (assistantMessage.chunks && assistantMessage.chunks.length > 0) {
        // Ensure all chunk IDs are strings for consistent comparison
        const chunkIds = new Set(assistantMessage.chunks.map(chunk => String(chunk.id)))
        setSelectedChunks(prev => {
          const newMap = new Map(prev)
          newMap.set(assistantMessage.id, chunkIds)
          return newMap
        })
      }
    } catch (error) {
      console.error('Error sending message:', error)
      let errorMessage = 'Failed to get response from AI'
      
      if (error.code === 'ECONNABORTED') {
        errorMessage = 'Request timeout. Please try again.'
      } else if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
        errorMessage = 'Cannot connect to backend. Make sure the backend server is running on port 8000.'
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }
      
      setMessages(prev => [...prev, {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content: `Error: ${errorMessage}`,
        chunks: null
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleToggleChunk = (messageId, chunkId) => {
    setSelectedChunks(prev => {
      const newMap = new Map(prev)
      const oldChunkSet = newMap.get(messageId) || new Set()
      // Create a new Set to ensure React detects the change
      const newChunkSet = new Set(oldChunkSet)
      
      // Ensure chunkId is a string for consistent comparison
      const chunkIdStr = String(chunkId)
      
      if (newChunkSet.has(chunkIdStr)) {
        newChunkSet.delete(chunkIdStr)
      } else {
        newChunkSet.add(chunkIdStr)
      }
      
      newMap.set(messageId, newChunkSet)
      return newMap
    })
  }

  const handleResendWithChunks = (messageId, selectedChunkIds) => {
    // Find the original user message that triggered this assistant response
    const assistantMsgIndex = messages.findIndex(m => m.id === messageId)
    if (assistantMsgIndex === -1) {
      console.error('Assistant message not found:', messageId)
      return
    }
    
    // Find the user message before this assistant message
    let userMsgId = null
    for (let i = assistantMsgIndex - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        userMsgId = messages[i].id
        break
      }
    }
    
    if (!userMsgId) {
      console.error('User message not found before assistant message:', messageId)
      return
    }
    
    if (selectedChunkIds.length === 0) {
      console.warn('No chunks selected for re-send')
      return
    }
    
    console.log('Re-sending with chunks:', { userMsgId, selectedChunkIds })
    sendMessage(null, selectedChunkIds, userMsgId)
  }

  const handleViewChunk = async (chunk) => {
    // If chunk text is missing or placeholder, fetch from database
    const needsFetch = !chunk.text || 
        chunk.text === '[Chunk text not available]' || 
        chunk.text === '[Chunk text requires database access]' ||
        (typeof chunk.text === 'string' && chunk.text.trim() === '')
    
    if (needsFetch && chunk.id) {
      try {
        console.log('📥 Fetching chunk content from database:', chunk.id)
        const url = API_URL ? `${API_URL}/api/chunks/${chunk.id}` : `/api/chunks/${chunk.id}`
        const response = await axios.get(url, { timeout: 5000 })
        
        if (response.data && response.data.text) {
          // Update chunk with fetched text
          const updatedChunk = {
            ...chunk,
            text: response.data.text,
            document_id: response.data.document_id || chunk.document_id,
            chunk_index: response.data.chunk_index !== undefined ? response.data.chunk_index : chunk.chunk_index
          }
          
          // Update the chunk in the message's chunks array
          setMessages(prev => prev.map(msg => {
            if (msg.chunks && msg.chunks.some(c => c.id === chunk.id)) {
              return {
                ...msg,
                chunks: msg.chunks.map(c => 
                  c.id === chunk.id ? updatedChunk : c
                )
              }
            }
            return msg
          }))
          
          setViewingChunk(updatedChunk)
          console.log('✅ Fetched chunk content from database')
        } else {
          // No text in response, show chunk as-is
          setViewingChunk(chunk)
        }
      } catch (error) {
        console.error('Error fetching chunk from database:', error)
        // Show error message in chunk viewer
        const errorChunk = {
          ...chunk,
          text: `[Error loading chunk: ${error.response?.status === 404 ? 'Chunk not found in database' : error.message}]`
        }
        setViewingChunk(errorChunk)
      }
    } else {
      // Chunk text is available, show it directly
      setViewingChunk(chunk)
    }
  }

  const handleCloseViewer = () => {
    setViewingChunk(null)
  }

  const handleSessionSelect = async (sessionId) => {
    if (!sessionId) {
      setSessionId(null)
      localStorage.removeItem('chatbox_session_id')
      setMessages([{
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content: 'Hello! I\'m your AI assistant. How can I help you today?',
        chunks: null
      }])
      return
    }

    try {
      const url = API_URL ? `${API_URL}/api/sessions/${sessionId}` : `/api/sessions/${sessionId}`
      const response = await axios.get(url, { timeout: 5000 })
      
      if (response.data && response.data.messages) {
        // Convert session messages to app message format
        const loadedMessages = response.data.messages.map(msg => {
          const messageChunks = response.data.chunks && response.data.chunks[msg.id] 
            ? response.data.chunks[msg.id].map(chunk => ({
                ...chunk,
                id: String(chunk.id), // Ensure chunk ID is string
                // Preserve all chunk properties
                text: chunk.text || '',
                document_id: chunk.document_id || '',
                chunk_index: chunk.chunk_index !== undefined ? chunk.chunk_index : null,
                score: chunk.score !== undefined ? chunk.score : null,
                distance: chunk.distance !== undefined ? chunk.distance : null
              }))
            : null
          
          return {
            id: msg.id,
            role: msg.role,
            content: msg.content,
            chunks: messageChunks
          }
        })
        
        console.log('📥 Loaded session:', {
          sessionId,
          messageCount: loadedMessages.length,
          chunksCount: Object.keys(response.data.chunks || {}).length,
          chunks: response.data.chunks
        })
        
        setMessages(loadedMessages)
        setSessionId(sessionId)
        localStorage.setItem('chatbox_session_id', sessionId)
        
        // Initialize selected chunks for messages with chunks
        const newSelectedChunks = new Map()
        loadedMessages.forEach(msg => {
          if (msg.chunks && msg.chunks.length > 0) {
            // Ensure all chunk IDs are strings and properly formatted
            const chunkIds = new Set(
              msg.chunks
                .filter(chunk => chunk && chunk.id) // Filter out invalid chunks
                .map(chunk => String(chunk.id))
            )
            if (chunkIds.size > 0) {
              newSelectedChunks.set(msg.id, chunkIds)
              console.log(`✅ Loaded ${chunkIds.size} chunks for message ${msg.id}:`, Array.from(chunkIds))
            } else {
              console.warn(`⚠️  No valid chunk IDs found for message ${msg.id}`, msg.chunks)
            }
          }
        })
        setSelectedChunks(newSelectedChunks)
        console.log('📋 Initialized selected chunks:', Array.from(newSelectedChunks.entries()).map(([msgId, chunks]) => [msgId, Array.from(chunks)]))
      }
    } catch (error) {
      console.error('Error loading session:', error)
      alert('Failed to load session')
    }
  }

  const handleNewSession = (newSessionId) => {
    if (newSessionId) {
      setSessionId(newSessionId)
      localStorage.setItem('chatbox_session_id', newSessionId)
      setMessages([{
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content: 'Hello! I\'m your AI assistant. How can I help you today?',
        chunks: null
      }])
      setSelectedChunks(new Map())
      setViewingChunk(null)
    } else {
      // Clear current session
      setSessionId(null)
      localStorage.removeItem('chatbox_session_id')
    }
  }

  return (
    <div className="app-layout">
      <SessionPanel
        currentSessionId={sessionId}
        onSessionSelect={handleSessionSelect}
        onNewSession={handleNewSession}
      />
      <div className="chatbox-container">
      <div className="chatbox-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <div style={{ flex: 1 }}></div>
          <ThemeSwitcher />
        </div>
        <h1>💬 AI Chatbox</h1>
        <p>Powered by LLM API</p>
        {sessionId && (
          <div className="session-info">
            <span className="session-label">Session:</span>
            <span className="session-id" title={sessionId}>{sessionId.substring(0, 8)}...</span>
          </div>
        )}
        <div className="health-status-container">
          {healthStatus.connected === true && (
            <div className="health-status health-connected">
              <span className="health-indicator pulse"></span>
              <span className="health-text">
                ✅ Backend connected
                {healthStatus.ragEnabled && <span className="rag-badge">RAG</span>}
              </span>
              {healthStatus.lastCheck && (
                <span className="health-timestamp">
                  {new Date(healthStatus.lastCheck).toLocaleTimeString()}
                </span>
              )}
            </div>
          )}
          {healthStatus.connected === false && (
            <div className="health-status health-disconnected">
              <span className="health-indicator"></span>
              <span className="health-text">
                ⚠️ Backend disconnected
                {healthStatus.error && <span className="health-error">({healthStatus.error})</span>}
              </span>
              {healthStatus.lastCheck && (
                <span className="health-timestamp">
                  Last check: {new Date(healthStatus.lastCheck).toLocaleTimeString()}
                </span>
              )}
            </div>
          )}
          {healthStatus.connected === null && (
            <div className="health-status health-checking">
              <span className="health-indicator pulse"></span>
              <span className="health-text">🔄 Checking connection...</span>
            </div>
          )}
        </div>
      </div>
      
      <div className="chatbox-messages">
        {messages.map((msg, idx) => {
          const messageId = msg.id || `msg-${idx}`
          return (
            <div key={messageId} className={`message ${msg.role}`}>
              <div className="message-content">
                {msg.content}
                {msg.attachments && msg.attachments.length > 0 && (
                  <div className="message-attachments">
                    {msg.attachments.map((file, fileIdx) => (
                      <div key={fileIdx} className="attachment-item">
                        <span className="attachment-icon">📎</span>
                        <span className="attachment-name">{file.filename}</span>
                        <span className="attachment-size">({(file.size / 1024).toFixed(1)} KB)</span>
                      </div>
                    ))}
                  </div>
                )}
                {msg.role === 'assistant' && msg.chunks && msg.chunks.length > 0 && (
                  <ContextChunks
                    chunks={msg.chunks}
                    selectedChunks={selectedChunks.get(messageId) || new Set()}
                    onToggleChunk={(chunkId) => handleToggleChunk(messageId, chunkId)}
                    onViewChunk={handleViewChunk}
                    onResend={handleResendWithChunks}
                    messageId={messageId}
                    isLoading={isLoading}
                  />
                )}
              </div>
            </div>
          )
        })}
        {isLoading && (
          <div className="message assistant">
            <div className="message-content loading">
              <span className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {attachedFiles.length > 0 && (
        <div className="attached-files-preview">
          {attachedFiles.map((file, idx) => (
            <div key={idx} className="attached-file-item">
              <span className="file-icon">📎</span>
              <span className="file-name">{file.filename}</span>
              <button
                type="button"
                onClick={() => removeFile(idx)}
                className="remove-file-button"
                title="Remove file"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
      
      <form className="chatbox-input-form" onSubmit={sendMessage}>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          multiple
          disabled={isLoading || isUploading}
          className="file-input-hidden"
          id="file-input"
          accept=".txt,.md,.json,.csv,.log,.py,.js,.html,.css,.xml,.yaml,.yml"
        />
        <label htmlFor="file-input" className="file-upload-button" title="Attach file">
          {isUploading ? '⏳' : '📎'}
        </label>
        <div className="input-wrapper">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... Use @ for documents"
            disabled={isLoading}
            className="chatbox-input"
          />
          {showSuggestions && suggestionDisplayInfo && (
            <SuggestionDropdown
              suggestions={suggestions}
              selectedIndex={selectedSuggestionIndex}
              onSelect={handleSuggestionSelect}
              onClose={() => {
                setShowSuggestions(false)
                setSuggestionSymbol(null)
                setSuggestionConfig(null)
                setSuggestionDisplayInfo(null)
              }}
              position={suggestionPosition}
              displayInfo={suggestionDisplayInfo}
            />
          )}
        </div>
        <button
          type="submit"
          disabled={isLoading || (!input.trim() && attachedFiles.length === 0)}
          className="chatbox-send-button"
        >
          {isLoading ? '⏳' : '➤'}
        </button>
      </form>
      </div>
      <ChunkViewer chunk={viewingChunk} onClose={handleCloseViewer} />
    </div>
  )
}

export default App


