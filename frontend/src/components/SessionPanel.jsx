import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './SessionPanel.css'

const API_URL = import.meta.env.VITE_API_URL || ''

const SessionPanel = ({ currentSessionId, onSessionSelect, onNewSession }) => {
  const [sessions, setSessions] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadSessions = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const url = API_URL ? `${API_URL}/api/sessions` : '/api/sessions'
      const response = await axios.get(url, { timeout: 5000 })
      setSessions(response.data || [])
    } catch (err) {
      console.error('Error loading sessions:', err)
      setError('Failed to load sessions')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadSessions()
    // Refresh sessions periodically
    const interval = setInterval(loadSessions, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleCreateSession = async () => {
    try {
      const url = API_URL ? `${API_URL}/api/sessions` : '/api/sessions'
      const response = await axios.post(url, { title: null }, { timeout: 5000 })
      if (response.data && response.data.session_id) {
        await loadSessions() // Refresh list
        if (onNewSession) {
          onNewSession(response.data.session_id)
        }
      }
    } catch (err) {
      console.error('Error creating session:', err)
      setError('Failed to create session')
    }
  }

  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation()
    if (!window.confirm('Are you sure you want to delete this session?')) {
      return
    }
    
    try {
      const url = API_URL ? `${API_URL}/api/sessions/${sessionId}` : `/api/sessions/${sessionId}`
      await axios.delete(url, { timeout: 5000 })
      await loadSessions() // Refresh list
      
      // If deleted session was current, clear selection
      if (sessionId === currentSessionId && onNewSession) {
        onNewSession(null)
      }
    } catch (err) {
      console.error('Error deleting session:', err)
      setError('Failed to delete session')
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="session-panel">
      <div className="session-panel-header">
        <h2>Sessions</h2>
        <button
          className="new-session-button"
          onClick={handleCreateSession}
          title="Create new session"
        >
          ➕ New
        </button>
      </div>
      
      {error && (
        <div className="session-panel-error">
          {error}
        </div>
      )}
      
      <div className="session-panel-content">
        {isLoading && sessions.length === 0 ? (
          <div className="session-panel-loading">
            <span>Loading sessions...</span>
          </div>
        ) : sessions.length === 0 ? (
          <div className="session-panel-empty">
            <p>No sessions yet</p>
            <p className="empty-hint">Create a new session to start chatting</p>
          </div>
        ) : (
          <div className="session-list">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                className={`session-item ${currentSessionId === session.session_id ? 'active' : ''}`}
                onClick={() => onSessionSelect && onSessionSelect(session.session_id)}
                title={session.title}
              >
                <div className="session-item-header">
                  <div className="session-item-title">
                    {session.title || `Session ${session.session_id.substring(0, 8)}`}
                  </div>
                  <button
                    className="session-delete-button"
                    onClick={(e) => handleDeleteSession(session.session_id, e)}
                    title="Delete session"
                  >
                    ×
                  </button>
                </div>
                <div className="session-item-meta">
                  <span className="session-message-count">
                    {session.message_count || 0} messages
                  </span>
                  <span className="session-date">
                    {formatDate(session.updated_at || session.created_at)}
                  </span>
                </div>
                {currentSessionId === session.session_id && (
                  <div className="session-active-indicator">Active</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default SessionPanel

