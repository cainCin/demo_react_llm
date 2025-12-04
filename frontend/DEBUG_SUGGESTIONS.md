# Debugging @ Suggestion Feature

## Quick Debug Steps

1. **Open Browser Console** (F12)
2. **Type "@" in the chatbox**
3. **Check console logs** - You should see:
   - `📝 handleInputChange called, value: "@"`
   - `🔍 detectSuggestionTrigger - input text: "@"`
   - `✅ Enabled suggestions: ["@ (Documents)"]`
   - `✅ Detected trigger: @ at index 0, query: ""`
   - `✅ Trigger detected: @ with query: ""`
   - `🔍 Searching suggestions for "@" with query: ""`
   - `🌐 Calling API: /api/documents/search with params: {query: "", limit: 5}`
   - `✅ API response: {...}`
   - `📋 Found X suggestions`

## Common Issues

### Issue 1: No trigger detected
**Symptoms**: No console logs about trigger detection
**Check**:
- Is `js-yaml` installed? Run: `cd frontend && npm list js-yaml`
- Check browser console for import errors
- Verify config is loading: Look for `📝 Using embedded suggestion config`

### Issue 2: RAG not enabled
**Symptoms**: See `⚠️ RAG not enabled` in console
**Solution**: 
- Make sure backend RAG system is initialized
- Check health status shows RAG enabled
- Upload a document first to enable RAG

### Issue 3: API call fails
**Symptoms**: See error in console about API call
**Check**:
- Is backend running on port 8000?
- Is `/api/documents/search` endpoint accessible?
- Check Network tab in browser DevTools

### Issue 4: No documents in database
**Symptoms**: API returns empty array `[]`
**Solution**: Upload a document first via the UI

### Issue 5: Dropdown not showing
**Symptoms**: Trigger detected but no dropdown appears
**Check**:
- Check `showSuggestions` state in React DevTools
- Check `suggestionDisplayInfo` is set
- Check `suggestionPosition` is calculated
- Verify CSS: `.suggestion-dropdown` should be visible

## Manual Test

Open browser console and run:

```javascript
// Test trigger detection
import { detectSuggestionTrigger } from './src/utils/suggestionConfig.js'
detectSuggestionTrigger("@test").then(console.log)

// Test config loading
import { loadSuggestionConfig } from './src/utils/suggestionConfig.js'
loadSuggestionConfig().then(console.log)

// Test API call
import { searchSuggestions } from './src/services/suggestionService.js'
searchSuggestions("@", "").then(console.log)
```

## Expected Behavior

1. Type `@` → Dropdown appears immediately (even if empty)
2. Type `@test` → Dropdown shows documents matching "test"
3. Use ↑↓ keys → Navigate suggestions
4. Press Enter → Select suggestion
5. Press Esc → Close dropdown

## Files to Check

- `frontend/src/utils/suggestionConfig.js` - Trigger detection
- `frontend/src/services/suggestionService.js` - API calls
- `frontend/src/App.jsx` - Input handler
- `frontend/src/components/SuggestionDropdown.jsx` - UI component
- `backend/main.py` - `/api/documents/search` endpoint

