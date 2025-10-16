# API Documentation - Perplexity OSS

## Overview

Perplexity OSS provides OpenAI-compatible REST endpoints at `/v1/*` that allow external applications to use this as a drop-in replacement for chat completion APIs.

**Base URL:** `http://localhost:8003/v1` (adjust port/domain for your deployment)

## Authentication

All API endpoints require Bearer token authentication.

### Setup

1. Add API key(s) to your `.env` file:
   ```bash
   API_KEYS=sk-your-secret-key-here
   ```

2. For multiple keys (comma-separated):
   ```bash
   API_KEYS=sk-key-1,sk-key-2,sk-key-3
   ```

### Usage

Include the API key in the Authorization header:
```bash
Authorization: Bearer sk-your-secret-key-here
```

## Endpoints

### POST /v1/chat/completions

Main chat completion endpoint. Supports both streaming and non-streaming responses.

#### Request

```http
POST /v1/chat/completions
Content-Type: application/json
Authorization: Bearer sk-your-secret-key-here
```

**Body:**

```json
{
  "model": "default",
  "messages": [
    {"role": "user", "content": "What is quantum computing?"}
  ],
  "stream": false,
  "return_images": false,
  "return_related_questions": false,
  "search_domain_filter": ["arxiv.org"],
  "search_recency_filter": "week",
  "pro_search": false,
  "max_results": 6
}
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | `"default"` | Model identifier (currently ignored, uses backend default) |
| `messages` | array | required | Array of message objects with `role` and `content` |
| `stream` | boolean | `false` | Enable streaming responses (SSE) |
| `return_images` | boolean | `false` | Include image URLs in response |
| `return_related_questions` | boolean | `false` | Include related follow-up questions |
| `search_domain_filter` | array | `null` | Limit search to specific domains (e.g. `["reddit.com"]`) |
| `search_recency_filter` | string | `null` | Time range filter: `"day"`, `"week"`, `"month"`, or `"year"` |
| `pro_search` | boolean | `false` | Enable multi-step reasoning (requires pro mode enabled) |
| `max_results` | integer | `6` | Number of search results to use (1-20) |

**Message Roles:**
- `system` - System instructions (treated as assistant context)
- `user` - User messages
- `assistant` - Assistant responses

#### Response (Non-Streaming)

```json
{
  "id": "chatcmpl-1234567890",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "default",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Quantum computing is..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 150,
    "total_tokens": 250
  },
  "search_results": [
    {
      "title": "Quantum Computing Basics",
      "url": "https://example.com/quantum",
      "content": "Summary of the article..."
    }
  ],
  "related_questions": [
    "How does quantum entanglement work?",
    "What are quantum algorithms?",
    "What is quantum supremacy?"
  ],
  "images": [
    "https://example.com/image1.jpg"
  ]
}
```

**Additional Fields (Perplexity OSS Extensions):**
- `search_results` - Array of search result objects (only if results found)
- `related_questions` - Array of follow-up questions (only if `return_related_questions: true`)
- `images` - Array of image URLs (only if `return_images: true`)

#### Response (Streaming)

Server-Sent Events (SSE) format with `text/event-stream` content type.

**Event Format:**
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":123,"model":"default","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":123,"model":"default","choices":[{"index":0,"delta":{"content":"Quantum"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":123,"model":"default","choices":[{"index":0,"delta":{"content":" computing"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":123,"model":"default","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

**Delta Object:**
- First chunk includes `role`
- Subsequent chunks include `content` with text fragments
- Final chunk includes `finish_reason: "stop"`
- Stream ends with `data: [DONE]`

### GET /v1/models

List available models.

#### Request

```http
GET /v1/models
Authorization: Bearer sk-your-secret-key-here
```

#### Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "default",
      "object": "model",
      "created": 1234567890,
      "owned_by": "perplexity-oss"
    }
  ]
}
```

## Examples

### cURL - Basic Request

