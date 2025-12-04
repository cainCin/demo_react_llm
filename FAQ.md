# Frequently Asked Questions (FAQ)

Common errors, solutions, and best practices for the Chatbox App.

## 🐛 Common Errors

### Frontend Errors

#### Error: `Failed to resolve import "js-yaml"`

**Symptoms:**
```
[vite] Pre-transform error: Failed to resolve import "js-yaml" from "src/utils/suggestionConfig.js"
```

**Solution:**
```bash
cd frontend
npm install js-yaml
```

**Prevention:** Always run `npm install` after pulling changes or when dependencies are added to `package.json`.

---

#### Error: `TypeError: paramValue.replace is not a function`

**Symptoms:**
```
❌ Error searching suggestions for @: TypeError: paramValue.replace is not a function
    at suggestionService.js:31:32
```

**Solution:**
1. **Hard refresh browser** (Ctrl+Shift+R or Cmd+Shift+R)
2. **Restart dev server:**
   ```bash
   cd frontend
   # Stop server (Ctrl+C)
   npm run dev
   ```

**Cause:** Browser is using cached JavaScript code. The fix is already in the codebase - just needs a refresh.

**Prevention:** Always hard refresh after code changes, or use browser DevTools with "Disable cache" enabled.

---

#### Error: `Cannot find module 'vite'` or other dependencies

**Symptoms:**
```
Error: Cannot find module 'vite'
```

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Prevention:** Keep `node_modules` in `.gitignore` and always run `npm install` after cloning or pulling.

---

#### Suggestion dropdown shows but "No results found"

**Symptoms:**
- Dropdown appears when typing `@`
- Shows "No documents found" message

**Possible Causes & Solutions:**

1. **No documents in database:**
   - Upload a document via the UI (📎 button)
   - Or check documents: `cd backend && python database/verify_databases.py`

2. **RAG system not enabled:**
   - Check health status in UI header
   - Ensure backend has RAG enabled in `.env`: `RAG_ENABLED=true`
   - Upload a document to initialize RAG

3. **API endpoint not accessible:**
   - Check backend is running on port 8000
   - Check browser console for API errors
   - Verify `/api/documents/search` endpoint is working

**Debug Steps:**
1. Open browser console (F12)
2. Type `@` in chatbox
3. Check console logs:
   - Should see: `🌐 Calling API: /api/documents/search`
   - Should see: `✅ API response: {...}`
   - Check `total` and `count` in response

---

#### Theme switcher not showing

**Symptoms:**
- No theme switcher in header
- Theme not changing

**Solution:**
1. Check `ThemeProvider` wraps app in `main.jsx`
2. Verify `js-yaml` is installed (required for config loading)
3. Check browser console for errors
4. Hard refresh browser

---

### Backend Errors

#### Error: `psycopg2.OperationalError: connection refused`

**Symptoms:**
```
connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
```

**Solution:**
```bash
# Check if PostgreSQL container exists
docker ps -a --filter 'name=chatbox-postgres'

# If container exists but is stopped
docker start chatbox-postgres

# If container doesn't exist
cd backend
bash setup_databases.sh
```

**Prevention:** Always start PostgreSQL before starting the backend.

---

#### Error: `ConnectionConfigException: Illegal uri` (Milvus)

**Symptoms:**
```
ConnectionConfigException: (code=1, message=Illegal uri: [./milvus_lite.db])
```

**Solution:**
1. Ensure `pymilvus>=2.4.2` is installed:
   ```bash
   pip install --upgrade 'pymilvus>=2.4.2'
   ```
2. Check `MILVUS_LITE_PATH` in `.env` points to a `.db` file (not directory)
3. Ensure path is absolute or relative to backend directory

**Prevention:** Use absolute paths in `.env` for `MILVUS_LITE_PATH`.

---

#### Error: `Request timeout` (Azure OpenAI)

**Symptoms:**
```
Error: Request timeout. Please try again.
```

**Solution:**
1. Check network connection
2. Increase timeout in `backend/config.py`: `LLM_TIMEOUT=120`
3. Check Azure OpenAI service status
4. Verify API key and endpoint are correct

**Prevention:** Set appropriate timeout based on your network and model size.

---

#### Error: `DataNotMatchException: id field should be int64`

