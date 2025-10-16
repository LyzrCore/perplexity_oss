# Perplexity OSS

An open-source AI-powered search engine that combines web search with language models to provide accurate answers with source citations. Self-hosted and powered by Lyzr AI agents.

## Overview

Perplexity OSS delivers intelligent search responses by:
- Searching the web using SearXNG
- Processing results through specialized AI agents
- Generating comprehensive answers with citations
- Supporting conversational follow-ups with context awareness

**Key Features:**
- Real-time streaming responses
- Source citations for transparency
- Pro mode with multi-step reasoning for complex queries
- OpenAI-compatible REST API
- Complete Docker setup for easy deployment

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Lyzr Agent Studio API key ([Get one here](https://studio.lyzr.ai))

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd perplexity_oss
   ```

2. **Configure environment**

   Create a `.env` file with your Lyzr API key:
   ```bash
   LYZR_API_KEY=your_api_key_here
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Access the interface**
   - Web UI: http://localhost:3003
   - Backend API: http://localhost:8003
   - API Docs: http://localhost:8003/docs

**First Run:** The application automatically creates required AI agents on startup. Agent configurations are saved and reused on subsequent runs.

## Environment Configuration

### Required Variables

| Variable | Description |
|----------|-------------|
| `LYZR_API_KEY` | Your Lyzr Agent Studio API key |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEYS` | - | Comma-separated API keys for REST endpoints |
| `NEXT_PUBLIC_PRO_MODE_ENABLED` | `true` | Enable advanced pro search mode |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL for frontend |
| `LYZR_API_BASE` | `https://agent-prod.studio.lyzr.ai` | Lyzr API endpoint |

### Advanced: Manual Agent Configuration

By default, agents are created automatically. To use manually created agents, add these to your `.env`:

```bash
LYZR_QUERY_REPHRASE_AGENT_ID=agent_id_1
LYZR_ANSWER_GENERATION_AGENT_ID=agent_id_2
LYZR_RELATED_QUESTIONS_AGENT_ID=agent_id_3
LYZR_QUERY_PLANNING_AGENT_ID=agent_id_4
LYZR_SEARCH_QUERY_AGENT_ID=agent_id_5
```

See `.env.example` for all available options.

## Using the REST API

Perplexity OSS provides OpenAI-compatible endpoints for programmatic access.

### Authentication

Set API keys in your `.env` file:
```bash
API_KEYS=sk-your-key-1,sk-your-key-2
```

### Chat Completions

```bash
curl http://localhost:8003/v1/chat/completions \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "messages": [
      {"role": "user", "content": "What is quantum computing?"}
    ],
    "stream": false,
    "search_domain_filter": ["arxiv.org"],
    "search_recency_filter": "week",
    "return_related_questions": true
  }'
```

**Parameters:**
- `stream` (boolean): Enable streaming responses
- `search_domain_filter` (array): Limit search to specific domains
- `search_recency_filter` (string): Filter by time - "day", "week", "month", "year"
- `pro_search` (boolean): Enable multi-step reasoning
- `return_related_questions` (boolean): Include follow-up questions
- `return_images` (boolean): Include image results

### Search Only

For search results without AI-generated answers:

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

**Full API documentation:** See [API.md](API.md) for complete endpoint reference and examples.

## Architecture

### Components

**Frontend (Next.js 14)**
- Modern React interface with TypeScript
- Real-time streaming support
- Responsive design with Tailwind CSS

**Backend (FastAPI)**
- RESTful API with OpenAI compatibility
- Lyzr AI agent orchestration
- Streaming response handling

**Search (SearXNG)**
- Privacy-focused web search
- No tracking or data collection
- Configurable search sources

### Agent System

The application uses specialized Lyzr agents for different tasks:

- **Query Rephrase:** Reformulates queries using conversation context
- **Answer Generation:** Creates comprehensive answers from search results
- **Related Questions:** Generates relevant follow-up questions
- **Query Planning:** Breaks complex queries into logical steps (Pro mode)
- **Search Query:** Optimizes search queries for better results (Pro mode)

## Production Deployment

### Using Custom Ports

Edit `docker-compose.yml` to change default ports:

```yaml
services:
  backend:
    ports:
      - "8080:8000"  # Custom backend port

  frontend:
    ports:
      - "3000:3000"  # Custom frontend port
```

### Resource Limits

Add resource constraints for production:

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

Use a reverse proxy (nginx, Caddy, or Traefik) for HTTPS:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3003;
    }

    location /api {
        proxy_pass http://localhost:8003;
    }
}
```

## Troubleshooting

### Agent Creation Fails

**Problem:** "Could not initialize agents" error on startup

**Solutions:**
1. Verify your `LYZR_API_KEY` is correct
2. Check internet connectivity
3. Ensure Lyzr API endpoint is accessible
4. Try manual agent creation in Lyzr Studio

### Search Not Working

**Problem:** No search results returned

**Solutions:**
1. Check SearXNG is running: `docker-compose ps`
2. Test SearXNG directly: http://localhost:8083
3. Restart SearXNG: `docker-compose restart searxng`

### API Endpoint Returns 503

**Problem:** "API keys not configured on server"

**Solutions:**
1. Verify `API_KEYS` is set in `.env`
2. Restart containers: `docker-compose restart`
3. Check environment passed correctly: `docker-compose config`

### Pro Search Fails

Pro search automatically falls back to regular search if query planning fails. Check logs for warnings:

```bash
docker-compose logs backend | grep "Pro search failed"
```

## Development

### Backend Development

```bash
cd backend
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
cd src
uvicorn main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Tech Stack

- **Backend:** FastAPI, Python 3.11, Pydantic, httpx
- **Frontend:** Next.js 14, React, TypeScript, Tailwind CSS
- **Search:** SearXNG
- **AI:** Lyzr Agent Studio
- **Infrastructure:** Docker, Docker Compose

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Issues:** [GitHub Issues](https://github.com/your-repo/issues)
- **Lyzr Support:** [studio.lyzr.ai](https://studio.lyzr.ai)
- **Documentation:** See [API.md](API.md) and [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

Built with Lyzr AI Agents
