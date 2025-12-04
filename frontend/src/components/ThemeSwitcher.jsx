import React, { useState, useRef, useEffect } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import './ThemeSwitcher.css'

const ThemeSwitcher = () => {
  const { currentThemeName, setTheme, availableThemes } = useTheme()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const handleThemeChange = (themeName) => {
    setTheme(themeName)
    setIsOpen(false)
  }

  const currentThemeDisplay = availableThemes.find(t => t.name === currentThemeName)?.displayName || currentThemeName

  return (
    <div className="theme-switcher" ref={dropdownRef}>
      <button
        className="theme-switcher-button"
        onClick={() => setIsOpen(!isOpen)}
        title="Change theme"
        aria-label="Change theme"
      >
        <span className="theme-icon">🎨</span>
        <span className="theme-name">{currentThemeDisplay}</span>
        <span className={`theme-arrow ${isOpen ? 'open' : ''}`}>▼</span>
      </button>
      
      {isOpen && (
        <div className="theme-dropdown">
          {availableThemes.map((theme) => (
            <button
              key={theme.name}
              className={`theme-option ${currentThemeName === theme.name ? 'active' : ''}`}
              onClick={() => handleThemeChange(theme.name)}
            >
              <span className="theme-option-name">{theme.displayName}</span>
              {currentThemeName === theme.name && (
                <span className="theme-check">✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default ThemeSwitcher

