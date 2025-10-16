# Perplexity OSS - Powered by Lyzr AI

![Perplexity OSS Logo](https://lyzr.ai/favicon.ico)

A self-hosted, open-source AI-powered search engine that combines the power of web search with advanced language models through specialized Lyzr Agents. Get accurate, real-time answers with source citations - all running on your own infrastructure.

## ✨ Features

- 🔍 **Intelligent Search**: Web search powered by SearXNG with AI-enhanced results
- 🤖 **Lyzr Agent Integration**: Specialized AI agents for query processing, search, and response generation
- 💬 **Conversational Interface**: Natural language chat with context awareness
- 🔗 **Source Citations**: Every answer includes links to original sources
- ⚡ **Real-time Streaming**: Live response streaming for immediate feedback
- 🎯 **Pro Search Mode**: Advanced multi-step reasoning for complex queries
- 🐳 **One-Command Deployment**: Complete Docker setup with docker-compose
- 🎨 **Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS

## 🛠️ Tech Stack

- **Backend**: FastAPI with Python 3.11
- **Frontend**: Next.js 14 with TypeScript
- **Search Engine**: SearXNG
- **AI Platform**: Lyzr Agent Studio
- **Containerization**: Docker & Docker Compose
- **Package Management**: uv (Python), npm (Node.js)

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Lyzr Agent Studio account and API key
- At least 4GB RAM available for containers

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd perplexity_oss
```

### 2. Get Your Lyzr API Key

1. Visit [Lyzr Agent Studio](https://studio.lyzr.ai)
2. Create an account or sign in
3. Get your API key from the dashboard

### 3. Configure Environment Variables

Create a `.env` file in the root directory with **just your API key**:

```bash
# Required: Lyzr API key
LYZR_API_KEY=your_actual_lyzr_api_key_here

# Optional: Feature Configuration
NEXT_PUBLIC_PRO_MODE_ENABLED=true
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**That's it!** The application will automatically create all required Lyzr agents on first startup. Agent IDs will be saved to persist across restarts.

<details>
<summary>📝 Advanced: Manual Agent Configuration (Optional)</summary>

If you prefer to create agents manually in Lyzr Studio:

1. Clone the Perplexity OSS blueprint in Lyzr Agent Studio
2. Copy each agent ID and add to your `.env` file:

```bash
LYZR_API_KEY=your_lyzr_api_key_here
LYZR_QUERY_REPHRASE_AGENT_ID=your_query_rephrase_agent_id
LYZR_ANSWER_GENERATION_AGENT_ID=your_answer_generation_agent_id
LYZR_RELATED_QUESTIONS_AGENT_ID=your_related_questions_agent_id
LYZR_QUERY_PLANNING_AGENT_ID=your_query_planning_agent_id
LYZR_SEARCH_QUERY_AGENT_ID=your_search_query_agent_id
```

See `.env.example` for all configuration options.
</details>

### 4. Launch the Application

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

This will start:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **SearXNG**: http://localhost:8080

### 5. Access the Application

Open your browser and navigate to http://localhost:3000

## 📖 Detailed Setup Guide

### Setting Up Lyzr Agents

#### Required Agent Types

Each agent should be configured in Lyzr Agent Studio with specific prompts and capabilities:

1. **Default Agent**
   - Purpose: General conversation and simple Q&A
   - Model: GPT-4 or equivalent
   - Instructions: "You are a helpful AI assistant that provides accurate and concise answers."

2. **Query Rephrase Agent**
   - Purpose: Reformulate queries with conversation context
   - Instructions: "Reformulate the user's query considering the conversation history to make it more searchable and specific."

3. **Answer Generation Agent**
   - Purpose: Generate comprehensive answers from search results
   - Instructions: "Generate detailed, accurate answers based on the provided search results. Include citations and maintain factual accuracy."

4. **Related Questions Agent**
   - Purpose: Generate follow-up questions
   - Instructions: "Generate 3 relevant follow-up questions based on the user's query and the provided answer."

5. **Query Planning Agent** (Pro Mode)
   - Purpose: Break down complex queries into steps
   - Instructions: "Analyze complex queries and break them down into logical search steps."

6. **Search Query Agent** (Pro Mode)
   - Purpose: Convert natural language to search queries
   - Instructions: "Convert natural language questions into effective search engine queries."

### Environment Variables Reference

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `LYZR_API_KEY` | ✅ | Your Lyzr Agent Studio API key | - |
| `LYZR_DEFAULT_AGENT_ID` | ✅ | ID for general chat agent | - |
| `LYZR_QUERY_REPHRASE_AGENT_ID` | ✅ | ID for query rephrasing agent | - |
| `LYZR_ANSWER_GENERATION_AGENT_ID` | ✅ | ID for answer generation agent | - |
| `LYZR_RELATED_QUESTIONS_AGENT_ID` | ✅ | ID for related questions agent | - |
| `LYZR_QUERY_PLANNING_AGENT_ID` | ⚠️ | ID for query planning agent (Pro mode) | - |
| `LYZR_SEARCH_QUERY_AGENT_ID` | ⚠️ | ID for search query agent (Pro mode) | - |
| `NEXT_PUBLIC_PRO_MODE_ENABLED` | ❌ | Enable advanced pro search features | `true` |
| `NEXT_PUBLIC_API_URL` | ❌ | Backend API URL for frontend | `http://localhost:8000` |
| `SEARXNG_BASE_URL` | ❌ | SearXNG instance URL | `http://searxng:8080` |

⚠️ = Required only if Pro Mode is enabled

### Development Setup

For development with hot reloading:

#### Backend Development
```bash
cd perplexity_oss/backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Development
```bash
cd perplexity_oss/frontend
npm install
npm run dev
```

#### SearXNG (Docker)
```bash
docker run -d --name searxng -p 8080:8080 searxng/searxng:latest
```

## 🔧 Configuration

### Customizing Search Behavior

Edit `perplexity_oss/backend/src/search/search_service.py` to:
- Modify search result limits
- Add custom result filtering
- Integrate additional search engines

### UI Customization

The frontend uses Tailwind CSS and shadcn/ui components:
- Colors: Edit `perplexity_oss/frontend/tailwind.config.js`
- Components: Modify files in `perplexity_oss/frontend/src/components/`
- Branding: Update `perplexity_oss/frontend/src/components/nav.tsx`

### Adding Search Providers

To add additional search engines beyond SearXNG:
1. Create a new provider in `perplexity_oss/backend/src/search/providers/`
2. Update `search_service.py` to include the new provider
3. Add configuration options to environment variables

## 🐳 Docker Configuration

### Custom Docker Setup

Modify `docker-compose.yml` for your needs:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - LYZR_API_KEY=${LYZR_API_KEY}
    volumes:
      - ./backend/src:/app/src  # For development
    
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    
  searxng:
    image: searxng/searxng:latest
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng  # Custom SearXNG config
```

### Production Deployment

For production deployment:

1. **Use environment-specific configs**:
   ```bash
   cp .env.example .env.production
   # Edit .env.production with production values
   docker-compose --env-file .env.production up -d
   ```

2. **Enable HTTPS** (recommended):
   ```yaml
   # Add to docker-compose.yml
   nginx:
     image: nginx:alpine
     ports:
       - "80:80"
       - "443:443"
     volumes:
       - ./nginx.conf:/etc/nginx/nginx.conf
       - ./ssl:/etc/ssl
   ```

3. **Resource limits**:
   ```yaml
   # Add to each service in docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 1G
         cpus: '0.5'
   ```

## 🔍 Usage

### Basic Search
1. Type your question in the search box
2. Press Enter or click the search button
3. View results with AI-generated answers and source citations

### Pro Search Mode
1. Toggle "Pro Search" in the interface
2. Ask complex, multi-step questions
3. Watch as the system breaks down your query into steps
4. Get comprehensive answers with detailed reasoning

### Example Queries
- "What are the latest developments in renewable energy?"
- "Compare the economic policies of major European countries"
- "Explain quantum computing and its potential applications"

## 🛠️ Troubleshooting

### Common Issues

1. **Backend fails to start**
   ```bash
   # Check logs
   docker-compose logs backend
   
   # Common fix: Verify environment variables
   docker-compose config
   ```

2. **Frontend build errors**
   ```bash
   # Clear cache and rebuild
   docker-compose down
   docker system prune -a
   docker-compose up --build
   ```

3. **Search not working**
   ```bash
   # Check SearXNG status
   curl http://localhost:8080/search?q=test
   
   # Restart SearXNG
   docker-compose restart searxng
   ```

4. **Lyzr API errors**
   - Verify your API key is correct
   - Check agent IDs match your Lyzr Studio setup
   - Ensure your Lyzr account has sufficient credits

### Performance Optimization

1. **Increase container resources**:
   ```bash
   # Edit docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 2G
         cpus: '1'
   ```

2. **Cache optimization**:
   - Enable Redis for caching (add to docker-compose.yml)
   - Configure SearXNG result caching

3. **Network optimization**:
   - Use a reverse proxy (nginx/traefik)
   - Enable HTTP/2 and compression

## 🏗️ Architecture

### Services

- **Frontend** (Next.js): Modern React-based web interface with TypeScript
- **Backend** (FastAPI): High-performance API server with Lyzr AI integration
- **SearXNG**: Privacy-focused, self-hosted search engine for web results

### Project Structure

```
perplexity_oss/
├── backend/
│   ├── src/
│   │   ├── main.py           # FastAPI application
│   │   ├── chat.py           # Chat logic and streaming
│   │   ├── agent_search.py   # Pro search with query planning
│   │   ├── llm/
│   │   │   └── lyzr_agent.py # Lyzr AI integration
│   │   ├── search/           # Search providers
│   │   │   ├── search_service.py
│   │   │   └── providers/
│   │   │       └── searxng.py
│   │   ├── schemas.py        # Pydantic models
│   │   └── prompts.py        # Agent prompts
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js app router
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── stores/           # Zustand state management
│   │   └── generated/        # API client (auto-generated)
│   ├── Dockerfile
│   └── package.json
├── searxng/                  # Search engine configuration
│   ├── settings.yml
│   └── uwsgi.ini
├── docker-compose.yml
└── README.md
```

### Lyzr Agents Integration

The system uses specialized Lyzr agents for different tasks:

- **Default Agent**: Main conversation and answer generation
- **Query Rephrase Agent**: Improves queries using conversation history
- **Answer Generation Agent**: Specialized for creating comprehensive answers from search results
- **Related Questions Agent**: Generates relevant follow-up questions
- **Query Planning Agent**: Plans complex multi-step queries (Pro mode)
- **Search Query Agent**: Optimizes search queries for better results (Pro mode)

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit with descriptive messages: `git commit -m 'Add amazing feature'`
5. Push to your branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Development Guidelines

- Follow Python PEP 8 for backend code
- Use TypeScript and follow React best practices for frontend
- Add tests for new features
- Update documentation for any API changes
- Ensure Docker builds work correctly

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Lyzr AI](https://lyzr.ai) for providing the agent platform
- [SearXNG](https://github.com/searxng/searxng) for the search engine
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Next.js](https://nextjs.org/) for the frontend framework
- The open-source community for inspiration and tools

## 📞 Support

- 📧 Issues: Create an issue on GitHub
- 💬 Discussions: Use GitHub Discussions for questions
- 🌐 Lyzr Support: Visit [Lyzr Agent Studio](https://studio.lyzr.ai) for agent-related questions

---

**Made with ❤️ using Lyzr AI Agents**