```bash
curl http://localhost:8003/v1/chat/completions \
  -H "Authorization: Bearer sk-your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "messages": [
      {"role": "user", "content": "Explain AI in simple terms"}
    ]
  }'
```

### cURL - Streaming

```bash
curl http://localhost:8003/v1/chat/completions \
  -H "Authorization: Bearer sk-your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "messages": [
      {"role": "user", "content": "What is machine learning?"}
    ],
    "stream": true
  }'
```

### cURL - With Filters

```bash
curl http://localhost:8003/v1/chat/completions \
  -H "Authorization: Bearer sk-your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "messages": [
      {"role": "user", "content": "Latest AI research"}
    ],
    "search_recency_filter": "week",
    "search_domain_filter": ["arxiv.org", "paperswithcode.com"],
    "return_related_questions": true
  }'
```

### Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-your-secret-key-here",
    base_url="http://localhost:8003/v1"
)

response = client.chat.completions.create(
    model="default",
    messages=[
        {"role": "user", "content": "What is quantum computing?"}
    ],
    extra_body={
        "search_recency_filter": "month",
        "return_related_questions": True
    }
)

print(response.choices[0].message.content)
```

### Python (Streaming)

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-your-secret-key-here",
    base_url="http://localhost:8003/v1"
)

stream = client.chat.completions.create(
    model="default",
    messages=[
        {"role": "user", "content": "Explain neural networks"}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### JavaScript/TypeScript

```typescript
const response = await fetch('http://localhost:8003/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sk-your-secret-key-here',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'default',
    messages: [
      { role: 'user', content: 'What is deep learning?' }
    ],
    return_related_questions: true
  })
});

const data = await response.json();
console.log(data.choices[0].message.content);
```

## Search Features

### Domain Filtering

Limit search results to specific domains using `search_domain_filter`:

```json
{
  "search_domain_filter": ["reddit.com", "stackoverflow.com"]
}
```

This adds `site:domain.com` operators to the search query.

### Time Range Filtering

Filter results by recency using `search_recency_filter`:

- `"day"` - Last 24 hours
- `"week"` - Last 7 days
- `"month"` - Last 30 days
- `"year"` - Last 365 days

```json
{
  "search_recency_filter": "week"
}
```

### Pro Search Mode

Enable multi-step reasoning for complex queries:

```json
{
  "pro_search": true
}
```

**Note:** Requires `NEXT_PUBLIC_PRO_MODE_ENABLED=true` in backend configuration.

Pro search automatically:
1. Breaks down complex queries into steps
2. Generates targeted search queries for each step
3. Synthesizes information from multiple searches
4. Provides comprehensive answers

## Error Handling

### Error Response Format

```json
{
  "error": {
    "message": "Invalid API key",
    "type": "invalid_request_error",
    "code": 401
  }
}
```

### Common Error Codes

| Code | Type | Description |
|------|------|-------------|
| 401 | `invalid_request_error` | Missing or invalid API key |
| 400 | `invalid_request_error` | Invalid request format or parameters |
| 500 | `internal_error` | Server error during processing |
| 503 | `service_unavailable` | API keys not configured on server |

## Rate Limiting

Currently no rate limiting is implemented. Configure your own rate limiting if deploying to production.

## CORS

CORS is enabled for all origins by default. Modify `main.py` to restrict origins in production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Differences from OpenAI API

### Supported
- Standard message format with roles
- Streaming and non-streaming modes
- Bearer token authentication
- Compatible with OpenAI Python SDK

### Not Supported
- Temperature, top_p, max_tokens (uses backend defaults)
- Function calling / tools
- Image inputs (vision)
- Audio/TTS
- Embeddings

### Additional Features (Extensions)
- Search domain filtering (`search_domain_filter`)
- Time range filtering (`search_recency_filter`)
- Pro search mode (`pro_search`)
- Search results in response (`search_results`)
- Related questions (`related_questions`)
- Image URLs (`images`)
