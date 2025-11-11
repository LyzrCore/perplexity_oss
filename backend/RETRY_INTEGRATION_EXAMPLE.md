# Retry Mechanism Integration Guide

This guide shows how to integrate the retry utilities into your chat endpoint.

## Option 1: Add Retries to LyzrAgentLLM (Recommended)

Add retry logic to the API calls in `backend/src/llm/lyzr_agent.py`:

```python
# At the top of lyzr_agent.py
from retry_utils import async_retry, STANDARD_RETRY, STREAMING_RETRY

class LyzrAgentLLM(BaseLLM):
    # ... existing code ...

    # Add retry to non-streaming completions
    @async_retry(STANDARD_RETRY)
    async def _complete_async(self, prompt: str) -> CompletionResponse:
        # ... existing implementation ...
```

### For Streaming (More Careful Approach)

```python
# Only retry the initial connection, not mid-stream
async def astream(self, prompt: str) -> CompletionResponseAsyncGen:
    """Async streaming completion using Lyzr Agent API"""
    
    async def _astream() -> AsyncIterator[CompletionResponse]:
        # Check credentials first (existing code)
        if self.api_key in [...]:
            # ... existing placeholder checks ...
        
        # Wrap the connection attempt with retry
        @async_retry(STREAMING_RETRY)
        async def _establish_connection():
            return await aiohttp.ClientSession()
        
        try:
            session = await _establish_connection()
            async with session:
                # Rest of streaming logic...
                # Don't retry mid-stream, only initial connection
        except Exception as e:
            # ... existing error handling ...
    
    return _astream()
```

## Option 2: Add Circuit Breaker for Production Resilience

Protect against cascading failures by adding a circuit breaker:

```python
# In backend/src/llm/lyzr_agent.py
from retry_utils import circuit_breaker, CircuitBreaker

# Create a module-level circuit breaker (shared across all instances)
lyzr_api_breaker = CircuitBreaker(
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60.0,    # Wait 60s before testing recovery
    success_threshold=2,      # Need 2 successes to fully recover
)

class LyzrAgentLLM(BaseLLM):
    @circuit_breaker(lyzr_api_breaker)
    @async_retry(STANDARD_RETRY)
    async def _complete_async(self, prompt: str) -> CompletionResponse:
        # ... existing implementation ...
```

## Option 3: Add Retries at Endpoint Level

Add retry logic at the chat endpoint level:

```python
# In backend/src/main.py
from retry_utils import async_retry, STANDARD_RETRY

@app.post("/chat")
async def chat(
    chat_request: ChatRequest, 
    request: Request,
    user: AuthenticatedUser = Depends(get_authenticated_user)
) -> EventSourceResponse:
    async def generator():
        @async_retry(STANDARD_RETRY)
        async def _process_with_retry():
            stream_fn = (
                stream_pro_search_qa if chat_request.pro_search else stream_qa_objects
            )
            # Collect all events first
            events = []
            async for obj in stream_fn(request=chat_request, session=None, user=user):
                events.append(obj)
            return events
        
        try:
            events = await _process_with_retry()
            for obj in events:
                if await request.is_disconnected():
                    break
                yield json.dumps(jsonable_encoder(obj))
                await asyncio.sleep(0)
        except Exception as e:
            # ... existing error handling ...
```

**⚠️ Warning:** Option 3 buffers all events before streaming, which defeats the purpose of streaming. Only use if you need retries at this level.

## Recommended Production Setup

Use a combination of approaches:

