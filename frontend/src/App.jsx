import React, { useState, useRef, useEffect, useCallback } from 'react'
import axios from 'axios'
import { useTheme } from './contexts/ThemeContext'
import ThemeSwitcher from './components/ThemeSwitcher'
import SuggestionDropdown from './components/SuggestionDropdown'
import { detectSuggestionTrigger } from './utils/suggestionConfig'
import { searchSuggestions, getSuggestionDisplayInfo } from './services/suggestionService'
import './App.css'

// Use relative URL to leverage Vite proxy, or full URL if VITE_API_URL is set
const API_URL = import.meta.env.VITE_API_URL || ''

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your AI assistant. How can I help you today?'
    }
  ])
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

  const sendMessage = async (e) => {
    e.preventDefault()
    if ((!input.trim() && attachedFiles.length === 0) || isLoading) return

    const userMessage = {
      role: 'user',
      content: input.trim() || '[No text message]',
      attachments: attachedFiles.length > 0 ? attachedFiles : undefined
    }
    
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setAttachedFiles([])
    setIsLoading(true)

    try {
      const url = API_URL ? `${API_URL}/api/chat` : '/api/chat'
      const requestBody = {
        messages: [...messages, userMessage]
        // model is omitted - backend will use appropriate default based on provider
      }
      const response = await axios.post(url, requestBody, {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 30000, // 30 second timeout
      })

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.message
      }])
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
        role: 'assistant',
        content: `Error: ${errorMessage}`
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chatbox-container">
      <div className="chatbox-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <div style={{ flex: 1 }}></div>
          <ThemeSwitcher />
        </div>
        <h1>💬 AI Chatbox</h1>
        <p>Powered by LLM API</p>
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
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
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
            </div>
          </div>
        ))}
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
  )
}

export default App


