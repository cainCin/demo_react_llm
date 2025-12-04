# UML Diagram Viewing Guide

## 📊 Database Architecture UML Diagram

The database architecture is documented in `UML_DIAGRAM.puml` using PlantUML syntax.

## 🖼️ Viewing the Diagram

### Option 1: Online Viewer (Easiest)

1. Copy the contents of `UML_DIAGRAM.puml`
2. Go to http://www.plantuml.com/plantuml/uml/
3. Paste the PlantUML code
4. The diagram will render automatically

### Option 2: PlantUML Command Line

```bash
# Install PlantUML (requires Java)
# On Ubuntu/Debian:
sudo apt-get install plantuml

# On macOS:
brew install plantuml

# Generate PNG
plantuml UML_DIAGRAM.puml

# Generate SVG
plantuml -tsvg UML_DIAGRAM.puml

# Generate PDF
plantuml -tpdf UML_DIAGRAM.puml
```

### Option 3: VS Code Extension

1. Install "PlantUML" extension in VS Code
2. Open `UML_DIAGRAM.puml`
3. Press `Alt+D` (or `Cmd+D` on Mac) to preview
4. Right-click → "Export Current Diagram" to save as image

### Option 4: IntelliJ IDEA / PyCharm

1. Install "PlantUML integration" plugin
2. Open `UML_DIAGRAM.puml`
3. Right-click → "PlantUML" → "Generate Diagram"

## 📋 Diagram Contents

The UML diagram shows:

### Classes

1. **DatabaseManager** (Purple)
   - Core database management class
   - Handles PostgreSQL and Milvus operations
   - Manages synchronization

2. **PostgreSQL ORM Models** (Blue)
   - `Document`: Document metadata and full text
   - `Chunk`: Text chunks with indexing

3. **Milvus Lite Collection** (Teal)
   - Vector storage schema
   - Embeddings only (no text)

4. **Data Classes** (Orange)
   - `DocumentData`: Complete document info
   - `ChunkData`: Chunk information
   - `VectorData`: Milvus vector data
   - `SearchResult`: Composite search results
   - `VerificationResult`: Verification status
   - `ResyncResult`: Resync operation results
   - `DocumentListItem`: Lightweight document list item

### Relationships

- **Document → Chunk**: One-to-many relationship
- **Data Classes → ORM Models**: `from_orm()` conversion
- **DatabaseManager → Databases**: Management and operations
- **VectorData → Milvus**: Insertion relationship
- **SearchResult → Both DBs**: Composite from Milvus + PostgreSQL

### Notes

- Text storage separation (PostgreSQL only)
- UUID to int64 conversion for Milvus
- Synchronization requirements
- Data flow patterns

## 🎨 Color Coding

- **Blue (POSTGRES_COLOR)**: PostgreSQL ORM models
- **Teal (MILVUS_COLOR)**: Milvus Lite collection
- **Orange (DATACLASS_COLOR)**: Data classes
- **Purple (MANAGER_COLOR)**: DatabaseManager

## 📝 Diagram Legend

- `<<ORM>>`: SQLAlchemy ORM model
- `<<DataClass>>`: Python dataclass
- `<<Collection>>`: Milvus collection
- `<<Manager>>`: Management class
- `[PK]`: Primary key
- `[FK]`: Foreign key
- `[INDEX]`: Indexed field
- `[UNIQUE]`: Unique constraint

## 🔄 Updating the Diagram

When making changes to the database structure:

1. Update the relevant ORM models in `database_manager.py`
2. Update corresponding data classes in `models.py`
3. Update the UML diagram in `UML_DIAGRAM.puml`
4. Regenerate the diagram image
5. Update `SYNCHRONIZATION_REPORT.md` if needed

## 📚 Related Documentation

- [README.md](README.md) - Package overview
- [SYNCHRONIZATION_REPORT.md](SYNCHRONIZATION_REPORT.md) - Field mapping verification
- [DATA_CLASSES.md](DATA_CLASSES.md) - Data class reference