**Symptoms:**
```
The Input data type is inconsistent with defined schema, {id} field should be a int64
```

**Solution:**
- This is automatically handled by `DatabaseManager._uuid_to_int64()`
- If error persists, delete Milvus collection to recreate with correct schema:
  ```python
  # In Python console or script
  from database import DatabaseManager
  db = DatabaseManager()
  db.initialize()
  db.milvus_client.drop_collection("chatbox_vectors")
  # Restart app to recreate collection
  ```

**Prevention:** Always use `DatabaseManager` methods, don't insert directly into Milvus.

---

#### Error: `RAG system is not enabled`

**Symptoms:**
- API returns: `"RAG system is not enabled"`
- Suggestion system doesn't work

**Solution:**
1. Check `RAG_ENABLED=true` in `backend/.env`
2. Ensure OpenAI client is initialized
3. Upload a document to initialize RAG system
4. Check backend logs for RAG initialization errors

---

### Database Errors

#### Error: Databases not synchronized

**Symptoms:**
- Verification shows count mismatch
- Documents in PostgreSQL but not in Milvus (or vice versa)

**Solution:**
```bash
# Resynchronize databases
curl -X POST http://localhost:8000/api/documents/resync

# Or via Python
cd backend
python -c "from rag_system import RAGSystem; from openai import OpenAI; import os; rag = RAGSystem(OpenAI(api_key=os.getenv('OPENAI_API_KEY'))); rag.resync_databases()"
```

**Prevention:** Always use `rag_system.store_document()` instead of direct database operations.

---

#### Error: `Session {session_id} does not exist`

**Symptoms:**
```
ValueError: Session <session_id> does not exist. Log file: sessions/logs/<session_id>.csv
```

**Solution:**
- The system automatically creates missing session files when needed
- If error persists, check file permissions on `sessions/` directory
- Verify session ID is valid UUID format

**Prevention:** Session files are auto-created. Ensure `sessions/` directory is writable.

---

#### Error: Chunk text not available when loading session

**Symptoms:**
- Session loads but chunks show "[Chunk text not available]"
- Chunk viewer shows loading message

**Solution:**
1. Click on the chunk to trigger on-demand loading from database
2. Verify chunk exists in PostgreSQL: `SELECT * FROM chunks WHERE id = 'chunk-id'`
3. Check if chunk was deleted from database after session was created

**Prevention:** Chunks are fetched from database when clicked. Ensure chunks aren't deleted while sessions reference them.

---

#### Error: `NameError: name 'VerificationResult' is not defined`

**Symptoms:**
```
NameError: name 'VerificationResult' is not defined
```

**Solution:**
- Ensure all data classes are imported:
  ```python
  from database import VerificationResult, ResyncResult
  ```

**Prevention:** Always import data classes from `database` package, not from individual modules.

---

## ✅ Best Practices

### Development

