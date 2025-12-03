import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
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
  const [attachedFiles, setAttachedFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Check backend connection on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        // Use health endpoint through proxy
        const healthUrl = API_URL ? `${API_URL}/health` : '/api/health'
        const response = await axios.get(healthUrl, { timeout: 3000 })
        if (response.data && response.data.status === 'ok') {
          setBackendConnected(true)
        } else {
          setBackendConnected(false)
        }
      } catch (error) {
        console.warn('Backend connection check failed:', error)
        setBackendConnected(false)
      }
    }
    checkBackend()
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
        <h1>💬 AI Chatbox</h1>
        <p>Powered by LLM API</p>
        {backendConnected === false && (
          <p style={{ fontSize: '12px', marginTop: '5px', opacity: 0.9 }}>
            ⚠️ Backend not connected. Make sure the backend server is running on port 8000.
          </p>
        )}
        {backendConnected === true && (
          <p style={{ fontSize: '12px', marginTop: '5px', opacity: 0.9 }}>
            ✅ Backend connected
          </p>
        )}
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
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={isLoading}
          className="chatbox-input"
        />
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


