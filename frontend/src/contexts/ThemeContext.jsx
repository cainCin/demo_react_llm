import React, { createContext, useContext, useState, useEffect } from 'react'
import { themes, defaultTheme, getTheme } from '../themes/themes'

const ThemeContext = createContext()

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

export const ThemeProvider = ({ children }) => {
  // Get theme from localStorage or use default
  const [currentThemeName, setCurrentThemeName] = useState(() => {
    const saved = localStorage.getItem('app-theme')
    return saved && themes[saved] ? saved : defaultTheme
  })

  const currentTheme = getTheme(currentThemeName)

  // Apply theme to document root
  useEffect(() => {
    const root = document.documentElement
    const theme = currentTheme

    // Apply all color variables
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value)
    })

    // Apply gradient variables
    Object.entries(theme.gradients).forEach(([key, value]) => {
      root.style.setProperty(`--gradient-${key}`, value)
    })

    // Store theme name in localStorage
    localStorage.setItem('app-theme', currentThemeName)
  }, [currentThemeName, currentTheme])

  const setTheme = (themeName) => {
    if (themes[themeName]) {
      setCurrentThemeName(themeName)
    } else {
      console.warn(`Theme "${themeName}" not found. Using default theme.`)
      setCurrentThemeName(defaultTheme)
    }
  }

  const value = {
    currentTheme: currentTheme,
    currentThemeName: currentThemeName,
    setTheme: setTheme,
    availableThemes: Object.keys(themes).map(key => ({
      name: key,
      displayName: themes[key].name
    }))
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  )
}

