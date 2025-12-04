# Quick Start Guide

## 🚀 Quick Setup

```bash
# 1. Setup PostgreSQL
cd backend
bash setup_databases.sh

# 2. Verify databases
python database/verify_databases.py

# 3. Export to CSV
python database/verify_databases.py -o report.csv
```

## 📋 Common Commands

### Verification
```bash
# Console output only
python database/verify_databases.py --no-export

# Export to CSV
python database/verify_databases.py -o my_report.csv
```

### API Calls (curl)

```bash
# List all documents
curl http://localhost:8000/api/documents

# Check synchronization
curl http://localhost:8000/api/documents/sync

# Resynchronize databases
curl -X POST http://localhost:8000/api/documents/resync

# Delete a document
curl -X DELETE http://localhost:8000/api/documents/{document_id}

# Clean all databases
curl -X DELETE http://localhost:8000/api/documents
```

### Python Usage

```python
from database import DatabaseManager

# Initialize
db = DatabaseManager()
db.initialize()

# Verify
result = db.verify()
print(f"Synchronized: {result['synchronized']}")

# Clean
db.clean_all()
```

## 🔍 Troubleshooting

```bash
# PostgreSQL not running?
docker start chatbox-postgres

# Check status
docker ps -a --filter 'name=chatbox-postgres'

# View logs
docker logs chatbox-postgres
```

For more details, see [README.md](README.md)