```python
# backend/src/llm/lyzr_agent.py

from retry_utils import (
    async_retry, 
    circuit_breaker, 
    CircuitBreaker, 
    STANDARD_RETRY,
    STREAMING_RETRY
)

# Shared circuit breaker for Lyzr API
lyzr_api_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    success_threshold=2,
)

class LyzrAgentLLM(BaseLLM):
    
    # Retry + circuit breaker for non-streaming
    @circuit_breaker(lyzr_api_breaker)
    @async_retry(STANDARD_RETRY)
    async def _complete_async(self, prompt: str) -> CompletionResponse:
        # ... existing implementation ...
    
    # Lighter retry for streaming (connection only)
    async def astream(self, prompt: str) -> CompletionResponseAsyncGen:
        async def _astream() -> AsyncIterator[CompletionResponse]:
            # Check if circuit breaker allows request
            if not lyzr_api_breaker.should_allow_request():
                raise Exception("Lyzr API circuit breaker is OPEN - service temporarily unavailable")
            
            # ... existing streaming implementation with timeout ...
            
            try:
                # ... streaming logic ...
                lyzr_api_breaker.record_success()
                
            except Exception as e:
                lyzr_api_breaker.record_failure()
                raise
        
        return _astream()
```

## Testing the Retry Mechanism

### Test 1: Simulate Network Failure

```python
# Add to test file
import pytest
from retry_utils import async_retry, RetryConfig

@pytest.mark.asyncio
async def test_retry_on_network_failure():
    attempt_count = 0
    
    @async_retry(RetryConfig(max_attempts=3, base_delay=0.1))
    async def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise aiohttp.ClientError("Network error")
        return "success"
    
    result = await failing_function()
    assert result == "success"
    assert attempt_count == 3  # Failed twice, succeeded on third attempt
```

### Test 2: Circuit Breaker Behavior

```python
from retry_utils import CircuitBreaker

def test_circuit_breaker_opens_after_failures():
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
    
    # Record failures
    for _ in range(3):
        breaker.record_failure()
    
    # Circuit should be open
    assert breaker.state == "OPEN"
    assert not breaker.should_allow_request()
    
    # Wait for recovery timeout
    import time
    time.sleep(1.1)
    
    # Circuit should transition to half-open
    assert breaker.should_allow_request()
    assert breaker.state == "HALF_OPEN"
```

## Monitoring and Observability

Add logging to track retry behavior:

```python
# In retry_utils.py, enhance the retry decorator:

print(
    f"⚠️ Attempt {attempt}/{config.max_attempts} failed with {exception_name}. "
    f"Retrying in {delay:.1f}s... (Error: {str(e)[:100]})"
)

# Add metrics if you have a metrics system:
# metrics.increment('api.retry.attempt', tags=[f'exception:{exception_name}'])
# metrics.timing('api.retry.delay', delay)
```

## Configuration via Environment Variables

Make retry behavior configurable:

```python
# backend/src/config/retry_config.py
import os

def get_retry_config():
    return RetryConfig(
        max_attempts=int(os.getenv("RETRY_MAX_ATTEMPTS", "3")),
        base_delay=float(os.getenv("RETRY_BASE_DELAY", "1.0")),
        max_delay=float(os.getenv("RETRY_MAX_DELAY", "10.0")),
    )

def get_circuit_breaker_config():
    return {
        "failure_threshold": int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5")),
        "recovery_timeout": float(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60.0")),
        "success_threshold": int(os.getenv("CIRCUIT_BREAKER_SUCCESS_THRESHOLD", "2")),
    }
```

Then in your `.env`:
```bash
# Retry configuration
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=10.0

# Circuit breaker configuration
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60.0
CIRCUIT_BREAKER_SUCCESS_THRESHOLD=2
```

## When NOT to Use Retries

❌ **Don't retry:**
1. User authentication failures (4xx errors)
2. Invalid request formats (validation errors)
3. Mid-stream failures (user already receiving data)
4. Resource exhaustion errors (out of memory, disk full)
5. Programming errors (bugs in your code)

✅ **Do retry:**
1. Network timeouts
2. Connection errors
3. Temporary API unavailability (503 Service Unavailable)
4. Rate limit errors (with exponential backoff)
5. Transient database connection issues

## Gradual Rollout Strategy

1. **Phase 1**: Deploy with enhanced error handling only (no retries yet)
2. **Phase 2**: Monitor error rates and types for 1-2 weeks
3. **Phase 3**: Add retries to non-streaming completions only
4. **Phase 4**: Add circuit breaker if needed
5. **Phase 5**: Consider streaming connection retries if issues persist

This allows you to validate that the improved error handling solves the issue before adding the complexity of retries.

