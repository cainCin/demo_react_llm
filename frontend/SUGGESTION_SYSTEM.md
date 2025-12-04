# Extensible Suggestion System

## Overview

The suggestion system allows users to trigger contextual suggestions by typing special symbols (like `@` for documents). The system is fully extensible through YAML configuration, making it easy to add new suggestion types without code changes.

## Architecture

### Components

1. **Configuration** (`public/config/suggestions.yaml`)
   - YAML file mapping symbols to suggestion providers
   - Located in `public/` directory for easy editing without rebuilds
   - Defines API endpoints, display templates, and behavior

2. **Config Loader** (`src/utils/suggestionConfig.js`)
   - Loads and parses YAML configuration
   - Provides utilities for trigger detection and formatting

3. **Suggestion Service** (`src/services/suggestionService.js`)
   - Handles API calls for different suggestion types
   - Formats results based on configuration

4. **UI Component** (`src/components/SuggestionDropdown.jsx`)
   - Generic dropdown component that works with any suggestion type
   - Theme-aware and keyboard navigable

5. **Integration** (`src/App.jsx`)
   - Detects suggestion triggers in input
   - Manages suggestion state and selection

## How It Works

1. **User types a symbol** (e.g., `@`)
2. **System detects trigger** using regex patterns from config
3. **Extracts query** text after the symbol
4. **Calls API** based on configuration
5. **Shows dropdown** with formatted results
6. **User selects** item, which replaces the trigger

## Adding New Suggestion Types

### Step 1: Update YAML Config

Edit `frontend/public/config/suggestions.yaml`:

```yaml
suggestions:
  # ... existing suggestions ...
  
  - symbol: "$"
    name: "Tags"
    icon: "🏷️"
    provider: "tags"
    enabled: true
    trigger:
      pattern: "^\\$|\\s\\$"
      minChars: 0
    api:
      endpoint: "/api/tags/search"
      method: "GET"
      params:
        query: "{query}"
        limit: 10
    display:
      title: "Tags"
      itemTemplate: "{name}"
      metadata:
        - label: "Count"
          value: "{count}"
    keyboard:
      selectKey: "Enter"
      closeKey: "Escape"
      navigateKeys: ["ArrowUp", "ArrowDown"]
```

### Step 2: Create Backend API (if needed)

```python
@app.get("/api/tags/search")
async def search_tags(query: str = "", limit: int = 10):
    # Your search logic
    tags = db.query(Tag).filter(
        Tag.name.ilike(f"%{query}%")
    ).limit(limit).all()
    
    return {
        "results": [
            {"id": t.id, "name": t.name, "count": t.count}
            for t in tags
        ]
    }
```

### Step 3: Done!

The suggestion will automatically:
- ✅ Appear when user types `$`
- ✅ Search as user types
- ✅ Show formatted results
- ✅ Handle keyboard navigation
- ✅ Replace trigger on selection

## Configuration Reference

### Required Fields

- `symbol` - Trigger symbol (e.g., `@`, `#`, `$`)
- `name` - Display name
- `provider` - Unique identifier
- `enabled` - Enable/disable flag
- `trigger.pattern` - Regex to detect symbol
- `api.endpoint` - API endpoint URL
- `display.title` - Dropdown title
- `display.itemTemplate` - Template for items

### Optional Fields

- `description` - Description text
- `icon` - Emoji icon
- `trigger.minChars` - Minimum chars to trigger search
- `api.method` - HTTP method (default: GET)
- `api.params` - Query parameters
- `display.metadata` - Additional metadata fields
- `keyboard.*` - Keyboard shortcuts

## Template Variables

Use `{field_name}` in templates to reference API response fields:

```yaml
itemTemplate: "{username} ({role})"
metadata:
  - label: "Email"
    value: "{email}"
```

## API Response Format

The API should return one of:
- `{documents: [...]}` - Array in documents field
- `{results: [...]}` - Array in results field
- `[...]` - Direct array

Each item should have fields matching template variables.

## Examples

### Document Suggestions (Current)

```yaml
- symbol: "@"
  name: "Documents"
  api:
    endpoint: "/api/documents/search"
  display:
    itemTemplate: "{filename}"
```

### User Mentions (Example)

```yaml
- symbol: "#"
  name: "Users"
  api:
    endpoint: "/api/users/search"
  display:
    itemTemplate: "{username}"
    metadata:
      - label: "Role"
        value: "{role}"
```

### Tag Suggestions (Example)

```yaml
- symbol: "$"
  name: "Tags"
  api:
    endpoint: "/api/tags/search"
  display:
    itemTemplate: "{name}"
```

## Keyboard Navigation

All suggestions support:
- **↑/↓** - Navigate (configurable)
- **Enter** - Select (configurable)
- **Escape** - Close (configurable)

Configure in `keyboard` section of YAML.

## Troubleshooting

### Suggestions not appearing?
- Check `enabled: true` in YAML
- Verify trigger pattern matches your input
- Check browser console for API errors
- Ensure `minChars` requirement is met

### Wrong results displayed?
- Verify API response format matches template variables
- Check `itemTemplate` uses correct field names
- Ensure API endpoint returns expected data structure

### YAML not loading?
- System falls back to default config
- Check browser console for loading errors
- Verify YAML syntax is valid
- In production, ensure YAML is bundled/served

## Future Enhancements

Potential additions:
- Custom suggestion providers (plugins)
- Caching for better performance
- Multi-symbol triggers
- Rich formatting in suggestions
- Custom keyboard shortcuts per type

