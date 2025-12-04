/**
 * Theme Presets
 * Easy to add new themes from the internet - just add a new theme object here!
 * 
 * To add a new theme:
 * 1. Copy an existing theme object
 * 2. Modify the color values
 * 3. Add it to the themes export
 * 4. The theme will automatically be available in the theme switcher
 */

export const themes = {
  // Default Light Theme
  light: {
    name: 'Light',
    colors: {
      // Primary colors
      primary: '#667eea',
      primaryDark: '#764ba2',
      primaryLight: '#8b9aff',
      
      // Background colors
      background: '#ffffff',
      backgroundSecondary: '#f8f9fa',
      backgroundTertiary: '#f5f5f5',
      
      // Text colors
      text: '#333333',
      textSecondary: '#666666',
      textTertiary: '#999999',
      textInverse: '#ffffff',
      
      // Border colors
      border: '#e0e0e0',
      borderLight: '#f0f0f0',
      borderDark: '#cccccc',
      
      // Status colors
      success: '#2ed573',
      error: '#e74c3c',
      warning: '#ffc107',
      info: '#667eea',
      
      // Message colors
      messageUserBg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      messageUserText: '#ffffff',
      messageAssistantBg: '#ffffff',
      messageAssistantText: '#333333',
      
      // Input colors
      inputBg: '#ffffff',
      inputBorder: '#e0e0e0',
      inputBorderFocus: '#667eea',
      inputText: '#333333',
      
      // Button colors
      buttonPrimary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      buttonPrimaryHover: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
      buttonText: '#ffffff',
      
      // Shadow colors
      shadow: 'rgba(0, 0, 0, 0.3)',
      shadowLight: 'rgba(0, 0, 0, 0.1)',
      shadowHover: 'rgba(102, 126, 234, 0.4)',
    },
    gradients: {
      header: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }
  },

  // Dark Theme
  dark: {
    name: 'Dark',
    colors: {
      // Primary colors
      primary: '#8b9aff',
      primaryDark: '#667eea',
      primaryLight: '#a8b5ff',
      
      // Background colors
      background: '#1a1a1a',
      backgroundSecondary: '#2d2d2d',
      backgroundTertiary: '#3a3a3a',
      
      // Text colors
      text: '#e0e0e0',
      textSecondary: '#b0b0b0',
      textTertiary: '#808080',
      textInverse: '#1a1a1a',
      
      // Border colors
      border: '#404040',
      borderLight: '#333333',
      borderDark: '#555555',
      
      // Status colors
      success: '#2ed573',
      error: '#e74c3c',
      warning: '#ffc107',
      info: '#8b9aff',
      
      // Message colors
      messageUserBg: 'linear-gradient(135deg, #8b9aff 0%, #667eea 100%)',
      messageUserText: '#ffffff',
      messageAssistantBg: '#2d2d2d',
      messageAssistantText: '#e0e0e0',
      
      // Input colors
      inputBg: '#2d2d2d',
      inputBorder: '#404040',
      inputBorderFocus: '#8b9aff',
      inputText: '#e0e0e0',
      
      // Button colors
      buttonPrimary: 'linear-gradient(135deg, #8b9aff 0%, #667eea 100%)',
      buttonPrimaryHover: 'linear-gradient(135deg, #667eea 0%, #8b9aff 100%)',
      buttonText: '#ffffff',
      
      // Shadow colors
      shadow: 'rgba(0, 0, 0, 0.6)',
      shadowLight: 'rgba(0, 0, 0, 0.3)',
      shadowHover: 'rgba(139, 154, 255, 0.4)',
    },
    gradients: {
      header: 'linear-gradient(135deg, #8b9aff 0%, #667eea 100%)',
      primary: 'linear-gradient(135deg, #8b9aff 0%, #667eea 100%)',
    }
  },

  // Ocean Theme (Blue/Teal)
  ocean: {
    name: 'Ocean',
    colors: {
      primary: '#00d4ff',
      primaryDark: '#0099cc',
      primaryLight: '#33e0ff',
      
      background: '#ffffff',
      backgroundSecondary: '#f0f9ff',
      backgroundTertiary: '#e6f7ff',
      
      text: '#003d52',
      textSecondary: '#006680',
      textTertiary: '#4d9db8',
      textInverse: '#ffffff',
      
      border: '#b3e5f0',
      borderLight: '#e0f5fa',
      borderDark: '#80d0e0',
      
      success: '#00c853',
      error: '#ff5252',
      warning: '#ffab00',
      info: '#00d4ff',
      
      messageUserBg: 'linear-gradient(135deg, #00d4ff 0%, #0099cc 100%)',
      messageUserText: '#ffffff',
      messageAssistantBg: '#ffffff',
      messageAssistantText: '#003d52',
      
      inputBg: '#ffffff',
      inputBorder: '#b3e5f0',
      inputBorderFocus: '#00d4ff',
      inputText: '#003d52',
      
      buttonPrimary: 'linear-gradient(135deg, #00d4ff 0%, #0099cc 100%)',
      buttonPrimaryHover: 'linear-gradient(135deg, #0099cc 0%, #00d4ff 100%)',
      buttonText: '#ffffff',
      
      shadow: 'rgba(0, 212, 255, 0.3)',
      shadowLight: 'rgba(0, 212, 255, 0.1)',
      shadowHover: 'rgba(0, 212, 255, 0.4)',
    },
    gradients: {
      header: 'linear-gradient(135deg, #00d4ff 0%, #0099cc 100%)',
      primary: 'linear-gradient(135deg, #00d4ff 0%, #0099cc 100%)',
    }
  },

  // Forest Theme (Green)
  forest: {
    name: 'Forest',
    colors: {
      primary: '#4caf50',
      primaryDark: '#2e7d32',
      primaryLight: '#81c784',
      
      background: '#ffffff',
      backgroundSecondary: '#f1f8f4',
      backgroundTertiary: '#e8f5e9',
      
      text: '#1b5e20',
      textSecondary: '#2e7d32',
      textTertiary: '#66bb6a',
      textInverse: '#ffffff',
      
      border: '#c8e6c9',
      borderLight: '#e8f5e9',
      borderDark: '#a5d6a7',
      
      success: '#4caf50',
      error: '#f44336',
      warning: '#ff9800',
      info: '#2196f3',
      
      messageUserBg: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)',
      messageUserText: '#ffffff',
      messageAssistantBg: '#ffffff',
      messageAssistantText: '#1b5e20',
      
      inputBg: '#ffffff',
      inputBorder: '#c8e6c9',
      inputBorderFocus: '#4caf50',
      inputText: '#1b5e20',
      
      buttonPrimary: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)',
      buttonPrimaryHover: 'linear-gradient(135deg, #2e7d32 0%, #4caf50 100%)',
      buttonText: '#ffffff',
      
      shadow: 'rgba(76, 175, 80, 0.3)',
      shadowLight: 'rgba(76, 175, 80, 0.1)',
      shadowHover: 'rgba(76, 175, 80, 0.4)',
    },
    gradients: {
      header: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)',
      primary: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)',
    }
  },

  // Sunset Theme (Orange/Red)
  sunset: {
    name: 'Sunset',
    colors: {
      primary: '#ff6b35',
      primaryDark: '#e63946',
      primaryLight: '#ff8c5a',
      
      background: '#ffffff',
      backgroundSecondary: '#fff5f2',
      backgroundTertiary: '#ffe8e0',
      
      text: '#5c1a00',
      textSecondary: '#8b2e00',
      textTertiary: '#cc5c33',
      textInverse: '#ffffff',
      
      border: '#ffccb8',
      borderLight: '#ffe8e0',
      borderDark: '#ffaa8a',
      
      success: '#4caf50',
      error: '#e63946',
      warning: '#ff6b35',
      info: '#ff9800',
      
      messageUserBg: 'linear-gradient(135deg, #ff6b35 0%, #e63946 100%)',
      messageUserText: '#ffffff',
      messageAssistantBg: '#ffffff',
      messageAssistantText: '#5c1a00',
      
      inputBg: '#ffffff',
      inputBorder: '#ffccb8',
      inputBorderFocus: '#ff6b35',
      inputText: '#5c1a00',
      
      buttonPrimary: 'linear-gradient(135deg, #ff6b35 0%, #e63946 100%)',
      buttonPrimaryHover: 'linear-gradient(135deg, #e63946 0%, #ff6b35 100%)',
      buttonText: '#ffffff',
      
      shadow: 'rgba(255, 107, 53, 0.3)',
      shadowLight: 'rgba(255, 107, 53, 0.1)',
      shadowHover: 'rgba(255, 107, 53, 0.4)',
    },
    gradients: {
      header: 'linear-gradient(135deg, #ff6b35 0%, #e63946 100%)',
      primary: 'linear-gradient(135deg, #ff6b35 0%, #e63946 100%)',
    }
  },

  // Purple Dream Theme
  purple: {
    name: 'Purple Dream',
    colors: {
      primary: '#9b59b6',
      primaryDark: '#7d3c98',
      primaryLight: '#bb8fce',
      
      background: '#ffffff',
      backgroundSecondary: '#f8f4fb',
      backgroundTertiary: '#f0e8f5',
      
      text: '#4a235a',
      textSecondary: '#6c3483',
      textTertiary: '#a569bd',
      textInverse: '#ffffff',
      
      border: '#d7bde2',
      borderLight: '#f0e8f5',
      borderDark: '#c39bd3',
      
      success: '#2ed573',
      error: '#e74c3c',
      warning: '#f39c12',
      info: '#9b59b6',
      
      messageUserBg: 'linear-gradient(135deg, #9b59b6 0%, #7d3c98 100%)',
      messageUserText: '#ffffff',
      messageAssistantBg: '#ffffff',
      messageAssistantText: '#4a235a',
      
      inputBg: '#ffffff',
      inputBorder: '#d7bde2',
      inputBorderFocus: '#9b59b6',
      inputText: '#4a235a',
      
      buttonPrimary: 'linear-gradient(135deg, #9b59b6 0%, #7d3c98 100%)',
      buttonPrimaryHover: 'linear-gradient(135deg, #7d3c98 0%, #9b59b6 100%)',
      buttonText: '#ffffff',
      
      shadow: 'rgba(155, 89, 182, 0.3)',
      shadowLight: 'rgba(155, 89, 182, 0.1)',
      shadowHover: 'rgba(155, 89, 182, 0.4)',
    },
    gradients: {
      header: 'linear-gradient(135deg, #9b59b6 0%, #7d3c98 100%)',
      primary: 'linear-gradient(135deg, #9b59b6 0%, #7d3c98 100%)',
    }
  },
}

// Default theme
export const defaultTheme = 'light'

// Get theme by name
export const getTheme = (themeName) => {
  return themes[themeName] || themes[defaultTheme]
}

// Get all theme names
export const getThemeNames = () => {
  return Object.keys(themes)
}

