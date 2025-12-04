/**
 * Suggestion Configuration Loader
 * Loads and parses suggestion configuration from YAML or uses embedded config
 */
import yaml from 'js-yaml'

// Default configuration (fallback if YAML can't be loaded)
const defaultConfig = {
  suggestions: [
    {
      symbol: "@",
      name: "Documents",
      description: "Mention documents from the database",
      icon: "📄",
      provider: "documents",
      enabled: true,
      trigger: {
        pattern: "^@|\\s@",
        minChars: 0
      },
      api: {
        endpoint: "/api/documents/search",
        method: "GET",
        params: {
          query: "{query}",
          limit: 5
        }
      },
      display: {
        title: "Documents",
        itemTemplate: "{filename}",
        metadata: [
          { label: "Chunks", value: "{chunk_count}" },
          { label: "Date", value: "{created_at}", format: "date" }
        ]
      },
      keyboard: {
        selectKey: "Enter",
        closeKey: "Escape",
        navigateKeys: ["ArrowUp", "ArrowDown"]
      }
    }
  ]
}

let cachedConfig = null

/**
 * Load suggestion configuration
 * Uses embedded default config (YAML can be loaded via import if needed)
 * For YAML support, you can import it directly: import configYaml from '../config/suggestions.yaml?raw'
 */
export const loadSuggestionConfig = async () => {
  if (cachedConfig) {
    return cachedConfig
  }

  // Try to load YAML file from public directory
  // Files in public/ are served at root, so /config/suggestions.yaml works
  try {
    const response = await fetch('/config/suggestions.yaml', {
      cache: 'no-cache' // Allow hot-reloading in dev
    })
    if (response.ok) {
      const yamlText = await response.text()
      const config = yaml.load(yamlText)
      cachedConfig = config
      console.log('✅ Loaded suggestion config from YAML')
      return config
    }
  } catch (error) {
    // Silently fall back to default config
    console.debug('Using embedded config (YAML not available):', error.message)
  }

  // Use embedded default config (always works)
  cachedConfig = defaultConfig
  console.log('📝 Using embedded suggestion config')
  console.log('📝 Config:', JSON.stringify(defaultConfig, null, 2))
  return defaultConfig
}

/**
 * Get enabled suggestions
 */
export const getEnabledSuggestions = async () => {
  const config = await loadSuggestionConfig()
  const enabled = config.suggestions.filter(s => s.enabled)
  console.log(`📝 Loaded ${enabled.length} enabled suggestion(s):`, enabled.map(s => s.symbol))
  return enabled
}

/**
 * Get suggestion by symbol
 */
export const getSuggestionBySymbol = async (symbol) => {
  const config = await loadSuggestionConfig()
  return config.suggestions.find(s => s.symbol === symbol && s.enabled)
}

/**
 * Get all suggestion symbols
 */
export const getAllSuggestionSymbols = async () => {
  const config = await loadSuggestionConfig()
  return config.suggestions
    .filter(s => s.enabled)
    .map(s => s.symbol)
}

/**
 * Check if text contains a suggestion trigger
 * Returns { symbol, query, index } or null
 */
export const detectSuggestionTrigger = async (text) => {
  if (!text || text.length === 0) {
    return null
  }

  console.log('🔍 detectSuggestionTrigger - input text:', JSON.stringify(text))
  const suggestions = await getEnabledSuggestions()
  
  if (!suggestions || suggestions.length === 0) {
    console.warn('❌ No enabled suggestions found')
    return null
  }
  
  console.log('✅ Checking', suggestions.length, 'enabled suggestion(s)')
  
  // Find the last trigger in the text (most recent one)
  let lastTrigger = null
  let lastIndex = -1
  
  for (const suggestion of suggestions) {
    try {
      const symbol = suggestion.symbol
      console.log(`  Checking symbol: "${symbol}"`)
      
      // Simple approach: find all occurrences of the symbol
      let searchIndex = 0
      while (true) {
        const symbolIndex = text.indexOf(symbol, searchIndex)
        if (symbolIndex === -1) break
        
        console.log(`    Found "${symbol}" at index ${symbolIndex}`)
        
        // Check if symbol is at start or after whitespace
        const beforeSymbol = symbolIndex === 0 ? '' : text[symbolIndex - 1]
        const isAtStart = symbolIndex === 0
        const isAfterWhitespace = /\s/.test(beforeSymbol)
        
        console.log(`      isAtStart: ${isAtStart}, isAfterWhitespace: ${isAfterWhitespace}, beforeSymbol: "${beforeSymbol}"`)
        
        if (isAtStart || isAfterWhitespace) {
          // Extract query (non-whitespace characters after symbol)
          const afterSymbol = text.substring(symbolIndex + symbol.length)
          const queryMatch = afterSymbol.match(/^(\S*)/)
          const query = queryMatch ? queryMatch[1] : ''
          
          console.log(`      Query extracted: "${query}" (minChars required: ${suggestion.trigger.minChars})`)
          
          // Check minimum characters requirement
          if (query.length >= suggestion.trigger.minChars) {
            // Use the most recent trigger (rightmost in text)
            if (symbolIndex > lastIndex) {
              lastIndex = symbolIndex
              lastTrigger = {
                symbol: symbol,
                query: query,
                index: symbolIndex,
                config: suggestion
              }
              console.log(`      ✅ Valid trigger found!`)
            }
          } else {
            console.log(`      ⚠️ Query too short (${query.length} < ${suggestion.trigger.minChars})`)
          }
        } else {
          console.log(`      ⚠️ Symbol not at valid position (not at start or after whitespace)`)
        }
        
        searchIndex = symbolIndex + 1
      }
    } catch (error) {
      console.warn(`Error detecting trigger for symbol ${suggestion.symbol}:`, error)
    }
  }
  
  if (lastTrigger) {
    console.log(`✅ FINAL: Detected trigger: ${lastTrigger.symbol} at index ${lastTrigger.index}, query: "${lastTrigger.query}"`)
  } else {
    console.log('❌ No valid trigger found')
  }
  
  return lastTrigger
}

/**
 * Format suggestion item based on template
 */
export const formatSuggestionItem = (item, config) => {
  let formatted = config.display.itemTemplate
  
  // Replace placeholders
  Object.keys(item).forEach(key => {
    const value = item[key]
    let formattedValue = value
    
    // Handle date formatting
    const metadataField = config.display.metadata?.find(m => m.value === `{${key}}`)
    if (metadataField?.format === 'date' && value) {
      formattedValue = new Date(value).toLocaleDateString()
    }
    
    formatted = formatted.replace(`{${key}}`, formattedValue)
  })
  
  return formatted
}

/**
 * Format metadata for display
 */
export const formatMetadata = (item, config) => {
  if (!config.display.metadata) {
    return []
  }
  
  return config.display.metadata.map(meta => {
    let value = meta.value
    
    // Replace placeholders
    Object.keys(item).forEach(key => {
      if (value.includes(`{${key}}`)) {
        let formattedValue = item[key]
        
        if (meta.format === 'date' && formattedValue) {
          formattedValue = new Date(formattedValue).toLocaleDateString()
        }
        
        value = value.replace(`{${key}}`, formattedValue)
      }
    })
    
    return {
      label: meta.label,
      value: value.replace(/{[^}]+}/g, '') // Remove any remaining placeholders
    }
  })
}

