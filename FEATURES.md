# Chatbox App - Feature Documentation

This document provides detailed documentation for key features of the Chatbox App, including session management, reference chunk selection, and chunk viewer.

## 📋 Table of Contents

1. [Session Management](#session-management)
2. [Reference Chunk Selection](#reference-chunk-selection)
3. [Chunk Viewer](#chunk-viewer)
4. [API Reference](#api-reference)

---

## 💾 Session Management

### Overview

Session management allows you to save, load, and manage chat conversations. Each session has a unique ID and stores all messages and context chunks in CSV format for easy tracking and analysis.

### Key Features

- **Automatic Session Creation**: Sessions are automatically created when you start a new conversation
- **Session Persistence**: All messages and chunks are saved to CSV files
- **Session Panel**: Left-side panel to browse and manage all sessions
- **Session Metadata**: Each session tracks title, creation time, update time, and message count
- **Optimized Storage**: Only chunk IDs are stored in logs; full chunk text is fetched from database when needed

### How It Works

#### Session Structure

Each session consists of three files:

1. **Metadata File** (`{session_id}.json`):
   ```json
   {
     "session_id": "uuid-here",
     "title": "Session Title",
     "created_at": "2024-01-01T12:00:00",
     "updated_at": "2024-01-01T12:30:00",
     "message_count": 10
   }
   ```

2. **Message Log** (`logs/{session_id}.csv`):
   - Stores all user and assistant messages
   - Columns: `timestamp`, `message_id`, `role`, `content`, `model`, `has_attachments`, `attachment_count`

3. **Chunks Log** (`chunks/{session_id}.csv`):
   - Stores chunk IDs and metadata (not full text)
   - Columns: `timestamp`, `message_id`, `chunk_id`, `document_id`, `chunk_index`, `score`, `distance`
   - Full chunk text is fetched from PostgreSQL when needed

#### Session Storage Location

Sessions are stored in the `sessions/` directory (configurable via `SESSIONS_DIR` environment variable):

```
sessions/
├── {session_id_1}.json
├── {session_id_2}.json
├── logs/
│   ├── {session_id_1}.csv
│   └── {session_id_2}.csv
└── chunks/
    ├── {session_id_1}.csv
    └── {session_id_2}.csv
```

### Using Sessions

#### Creating a New Session

1. **Automatic**: A new session is automatically created when you send your first message
2. **Manual**: Click the "+ New" button in the Session Panel

#### Loading a Session

1. Click on any session in the Session Panel
2. All messages and chunks for that session will be loaded
3. The session ID is displayed in the chatbox header

#### Switching Between Sessions

1. Click on a different session in the Session Panel
2. The current conversation will be replaced with the selected session's messages
3. Your current session is automatically saved before switching

#### Deleting a Session

1. Click the "×" button next to a session in the Session Panel
2. Confirm deletion
3. All session files (metadata, logs, chunks) will be permanently deleted

#### Session ID Display

The current session ID is displayed in the chatbox header, showing:
- Session ID (first 8 characters)
- Session status (active/inactive)

### Session Data Flow

```
User sends message
    ↓
Backend processes message
    ↓
Session auto-created (if needed)
    ↓
Message saved to session log (background task)
    ↓
Chunks retrieved from RAG system
    ↓
Chunk IDs saved to session chunks log (background task)
    ↓
Response returned to frontend
    ↓
Session ID displayed in header
```

### Best Practices

1. **Session Titles**: Update session titles to make them easier to find later
2. **Regular Cleanup**: Delete old sessions you no longer need
3. **Session Backup**: The CSV files can be easily backed up or exported
4. **Chunk Storage**: Chunk IDs are stored, not full text, to keep file sizes small

### Troubleshooting

**Issue**: Session ID is `null` in the UI
- **Solution**: Check backend logs for session creation errors. Ensure `sessions/` directory is writable.

**Issue**: Session files are missing
- **Solution**: The system automatically creates missing files when needed. If issues persist, check file permissions.

**Issue**: Cannot load session
- **Solution**: Verify session files exist in `sessions/` directory. Check backend logs for errors.

---

## 🔍 Reference Chunk Selection

### Overview

Reference chunk selection allows you to control which context chunks are sent to the LLM. You can select or deselect chunks from the RAG retrieval results to improve answer quality.

### Key Features

- **Visual Chunk List**: All retrieved chunks are displayed as checkboxes below each assistant message
- **Select/Deselect**: Click checkboxes to include or exclude chunks
- **Re-send with Selection**: Send the same message again with only selected chunks
- **Chunk Metadata**: Each chunk shows document ID, chunk index, and similarity score
- **Persistent Selection**: Selected chunks are remembered per message

### How It Works

#### Chunk Display

When the assistant responds with RAG context, chunks are displayed below the message:

```
[✓] Chunk 1: Document abc123, Index 0, Score: 0.85
[✓] Chunk 2: Document abc123, Index 1, Score: 0.82
[ ] Chunk 3: Document xyz789, Index 5, Score: 0.75
```

- **Checkbox**: Click to select/deselect
- **Chunk Text Preview**: First 200 characters of chunk text
- **Metadata**: Document ID (first 8 chars), chunk index, similarity score

#### Selecting Chunks

1. **Default**: All chunks are selected by default
2. **Deselect**: Click the checkbox to uncheck a chunk
3. **Re-select**: Click again to re-check a chunk
4. **Visual Feedback**: Selected chunks have a checkmark, deselected chunks are dimmed

#### Re-sending with Selected Chunks

1. Deselect irrelevant chunks
2. Click the "Re-send" button
3. The original user message is re-sent with only the selected chunks
4. The assistant generates a new response with the filtered context

### Chunk Selection State

The selection state is managed per message:

```javascript
{
  messageId: Set<chunkId1, chunkId2, ...>
}
```

- Each message has its own set of selected chunk IDs
- Selection persists when switching sessions
- Selection is cleared when starting a new session

### Use Cases

1. **Filtering Irrelevant Context**: Remove chunks that don't match your query
2. **Focusing on Specific Documents**: Select only chunks from specific documents
3. **Improving Answer Quality**: Re-send with better context selection
4. **Experimenting**: Try different chunk combinations to see which works best

### Best Practices

1. **Review Before Re-sending**: Check chunk previews to understand what context will be sent
2. **Keep Relevant Chunks**: Only deselect chunks that are clearly irrelevant
3. **Use Similarity Scores**: Higher scores indicate more relevant chunks
4. **Test Different Combinations**: Experiment with different chunk selections

### Troubleshooting

**Issue**: Cannot deselect chunks
- **Solution**: Ensure you're clicking the checkbox, not the chunk text. Check browser console for errors.

**Issue**: Re-send button doesn't work
- **Solution**: Verify at least one chunk is selected. Check browser console for API errors.

**Issue**: Chunks not showing
- **Solution**: Ensure RAG system is enabled and documents are indexed. Check backend logs.

---

## 📄 Chunk Viewer

### Overview

The Chunk Viewer displays the full content of a selected chunk in a dedicated side panel. It provides a focused view of chunk text and metadata.

### Key Features

- **Full Text Display**: Shows complete chunk content (not truncated)
- **Metadata Display**: Document ID, chunk index, similarity score, distance
- **Side-by-Side Layout**: Chunk viewer appears next to the chatbox
- **On-Demand Loading**: Fetches chunk text from database if missing
- **Click to View**: Click any chunk to view its full content

### How It Works

#### Opening the Chunk Viewer

1. Click on any chunk in the Context Chunks list
2. The Chunk Viewer panel opens on the right side
3. Full chunk text and metadata are displayed

#### Chunk Viewer Layout

```
┌─────────────────────────────────┐
│ 📄 Chunk Content          [×]   │  ← Header
├─────────────────────────────────┤
│ Document ID: abc123...          │  ← Metadata
│ Chunk Index: 0                  │
│ Similarity Score: 85.00%        │
│ Distance: 0.1500                │
├─────────────────────────────────┤
│                                 │
│ Full chunk text content here... │  ← Content
│ (complete, not truncated)       │
│                                 │
└─────────────────────────────────┘
```

#### On-Demand Content Loading

If chunk text is missing (e.g., when loading from session logs):

1. Click on a chunk with missing text
2. Frontend detects missing text
3. API call to `/api/chunks/{chunk_id}` is made
4. Chunk text is fetched from PostgreSQL
5. Content is displayed in the viewer
6. Chunk is updated in the message's chunks array (cached)

#### Chunk Text States

- **Available**: Full text is displayed
- **Missing**: Shows "[Click to load content from database]"
- **Loading**: Shows "Loading content from database..."
- **Error**: Shows error message if fetch fails

### Chunk Viewer Features

#### Metadata Display

- **Document ID**: The document this chunk belongs to
- **Chunk Index**: Position of chunk within the document
- **Similarity Score**: Relevance score (0-1, displayed as percentage)
- **Distance**: Vector distance (lower = more similar)

#### Text Display

- **Full Content**: Complete chunk text (no truncation)
- **Word Wrapping**: Text wraps properly for long content
- **Scrollable**: Scroll for very long chunks
- **Formatted**: Preserves original formatting

#### Closing the Viewer

- Click the "×" button in the header
- Click outside the viewer (if implemented)
- Select a different chunk (replaces current view)

### Use Cases

1. **Reviewing Context**: See exactly what context was sent to the LLM
2. **Understanding Relevance**: Check why a chunk was retrieved
3. **Verifying Content**: Ensure chunk content matches expectations
4. **Debugging**: Identify issues with chunk retrieval or selection

### Best Practices

1. **Review Before Re-sending**: Check chunk content before re-sending with selection
2. **Use Metadata**: Similarity scores help identify most relevant chunks
3. **Check Multiple Chunks**: View different chunks to understand full context
4. **Verify Content**: Ensure chunk text matches what you expect

### Troubleshooting

**Issue**: Chunk viewer shows "Loading content from database..."
- **Solution**: Check backend logs for database errors. Verify chunk exists in PostgreSQL.

**Issue**: Chunk text is missing
- **Solution**: Click the chunk to trigger on-demand loading. Check if chunk was deleted from database.

**Issue**: Chunk viewer doesn't open
- **Solution**: Check browser console for errors. Verify chunk object has required fields.

---

## 🔌 API Reference

### Session Management Endpoints

#### `POST /api/sessions`

Create a new chat session.

**Request:**
```json
{
  "title": "Optional session title"
}
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "title": "Session Title",
  "created_at": "2024-01-01T12:00:00"
}
```

#### `GET /api/sessions`

List all sessions.

**Response:**
```json
[
  {
    "session_id": "uuid-here",
    "title": "Session Title",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:30:00",
    "message_count": 10
  }
]
```

#### `GET /api/sessions/{session_id}`

Get session messages and chunks.

**Response:**
```json
{
  "session_id": "uuid-here",
  "messages": [
    {
      "id": "msg-123",
      "role": "user",
      "content": "Hello!",
      "timestamp": "2024-01-01T12:00:00"
    },
    {
      "id": "msg-124",
      "role": "assistant",
      "content": "Hi there!",
      "timestamp": "2024-01-01T12:00:05"
    }
  ],
  "chunks": {
    "msg-124": [
      {
        "id": "chunk-id",
        "text": "Chunk text...",
        "document_id": "doc-id",
        "chunk_index": 0,
        "score": 0.85,
        "distance": 0.15
      }
    ]
  }
}
```

#### `PUT /api/sessions/{session_id}/title`

Update session title.

**Request:**
```json
{
  "title": "New Title"
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Session title updated"
}
```

#### `DELETE /api/sessions/{session_id}`

Delete a session.

**Response:**
```json
{
  "status": "ok",
  "message": "Session deleted"
}
```

### Chunk Endpoints

#### `GET /api/chunks/{chunk_id}`

Get chunk content by ID from database.

**Response:**
```json
{
  "id": "chunk-id",
  "text": "Full chunk text content...",
  "document_id": "doc-id",
  "chunk_index": 0
}
```

**Errors:**
- `404`: Chunk not found
- `400`: RAG system not enabled

### Chat Endpoint (Updated)

#### `POST /api/chat`

Send a chat message (now includes session management).

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "session_id": "optional-session-id",
  "selected_chunks": ["chunk-id-1", "chunk-id-2"]
}
```

**Response:**
```json
{
  "message": "Assistant response",
  "model": "gpt-3.5-turbo",
  "chunks": [
    {
      "id": "chunk-id",
      "text": "Chunk text...",
      "document_id": "doc-id",
      "chunk_index": 0,
      "score": 0.85,
      "distance": 0.15
    }
  ],
  "session_id": "uuid-here",
  "message_id": "msg-123"
}
```

**Notes:**
- If `session_id` is not provided, a new session is automatically created
- `selected_chunks` filters which chunks are used as context
- Session data is saved asynchronously (background task)

---

## 🔗 Related Documentation

- **Main README**: [README.md](README.md) - Project overview and setup
- **API Documentation**: http://localhost:8000/docs - Swagger UI
- **Database Documentation**: [backend/database/README.md](backend/database/README.md)
- **FAQ**: [FAQ.md](FAQ.md) - Troubleshooting and best practices
- **Conventions**: [CONVENTIONS.md](CONVENTIONS.md) - Development guidelines

---

## 📝 Notes

- Session files are stored in CSV format for easy analysis and export
- Chunk IDs are stored in logs, not full text, to optimize storage
- Full chunk text is fetched from PostgreSQL when needed
- Session data is saved asynchronously to avoid blocking API responses
- All session operations are logged for debugging

