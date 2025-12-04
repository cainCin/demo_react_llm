# Suggestion Configuration

This directory contains configuration files for the extensible suggestion system.

## 📄 suggestions.yaml

**Location**: `frontend/public/config/suggestions.yaml`

This YAML file maps suggestion symbols to their configuration, making it easy to add new suggestion types without modifying code.

**Note**: The YAML file is in the `public/` directory so it can be served statically and edited without rebuilding. The system will load it at runtime, falling back to embedded defaults if unavailable.

### Structure

```yaml
suggestions:
  - symbol: "@"              # The trigger symbol
    name: "Documents"         # Display name
    description: "..."        # Description
    icon: "📄"                # Icon emoji
    provider: "documents"     # Provider identifier
    enabled: true             # Enable/disable this suggestion
    trigger:
      pattern: "^@|\\s@"      # Regex pattern to detect trigger
      minChars: 0             # Minimum chars after symbol to search
    api:
      endpoint: "/api/..."    # API endpoint
      method: "GET"           # HTTP method
      params:                 # Query parameters
        query: "{query}"      # {query} is replaced with user input
        limit: 5
    display:
      title: "Documents"      # Dropdown title
      itemTemplate: "{filename}"  # Template for item display
      metadata:               # Additional metadata to show
        - label: "Chunks"
          value: "{chunk_count}"
    keyboard:
      selectKey: "Enter"      # Key to select
      closeKey: "Escape"      # Key to close
      navigateKeys: ["ArrowUp", "ArrowDown"]  # Navigation keys
```

### Adding a New Suggestion Type

1. **Add entry to `suggestions.yaml`**:
```yaml
- symbol: "#"
  name: "Users"
  icon: "👤"
  provider: "users"
  enabled: true
  trigger:
    pattern: "^#|\\s#"
    minChars: 1
  api:
    endpoint: "/api/users/search"
    method: "GET"
    params:
      query: "{query}"
      limit: 5
  display:
    title: "Users"
    itemTemplate: "{username}"
    metadata:
      - label: "Role"
        value: "{role}"
  keyboard:
    selectKey: "Enter"
    closeKey: "Escape"
    navigateKeys: ["ArrowUp", "ArrowDown"]
```

2. **Create backend API endpoint** (if needed):
```python
@app.get("/api/users/search")
async def search_users(query: str = "", limit: int = 5):
    # Your search logic
    return {"results": [...]}
```

3. **Done!** The suggestion will automatically work in the UI.

### Template Variables

In `itemTemplate` and `metadata.value`, use `{field_name}` to reference API response fields:
- `{filename}` - Document filename
- `{username}` - User username
- `{name}` - Generic name field
- `{query}` - User's search query (in API params)

### Date Formatting

For date fields, add `format: "date"`:
```yaml
metadata:
  - label: "Date"
    value: "{created_at}"
    format: "date"
```

### Trigger Patterns

Common patterns:
- `^@` - At start of input
- `\\s@` - After whitespace
- `^@|\\s@` - At start OR after whitespace
- `^#|\\s#` - Same for # symbol

### Enabling/Disabling

Set `enabled: false` to temporarily disable a suggestion type without removing it.

## 🔧 Configuration Loading

The system:
1. Tries to load `suggestions.yaml` from `/src/config/suggestions.yaml`
2. Falls back to embedded default config if YAML can't be loaded
3. Caches config for performance

## 📝 Examples

See `suggestions.yaml` for commented examples of:
- User mentions (`#`)
- Tag suggestions (`$`)
- Document mentions (`@`) - currently enabled

## 🚀 Best Practices

1. **Use descriptive symbols** - Choose symbols that make sense (`@` for mentions, `#` for tags, etc.)
2. **Set appropriate `minChars`** - Prevents excessive API calls
3. **Limit results** - Use `limit: 5` or similar to keep UI responsive
4. **Test trigger patterns** - Ensure regex patterns work as expected
5. **Document your API** - Make sure API response format matches template variables

