# Perplexity OSS

An open-source, self-hosted AI search engine that combines web search with Amazon Bedrock's Nova language models through specialized Lyzr AI agents. Delivers accurate, citation-backed answers with sophisticated multi-agent orchestration.


## Overview

Perplexity OSS provides intelligent search responses by analyzing web results through Amazon Nova models. The system uses five specialized AI agents, each powered by either Nova Pro (for complex reasoning) or Nova Lite (for efficient query processing), to deliver contextual answers with full source attribution.

**Key Features:**
- **Amazon Nova Models**: Leverages Bedrock's Nova Pro for answer generation and Nova Lite for query processing
- **Multi-Agent Architecture**: Five specialized agents work in concert for optimal results
- **Pro Search Mode**: Multi-step reasoning that breaks complex queries into logical steps
- **Privacy-First**: Self-hosted SearXNG ensures no tracking during web searches
- **OpenAI-Compatible API**: Drop-in replacement for chat completion endpoints
- **Auto-Configuration**: Agents automatically created and configured on first startup


## Architecture

### System Components

Three containerized services orchestrated via Docker Compose:

<!-- ```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Frontend      │─────▶│    Backend       │─────▶│    SearXNG      │
│   (Next.js 14)  │      │    (FastAPI)     │      │  (Search Engine)│
│   Port 3003     │◀─────│   Port 8003      │◀─────│   Port 8083     │
└─────────────────┘      └──────────────────┘      └─────────────────┘
``` -->
<img width="512" alt="image" src="https://github.com/user-attachments/assets/c487186b-499b-4a01-91d2-3ee80529e3c6" />


- **Frontend**: React interface with TypeScript, Tailwind CSS, real-time streaming support
- **Backend**: FastAPI server orchestrating Lyzr agents powered by Amazon Bedrock Nova models
- **SearXNG**: Privacy-respecting meta-search engine (no tracking, no data collection)

### Agent System

Five specialized Lyzr AI agents, each configured in `backend/src/llm/agent_config.py`:

**1. Answer Generation Agent**
- **Model**: `bedrock/amazon.nova-pro-v1:0` (most capable Nova model)
- **Purpose**: Synthesizes search results into comprehensive, citation-backed answers
- **Behavior**: Always cites sources in `[[n]](url)` format, maintains journalistic tone
- **Temperature**: 0.7 for balanced creativity and accuracy
- **Provider**: AWS Bedrock via Lyzr credential `lyzr_aws-bedrock`

**2. Query Rephrase Agent**
- **Model**: `bedrock/amazon.nova-lite-v1:0` (cost-effective)
- **Purpose**: Reformulates queries with conversation context
- **Behavior**: Creates concise, standalone queries from conversational follow-ups
- **Used in**: Both simple and pro search modes

**3. Related Questions Agent**
- **Model**: `bedrock/amazon.nova-lite-v1:0`
- **Purpose**: Generates three relevant follow-up questions
- **Behavior**: Creates simple, concise questions matching user's language
- **Output**: Three numbered questions based on answer and search context

**4. Query Planning Agent** (Pro Mode)
- **Model**: `bedrock/amazon.nova-lite-v1:0`
- **Purpose**: Decomposes complex queries into logical search steps
- **Response Format**: Strict JSON Schema with step IDs and dependencies
- **Constraints**: Max 4 steps, supports dependency tracking
- **Example**: "Compare X and Y" → [Research X, Research Y, Compare findings]

**5. Search Query Agent** (Pro Mode)
- **Model**: `bedrock/amazon.nova-lite-v1:0`
- **Purpose**: Generates optimized search queries for each planning step
- **Behavior**: Creates 1-3 targeted queries per step, incorporates previous step context
- **Response Format**: JSON array of search queries

**Agent Auto-Creation:**

On first startup, the system automatically creates agents via Lyzr Agent Studio API:

1. Checks environment variables for agent IDs
2. Checks `/app/config/agents.json` (Docker volume)
3. If not found, creates agents using configurations from `agent_config.py`
4. Persists IDs to `agents.json` for future runs
5. File locking prevents duplicate creation

**Implementation**: `backend/src/config/agent_manager.py`

### Search Modes

**Simple Mode** (default):
<img width="1493" height="1033" alt="image" src="https://github.com/user-attachments/assets/7188656e-db37-43e4-9184-2d0a0e40f264" />
```
Query → Rephrase → Web Search → Answer Generation → Related Questions
```

