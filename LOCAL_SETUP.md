# RAG Testing Pipeline - Local Setup Guide

This guide is for users who already have **PostgreSQL** and **Ollama** running locally.

---

## 🎯 Overview

Since you have PostgreSQL and Ollama installed locally, we'll configure the project to use your existing services instead of Docker containers. **Only the API will run in Docker**, connecting to your local services.

---

## ✅ Prerequisites

Before starting, ensure you have:

### 1. PostgreSQL Running
```bash
# Check if PostgreSQL is running
psql -h localhost -U postgres -c "SELECT 1"

# If not running, start it:
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux
```

### 2. PostgreSQL with pgvector Extension
```bash
# Check if pgvector is available
psql -U postgres -c "SELECT * FROM pg_available_extensions WHERE name = 'vector'"

# If not installed:
brew install pgvector  # macOS
# OR
sudo apt-get install postgresql-16-pgvector  # Ubuntu/Debian
```

### 3. Ollama Running
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve

# Pull llama3.2 model
ollama pull llama3.2
```

### 4. Docker
```bash
# Check Docker
docker --version

# If not installed: https://docs.docker.com/get-docker/
```

---

## 🚀 Setup (3 steps)

### Step 1: Run Setup Script

```bash
cd rag-testing
./setup-local.sh
```

This will:
- Create `.env` configuration file
- Check that PostgreSQL and Ollama are accessible
- Create database and user (`rag_testing` / `testuser`)
- Run `db/init.sql` to set up schema with pgvector
- Verify llama3.2 model is available

### Step 2: Review Configuration (Optional)

Check `.env` file if you need custom settings:

```bash
# Database connection (should match your local PostgreSQL)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rag_testing
POSTGRES_USER=testuser
POSTGRES_PASSWORD=changeme

# Ollama connection (should match your local Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### Step 3: Start API

```bash
./start-local.sh
```

This will:
- Verify PostgreSQL and Ollama are running
- Build the API Docker image
- Start the API container (connects to your local services via `host.docker.internal`)

---

## ✅ Verify Setup

```bash
# Check API health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs
```

---

## 📊 Architecture

```
┌─────────────────────────────────────┐
│         Your Local Machine          │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │ PostgreSQL   │  │   Ollama    │ │
│  │ (port 5432)  │  │ (port 11434)│ │
│  └──────▲───────┘  └──────▲──────┘ │
│         │                  │        │
│         │  host.docker.internal     │
│         │                  │        │
│  ┌──────┴──────────────────┴──────┐ │
│  │   API Container (port 8000)    │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Key Points:**
- PostgreSQL and Ollama run **natively** on your machine
- API runs in **Docker container** but connects to host services
- Uses `host.docker.internal` to reach host machine from container

---

## 📝 Test the Pipeline

### 1. Ingest a Document

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.python.org/3/tutorial/venv.html"
  }'
```

### 2. Query the Knowledge Base

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I create a Python virtual environment?"
  }'
```

### 3. Submit Feedback

```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "<from query response>",
    "score": 9
  }'
```

### 4. View Metrics

```bash
curl http://localhost:8000/metrics
```

---

## 🔧 Common Commands

```bash
# View API logs
docker-compose logs -f api

# Restart API
docker-compose restart api

# Stop API
docker-compose stop api

# Rebuild API (after code changes)
docker-compose build api
docker-compose up -d api

# Connect to PostgreSQL
psql -h localhost -U testuser -d rag_testing

# Check Ollama models
ollama list

# Check Ollama status
curl http://localhost:11434/api/tags
```

---

## 🐛 Troubleshooting

### API can't connect to PostgreSQL

**Error**: `connection refused` or `could not connect to server`

**Solution**:
1. Check PostgreSQL is running:
   ```bash
   pg_isready -h localhost -p 5432
   ```

2. Check PostgreSQL accepts connections from Docker:
   ```bash
   # Edit postgresql.conf
   listen_addresses = '*'  # or 'localhost, 127.0.0.1'

   # Edit pg_hba.conf to allow connections
   host    all    all    172.17.0.0/16    md5

   # Restart PostgreSQL
   brew services restart postgresql
   ```

3. Verify database exists:
   ```bash
   psql -U postgres -c "\l" | grep rag_testing
   ```

### API can't connect to Ollama

**Error**: `Connection refused to localhost:11434`

**Solution**:
1. Check Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Start Ollama if needed:
   ```bash
   ollama serve
   ```

3. Check firewall isn't blocking port 11434

### pgvector extension not found

**Error**: `extension "vector" does not exist`

**Solution**:
```bash
# Install pgvector
brew install pgvector  # macOS

# Or from source
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make && sudo make install

# Then re-run setup
./setup-local.sh
```

### Model not found

**Error**: `model "llama3.2" not found`

**Solution**:
```bash
ollama pull llama3.2
```

---

## 💡 Benefits of Local Setup

✅ **Faster** - No Docker overhead for PostgreSQL/Ollama
✅ **Familiar** - Use your existing local tools
✅ **Persistent** - Data survives container restarts
✅ **Debugging** - Easy access to logs and database
✅ **Resource-efficient** - One less layer of containerization

---

## 🔄 Switch to Full Docker Setup

If you want to switch to running everything in Docker:

1. Stop local services (optional):
   ```bash
   brew services stop postgresql
   brew services stop ollama
   ```

2. Uncomment services in `docker-compose.yml`:
   - Uncomment `postgres` service
   - Uncomment `ollama` service

3. Update API environment:
   ```yaml
   - POSTGRES_HOST=postgres  # instead of host.docker.internal
   - OLLAMA_BASE_URL=http://ollama:11434
   ```

4. Run full Docker setup:
   ```bash
   ./setup.sh
   ./start.sh
   ```

---

## 📚 Next Steps

1. **Ingest documents** - Build your knowledge base
2. **Test queries** - Verify search and generation work
3. **Submit feedback** - Improve quality through boosting
4. **Monitor metrics** - Track performance and costs
5. **Read docs** - Explore advanced features in [docs/](docs/)

---

**Ready to go!** 🚀

Start with `./setup-local.sh` and `./start-local.sh`
