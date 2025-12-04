/**
 * Suggestion Service
 * Handles API calls for different suggestion types
 */
import axios from 'axios'
import { getSuggestionBySymbol, formatSuggestionItem, formatMetadata } from '../utils/suggestionConfig'

const API_URL = import.meta.env.VITE_API_URL || ''

/**
 * Search suggestions based on configuration
 */
export const searchSuggestions = async (symbol, query) => {
  const config = await getSuggestionBySymbol(symbol)
  
  if (!config) {
    console.warn(`❌ No suggestion config found for symbol: ${symbol}`)
    return []
  }

  try {
    // Build API URL
    const endpoint = config.api.endpoint
    const url = API_URL ? `${API_URL}${endpoint}` : endpoint
    
    // Build params - safely handle different types
    const params = {}
    if (!config.api || !config.api.params) {
      console.warn('⚠️ Config missing api.params')
      return []
    }
    
    Object.keys(config.api.params).forEach(key => {
      const paramValue = config.api.params[key]
      
      try {
        // Only replace if it's a string and contains the placeholder
        if (typeof paramValue === 'string' && paramValue.includes && paramValue.includes('{query}')) {
          params[key] = paramValue.replace('{query}', query)
        } else {
          // Use value as-is for numbers, booleans, null, etc.
          params[key] = paramValue
        }
      } catch (error) {
        console.warn(`⚠️ Error processing param ${key}:`, error, 'value:', paramValue)
        params[key] = paramValue
      }
    })
    
    console.log(`📋 Built params:`, params)
    
    console.log(`🌐 Calling API: ${url} with params:`, params)
    
    // Make API call
    const response = await axios.get(url, {
      params: params,
      timeout: 2000
    })
    
    console.log(`✅ API response:`, response.data)
    console.log(`📊 Response structure:`, {
      hasDocuments: !!response.data?.documents,
      hasResults: !!response.data?.results,
      isArray: Array.isArray(response.data),
      total: response.data?.total,
      count: response.data?.count
    })
    
    // Extract results (handle different response formats)
    let results = []
    if (response.data?.documents) {
      results = response.data.documents
      console.log(`📄 Extracted ${results.length} documents from response.data.documents`)
    } else if (response.data?.results) {
      results = response.data.results
      console.log(`📄 Extracted ${results.length} results from response.data.results`)
    } else if (Array.isArray(response.data)) {
      results = response.data
      console.log(`📄 Extracted ${results.length} items from array response`)
    } else {
      console.warn(`⚠️ Unexpected response format:`, response.data)
    }
    
    if (results.length === 0) {
      console.warn(`⚠️ No results found. Total documents in DB: ${response.data?.total || 'unknown'}`)
    }
    
    // Format results with metadata
    const formattedResults = results.map(item => {
      try {
        return {
          ...item,
          formattedTitle: formatSuggestionItem(item, config),
          metadata: formatMetadata(item, config),
          config: config
        }
      } catch (error) {
        console.warn(`Error formatting item:`, item, error)
        return {
          ...item,
          formattedTitle: item.filename || item.name || 'Unknown',
          metadata: [],
          config: config
        }
      }
    })
    
    console.log(`✅ Formatted ${formattedResults.length} results`)
    return formattedResults
  } catch (error) {
    console.error(`❌ Error searching suggestions for ${symbol}:`, error)
    if (error.response) {
      console.error(`   Response status: ${error.response.status}`)
      console.error(`   Response data:`, error.response.data)
    } else if (error.request) {
      console.error(`   No response received. Is backend running?`)
    } else {
      console.error(`   Error:`, error.message)
    }
    return []
  }
}

/**
 * Get suggestion display info
 */
export const getSuggestionDisplayInfo = async (symbol) => {
  const config = await getSuggestionBySymbol(symbol)
  
  if (!config) {
    return null
  }
  
  return {
    name: config.name,
    icon: config.icon,
    title: config.display.title,
    description: config.description
  }
}