1. **Always activate virtual environment:**
   ```bash
   cd backend
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

2. **Keep dependencies updated:**
   ```bash
   # Backend
   pip install --upgrade -r requirements.txt
   
   # Frontend
   cd frontend
   npm update
   ```

3. **Use environment variables:**
   - Never commit `.env` files
   - Use `env.example` as template
   - Document new environment variables

4. **Test before committing:**
   - Run linter: Check for errors
   - Test API endpoints: Use `/docs` or curl
   - Test UI: Check browser console for errors

### Database Management

1. **Always use DatabaseManager:**
   - Don't access databases directly
   - Use provided methods for all operations
   - Ensures synchronization between PostgreSQL and Milvus

2. **Verify before critical operations:**
   ```python
   result = db_manager.verify()
   if not result.synchronized:
       print("Warning: Databases not synchronized!")
   ```

3. **Backup before cleanup:**
   - Export data before `clean_all()`
   - Use verification script to export CSV

4. **Use data classes:**
   - Always use data classes from `database.models`
   - Don't use raw dictionaries
   - Ensures type safety and consistency

### Suggestion System

1. **Test trigger detection:**
   - Type `@` at start of input
   - Type `@` after space
   - Verify dropdown appears

2. **Check console logs:**
   - Enable detailed logging in development
   - Check for API errors
   - Verify response format

3. **Add new suggestion types:**
   - Edit `frontend/public/config/suggestions.yaml`
   - Test with different symbols
   - Verify API endpoint exists

### Theme System

1. **Test all themes:**
   - Ensure text is readable in dark themes
   - Check contrast ratios (WCAG AA minimum)
   - Verify all components use CSS variables

2. **Add new themes:**
   - Copy existing theme structure
   - Use online color palette generators
   - Test in both light and dark modes

### API Development

1. **Use proper HTTP status codes:**
   - 200: Success
   - 400: Bad request (client error)
   - 500: Server error

2. **Return consistent response format:**
   ```python
   return {
       "status": "ok",
       "data": {...},
       "message": "Optional message"
   }
   ```

3. **Handle errors gracefully:**
   - Log errors server-side
   - Return user-friendly error messages
   - Don't expose internal details

### Performance

1. **Debounce API calls:**
   - Use 300ms debounce for search
   - Prevent excessive API requests
   - Cache results when possible

2. **Optimize database queries:**
   - Use indexes (already on `document_id`)
   - Limit result sets
   - Use pagination for large datasets

3. **Monitor resource usage:**
   - Check PostgreSQL connection pool
   - Monitor Milvus memory usage
   - Watch for memory leaks

## 🔍 Debugging Tips

### Frontend Debugging

1. **Browser Console:**
   - Open DevTools (F12)
   - Check Console tab for errors
   - Check Network tab for API calls
   - Use React DevTools for state inspection

2. **Check State:**
   ```javascript
   // In browser console
   // Check if theme is loaded
   localStorage.getItem('app-theme')
   
   // Check if config is cached
   // Look for console logs from suggestionConfig.js
   ```

3. **Network Issues:**
   - Verify backend is running
   - Check CORS settings
   - Verify proxy configuration in `vite.config.js`

### Backend Debugging

1. **Check Logs:**
   - Backend prints detailed logs
   - Look for ✅ (success) and ❌ (error) markers
   - Check for stack traces

2. **Test API Endpoints:**
   ```bash
   # Health check
   curl http://localhost:8000/api/health
   
   # List documents
   curl http://localhost:8000/api/documents
   
   # Search documents
   curl "http://localhost:8000/api/documents/search?query=test&limit=5"
   ```

3. **Database Verification:**
   ```bash
   cd backend
   python database/verify_databases.py
   ```

### Common Debugging Commands

```bash
# Check if services are running
docker ps
ps aux | grep python
ps aux | grep node

# Check ports
netstat -tulpn | grep 8000  # Backend
netstat -tulpn | grep 3000  # Frontend

# Check database connection
docker exec -it chatbox-postgres psql -U chatbox_user -d chatbox_db -c "SELECT COUNT(*) FROM documents;"

# View backend logs
# (Check terminal where backend is running)

# View frontend logs
# (Check browser console)
```

## 📚 Additional Resources

- **Backend API Docs:** http://localhost:8000/docs (Swagger UI)
- **Feature Documentation:** `FEATURES.md` - Session management, chunk selection, chunk viewer
- **Database Documentation:** `backend/database/README.md`
- **Suggestion System:** `frontend/SUGGESTION_SYSTEM.md`
- **Theme System:** `frontend/src/themes/README.md`
- **Installation Guide:** `INSTALLATION.md`

## 🆘 Still Having Issues?

1. **Check logs:** Both browser console and backend terminal
2. **Verify setup:** Run installation verification
3. **Check versions:** Ensure Python 3.8+ and Node.js 16+
4. **Clear caches:** Browser cache, npm cache, Python cache
5. **Restart services:** Backend and frontend dev servers
6. **Check environment:** Verify `.env` file is correct

## 💡 Pro Tips

1. **Use browser DevTools:**
   - Enable "Disable cache" during development
   - Use Network tab to debug API calls
   - Use React DevTools for component inspection

2. **Keep console open:**
   - Many errors are logged to console
   - Check for warnings (yellow) and errors (red)

3. **Test incrementally:**
   - Test one feature at a time
   - Verify each step before moving on
   - Use git commits to track working states

4. **Document your setup:**
   - Note any custom configurations
   - Document environment-specific settings
   - Keep troubleshooting notes

5. **Use version control:**
   - Commit working code frequently
   - Use branches for experiments
   - Tag stable versions

