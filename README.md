# RAG MCP Server

A RAG (Retrieval-Augmented Generation) ingestion and retrieval service that acts as an MCP backend for GitHub Copilot (or any MCP-compatible client).

The service handles **ingestion** (scraping, chunking, embedding, storing in pgvector) and **retrieval** (hybrid vector + keyword search). Generation is delegated to Copilot via the MCP pass-through.

---

## How It Works

```
You (in Copilot)
  └── asks a question
       └── .mcp.json routes to kbsearch-mcp-server
            └── MCP server calls POST /query?retrieve_only=true
                 └── RAG service returns ranked chunks with citations
                      └── Copilot synthesizes the answer
```

The `default` profile uses the `mcp` provider — the RAG service returns raw chunks and Copilot handles generation.

---

## Quick Start

```bash
# 1. Start the RAG service
docker-compose up -d

# 2. Copy and configure environment
cp .env.template .env

# 3. Ingest a knowledge source
python cli.py ringest https://your-docs-url.com 2 50

# 4. Query (retrieval only — for MCP)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I configure X?", "retrieve_only": true, "profile": "default"}'
```

---

## MCP Configuration

`.mcp.json` wires Copilot to the local `kbsearch-mcp-server`, which calls this service's `/query` endpoint with `retrieve_only: true`.

```json
{
  "servers": {
    "local-kbsearch-server": {
      "command": "/path/to/kbsearch-mcp-server/.venv/bin/python",
      "args": ["/path/to/kbsearch-mcp-server/server.py"],
      "type": "stdio"
    }
  }
}
```

---

## API Endpoints

### `POST /ingest`
Scrape and embed a URL into the knowledge base.

```json
{
  "url": "https://docs.example.com",
  "depth": 2,
  "max_pages": 50,
  "profile": "default"
}
```

### `POST /query`
Retrieve relevant chunks. Use `retrieve_only: true` for MCP pass-through.

```json
{
  "query": "How do I configure X?",
  "top_k": 5,
  "retrieve_only": true,
  "profile": "default"
}
```

Returns chunks with citations and relevance scores for Copilot to synthesize.

### `POST /feedback`
Submit feedback (0–10) on a query response to improve future retrieval.

### `GET /metrics`
View retrieval latency, chunk scores, and feedback statistics.

---

## Profiles

| Profile | Description |
|---|---|
| `default` | MCP pass-through — retrieval only, Copilot generates |
| `copilot-gpt4o` | Copilot API handles full RAG + generation |

---

## CLI

```bash
python cli.py health                          # Check service health
python cli.py ingest <url>                    # Ingest a single page
python cli.py ringest <url> <depth> <pages>   # Recursive ingestion
python cli.py query "<question>"              # Query the knowledge base
python cli.py feedback <query_id> <0-10>      # Submit feedback
python cli.py metrics                         # View metrics
python cli.py profiles                        # List profiles
```

---

## Infrastructure

```bash
docker-compose up -d    # Start postgres + api
docker-compose down     # Stop
docker-compose logs -f api  # View API logs
```

Services:
- `postgres` — PostgreSQL 16 with pgvector (port 5434)
- `api` — FastAPI service (port 8000)