- Single SearXNG search retrieves top 6 results
- Nova Pro streams answer with citations
- Nova Lite generates follow-up questions (parallel)

**Pro Search Mode**:
<img width="1260" height="1662" alt="image" src="https://github.com/user-attachments/assets/3ced9af0-0b88-497e-95a5-3dc57504bf0f" />
```
Query → Query Planning → Step Execution Loop → Answer Synthesis
```
1. Nova Lite breaks query into logical steps (max 4)
2. For each step: Generate search queries → Execute searches → Store results
3. Final step: Aggregate results → Nova Pro synthesizes comprehensive answer
4. Fallback: Gracefully falls back to simple mode if planning fails

**Context Management:**
- Simple mode: 7,000 character limit
- Pro mode: 10,000 character total limit


## Quick Start

### Prerequisites

- Docker and Docker Compose
- Lyzr Agent Studio API key ([Get one](https://studio.lyzr.ai))

### Installation

1. **Clone repository**
   ```bash
   git clone https://github.com/your-username/perplexity_oss.git
   cd perplexity_oss
   ```

2. **Configure environment**

   Create `.env` file:
   ```bash
   # Required
   LYZR_API_KEY=your_lyzr_api_key_here

   # Optional
   API_KEYS=sk-your-custom-key
   NEXT_PUBLIC_PRO_MODE_ENABLED=true
   ```

3. **Launch**
   ```bash
   docker-compose up --build
   ```

   First startup takes ~2 minutes to build and create agents.

4. **Access**
   - Web UI: http://localhost:3003
   - API: http://localhost:8003
   - API Docs: http://localhost:8003/docs

### Verification

```bash
# Check services
docker-compose ps

# View agent initialization
docker-compose logs backend | grep "agents initialized"
```

Expected: `✅ All agents initialized successfully!`


## Environment Configuration

### Required

| Variable | Description |
|----------|-------------|
| `LYZR_API_KEY` | Lyzr Agent Studio API key (provides Bedrock access) |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEYS` | - | Comma-separated API keys for REST endpoints |
| `NEXT_PUBLIC_PRO_MODE_ENABLED` | `true` | Enable multi-step search mode |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL for frontend |
| `LYZR_API_BASE` | `https://agent-prod.studio.lyzr.ai` | Lyzr API endpoint |

### Manual Agent Configuration (Advanced)

To use pre-created agents from Lyzr Studio:

```bash
LYZR_QUERY_REPHRASE_AGENT_ID=agent_id_1
LYZR_ANSWER_GENERATION_AGENT_ID=agent_id_2
LYZR_RELATED_QUESTIONS_AGENT_ID=agent_id_3
LYZR_QUERY_PLANNING_AGENT_ID=agent_id_4
LYZR_SEARCH_QUERY_AGENT_ID=agent_id_5
```


## REST API

OpenAI-compatible endpoints for programmatic access.

### Authentication

Set in `.env`:
```bash
API_KEYS=sk-your-secret-key
```

Include in requests:
```bash
Authorization: Bearer sk-your-secret-key
```

### Chat Completions

`POST /v1/chat/completions`

**Basic:**
```bash
curl http://localhost:8003/v1/chat/completions \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "messages": [{"role": "user", "content": "Explain quantum computing"}]
  }'
```

**Advanced:**
```bash
curl http://localhost:8003/v1/chat/completions \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "messages": [{"role": "user", "content": "Latest AI developments"}],
    "stream": true,
    "pro_search": true,
    "search_recency_filter": "week",
    "search_domain_filter": ["arxiv.org"],
    "return_related_questions": true
  }'
```

**Parameters:**
- `stream`: Enable SSE streaming
- `pro_search`: Use multi-step query planning
- `search_recency_filter`: `"day"`, `"week"`, `"month"`, `"year"`
- `search_domain_filter`: Array of domains to search
- `return_related_questions`: Include follow-up questions
- `return_images`: Include image URLs
- `max_results`: Number of results (1-20, default: 6)

### Search-Only Endpoint

`POST /v1/search`

```bash
curl http://localhost:8003/v1/search \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning papers",
    "max_results": 10,
    "search_domain_filter": ["arxiv.org"]
  }'
```

**See [API.md](API.md) for complete documentation**


## Production Deployment

### Custom Ports

Edit `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "8080:8000"
  frontend:
    ports:
      - "80:3000"
```

### Resource Limits

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1'
```

### HTTPS Setup

nginx reverse proxy example:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3003;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }

    location /api {
        proxy_pass http://localhost:8003;
        proxy_buffering off;  # Important for SSE
    }
}
```

### Persistent Configuration

Agent IDs persist via Docker volume:

```bash
# View saved agent IDs
docker exec backend-1 cat /app/config/agents.json

# Backup
docker cp backend-1:/app/config/agents.json ./backup.json

# Reset and recreate
docker-compose down -v
docker-compose up --build
```

## Development

### Backend

```bash
cd backend
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
cd src
uvicorn main:app --reload --port 8000
```

Environment:
```bash
export LYZR_API_KEY=your_key
export SEARXNG_BASE_URL=http://localhost:8080
```

### Frontend

```bash
cd frontend
npm install
npm run dev  # http://localhost:3000
```

### Modifying Agents

Edit `backend/src/llm/agent_config.py`:

```python
ANSWER_GENERATION_AGENT = {
    "model": "bedrock/amazon.nova-pro-v1:0",
    "temperature": "0.7",  # Adjust
    "agent_instructions": "...",  # Modify
}
```

Recreate agents:
```bash
docker exec backend-1 rm /app/config/agents.json
docker-compose restart backend
```


## Troubleshooting

### Agent Creation Fails

**Error**: "Could not initialize agents"

**Solutions**:
- Verify `LYZR_API_KEY` is correct
- Check Bedrock access in Lyzr Studio
- Review logs: `docker-compose logs backend | grep agent`

### Search Not Working

**Solutions**:
- Check SearXNG: `curl http://localhost:8083`
- Restart: `docker-compose restart searxng`
- View logs: `docker-compose logs searxng`

### API Returns 503

**Error**: "API keys not configured"

**Solutions**:
- Add `API_KEYS` to `.env`
- Restart: `docker-compose restart backend`
- Verify: `docker-compose config | grep API_KEYS`

### Pro Search Fallback

Check why pro search fell back to simple mode:
```bash
docker-compose logs backend | grep "Pro search failed"
```

Common causes:
- Query Planning Agent JSON parsing failure
- Network timeout to Lyzr API
- System automatically falls back to ensure response


## Technical Stack

**Backend:**
- FastAPI (Python 3.11)
- Amazon Bedrock (Nova Pro v1.0, Nova Lite v1.0)
- Lyzr Agent Studio
- Pydantic v2, httpx (async)
- Package manager: uv

**Frontend:**
- Next.js 14 (App Router)
- TypeScript, Tailwind CSS v4
- shadcn/ui components
- Zustand state management

**Infrastructure:**
- SearXNG (privacy-focused search)
- Docker & Docker Compose
- Server-Sent Events (SSE streaming)

**AWS Services:**
- Amazon Bedrock (via Lyzr)
- Bedrock AgentCore primitives
- AWS credentials managed by Lyzr


## Project Structure

```
perplexity_oss/
├── backend/
│   ├── src/
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── chat.py                 # Simple search mode
│   │   ├── agent_search.py         # Pro search mode
│   │   ├── llm/
│   │   │   ├── lyzr_agent.py       # Agent client & streaming
│   │   │   └── agent_config.py     # Nova model configs
│   │   ├── config/
│   │   │   └── agent_manager.py    # Auto-creation logic
│   │   ├── search/
│   │   │   ├── search_service.py   # Search orchestration
│   │   │   └── providers/searxng.py
│   │   ├── api_compat/             # OpenAI compatibility
│   │   ├── schemas.py              # Data models
│   │   └── prompts.py              # Agent prompts
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js routes
│   │   ├── components/             # React components
│   │   ├── contexts/AuthContext.tsx
│   │   └── hooks/chat.ts
│   └── package.json
├── docker-compose.yml
└── .env.example
```

## License

MIT License - see [LICENSE](LICENSE)

## Documentation

- **API Reference**: [API.md](API.md)
- **Issues**: [GitHub Issues](https://github.com/LyzrCore/perplexity_oss/issues)
- **Lyzr Support**: [studio.lyzr.ai](https://studio.lyzr.ai)
