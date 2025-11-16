"""Lyzr Agent LLM implementation for the Perplexity OSS application."""

import os
import json
import asyncio
from typing import AsyncIterator, Dict, Any, List, TypeVar, Iterator
import aiohttp
from pydantic import BaseModel

from dotenv import load_dotenv

from .base import BaseLLM, CompletionResponse, CompletionResponseAsyncGen
from retry_utils import async_retry, RetryConfig, CircuitBreaker

# Type aliases for generators
CompletionResponseGen = Iterator[CompletionResponse]

T = TypeVar("T")

load_dotenv()


# Module-level circuit breaker for Lyzr API (shared across all agent instances)
# This prevents cascading failures when the API is experiencing issues
lyzr_streaming_breaker = CircuitBreaker(
    failure_threshold=5,      # Open circuit after 5 consecutive failures
    recovery_timeout=30.0,    # Wait 30s before testing recovery (faster for streaming)
    success_threshold=2,      # Need 2 successes to fully close circuit
)

lyzr_completion_breaker = CircuitBreaker(
    failure_threshold=5,      # Open circuit after 5 consecutive failures  
    recovery_timeout=60.0,    # Wait 60s before testing recovery
    success_threshold=2,      # Need 2 successes to fully close circuit
)

# Retry configuration for non-streaming completions
COMPLETION_RETRY_CONFIG = RetryConfig(
    max_attempts=3,           # Retry up to 3 times total
    base_delay=0.5,          # Start with 0.5s delay
    max_delay=5.0,           # Cap at 5s delay
    exponential_base=2.0,    # Exponential backoff
    retry_exceptions=(asyncio.TimeoutError, aiohttp.ClientError),
)

# More conservative retry for streaming (only connection failures, not timeouts mid-stream)
STREAMING_RETRY_CONFIG = RetryConfig(
    max_attempts=2,           # Only retry once
    base_delay=0.5,          # Quick retry
    max_delay=2.0,           # Short max delay
    exponential_base=2.0,
    retry_exceptions=(aiohttp.ClientConnectionError,),  # Only connection failures
)


class LyzrAgentLLM(BaseLLM):
    """Lyzr Agent implementation for the BaseLLM interface"""

    def __init__(self, agent_id: str, api_key: str = None, api_base: str = None):
        self.agent_id = agent_id
        self.api_key = api_key or os.getenv("LYZR_API_KEY")
        self.api_base = api_base or os.getenv(
            "LYZR_API_BASE", "https://agent-prod.studio.lyzr.ai"
        )

        if not self.api_key:
            raise ValueError(
                "LYZR_API_KEY environment variable or api_key parameter is required"
            )

        if not self.agent_id:
            raise ValueError("agent_id is required")

        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-api-key": self.api_key,
        }

    def _build_url(self, streaming: bool = False) -> str:
        """Build the API URL for chat completions"""
        if streaming:
            # Use the streaming endpoint that returns plain text tokens
            return f"{self.api_base}/v3/inference/stream/"
        else:
            # Use the v3 chat endpoint (non-streaming)
            return f"{self.api_base}/v3/inference/chat/"

    def _format_messages(self, prompt: str) -> List[Dict[str, Any]]:
        """Format prompt as messages for Lyzr API"""
        return [{"role": "user", "content": prompt}]

    def _build_system_prompt_variables(self, variables: Dict[str, str] = None) -> Dict[str, str]:
        """Add common variables like datetime to system_prompt_variables"""
        from datetime import datetime
        
        result = variables.copy() if variables else {}
        if 'current_datetime' not in result:
            now = datetime.now()
            result['current_datetime'] = now.strftime("%A, %B %d, %Y %I:%M %p")
        return result

    async def astream(
        self,
        prompt: str,
        system_prompt_variables: Dict[str, str] = None,
        session_id: str = None,
        user_id: str = None
    ) -> CompletionResponseAsyncGen:
        """Async streaming completion using Lyzr Agent API with circuit breaker

        Args:
            prompt: The user message to send to the agent
            system_prompt_variables: Variables to substitute in the agent's system prompt
            session_id: Session ID for maintaining conversation history (auto-generated if not provided)
            user_id: User ID for tracking (defaults to "default_user" if not provided)
        """

        async def _astream() -> AsyncIterator[CompletionResponse]:
            # Check circuit breaker first
            if not lyzr_streaming_breaker.should_allow_request():
                error_msg = (
                    "Lyzr API streaming circuit breaker is OPEN - service temporarily unavailable. "
                    "This usually means the streaming API experienced multiple consecutive failures. "
                    "The circuit will automatically test recovery soon."
                )
                print(f"⚠️ {error_msg}")
                raise Exception(error_msg)
            
            # Check if we have valid API credentials for streaming
            if self.api_key in [
                None,
                "",
                "test_key_placeholder",
                "your_lyzr_api_key_here",
            ]:
                print(
                    f"Warning: Using placeholder/invalid Lyzr API key for streaming. Returning mock response."
                )
                yield CompletionResponse(
                    text="Mock streaming response", delta="Mock streaming response"
                )
                return

            if self.agent_id in [
                None,
                "",
                "test_agent_id_placeholder",
                "your_agent_id_here",
            ]:
                print(
                    f"Warning: Using placeholder/invalid Lyzr Agent ID for streaming. Returning mock response."
                )
                yield CompletionResponse(
                    text="Mock streaming response", delta="Mock streaming response"
                )
                return

            # Generate session_id if not provided
            import uuid
            actual_session_id = session_id or str(uuid.uuid4())
            
            # Build system_prompt_variables with datetime and custom vars
            actual_variables = self._build_system_prompt_variables(system_prompt_variables)
            
            # Use the streaming endpoint with the correct payload format
            payload = {
                "user_id": user_id or "default_user",  # Use authenticated user_id if provided
                "system_prompt_variables": actual_variables,
                "agent_id": self.agent_id,
                "session_id": actual_session_id,
                "message": prompt,
            }

            print(f"Streaming to Lyzr API:")
            print(f"  URL: {self._build_url(streaming=True)}")
            print(f"  Headers: {self.headers}")
            print(f"  Payload: {payload}")

            # Retry logic for establishing connection only (not mid-stream)
            connection_attempt = 0
            max_connection_attempts = STREAMING_RETRY_CONFIG.max_attempts
            last_error = None
            
            while connection_attempt < max_connection_attempts:
                connection_attempt += 1
                
                try:
                    async with aiohttp.ClientSession() as session:
                        # Add timeout for streaming requests (60s total, 30s between chunks)
                        timeout = aiohttp.ClientTimeout(total=60, sock_read=30)
                        
                        print(f"🔄 Connection attempt {connection_attempt}/{max_connection_attempts}")
                        
                        async with session.post(
                            self._build_url(streaming=True), 
                            headers=self.headers, 
                            json=payload,
                            timeout=timeout
                        ) as response:
                            print(f"Received streaming response from Lyzr API:")
                            print(f"  Status: {response.status}")
                            print(f"  Headers: {dict(response.headers)}")

                            if response.status != 200:
                                error_text = await response.text()
                                print(f"  Error Response Body: {error_text}")
                                
                                # Retry on 5xx errors if we have attempts left
                                if response.status >= 500 and connection_attempt < max_connection_attempts:
                                    delay = STREAMING_RETRY_CONFIG.base_delay * (STREAMING_RETRY_CONFIG.exponential_base ** (connection_attempt - 1))
                                    delay = min(delay, STREAMING_RETRY_CONFIG.max_delay)
                                    print(f"⚠️ Server error {response.status}, retrying in {delay:.1f}s...")
                                    await asyncio.sleep(delay)
                                    continue
                                
                                raise Exception(
                                    f"Lyzr API error {response.status}: {error_text}"
                                )

                            # Connection established successfully - now stream content
                            # Do NOT retry mid-stream failures
                            print("✅ Streaming connection established, starting to receive tokens...")
                            
                            buffer = ""
                            tokens_received = 0
                            
                            async for chunk in response.content.iter_chunked(8192):
                                chunk_str = chunk.decode("utf-8")
                                buffer += chunk_str
                                print(f"  Stream chunk received: {repr(chunk_str)}")

                                # Process complete lines (each token is on its own line)
                                while "\n" in buffer:
                                    line, buffer = buffer.split("\n", 1)
                                    line = line.strip()
                                    
                                    if not line:
                                        continue
                                    
                                    # Check for end marker (before stripping prefix)
                                    if line == "[DONE]":
                                        print(f"  Stream completed: [DONE] ({tokens_received} tokens received)")
                                        break
                                    
                                    # Lyzr's stream endpoint already includes "data: " prefix - strip it
                                    if line.startswith("data: "):
                                        token = line[6:]  # Remove "data: " prefix
                                        
                                        # Also check for [DONE] after stripping prefix
                                        if token == "[DONE]":
                                            print(f"  Stream completed: [DONE] (after prefix strip, {tokens_received} tokens received)")
                                            break
                                        
                                        # Convert literal \n to actual newlines for markdown rendering
                                        token = token.replace("\\n", "\n")
                                        
                                        print(f"  Token received: {repr(token)}")
                                        
                                        if token:  # Only yield non-empty tokens
                                            tokens_received += 1
                                            yield CompletionResponse(text="", delta=token)
                            
                            # Stream completed successfully - record success
                            lyzr_streaming_breaker.record_success()
                            print(f"✅ Streaming completed successfully ({tokens_received} tokens total)")
                            return  # Exit successfully

                except aiohttp.ClientConnectionError as e:
                    # Connection errors can be retried
                    last_error = e
                    error_msg = f"Lyzr API connection error: {type(e).__name__}"
                    if str(e):
                        error_msg = f"{error_msg} - {str(e)}"
                    print(f"⚠️ {error_msg}")
                    
                    if connection_attempt < max_connection_attempts:
                        delay = STREAMING_RETRY_CONFIG.base_delay * (STREAMING_RETRY_CONFIG.exponential_base ** (connection_attempt - 1))
                        delay = min(delay, STREAMING_RETRY_CONFIG.max_delay)
                        print(f"  Retrying in {delay:.1f}s...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Out of retries
                        lyzr_streaming_breaker.record_failure()
                        raise Exception(f"{error_msg} (after {max_connection_attempts} connection attempts)") from e
                        
                except asyncio.TimeoutError as e:
                    # Timeouts are usually not worth retrying (could be mid-stream)
                    last_error = e
                    error_msg = f"Lyzr API streaming timeout after 60s"
                    print(f"  Streaming timeout error: {error_msg}")
                    lyzr_streaming_breaker.record_failure()
                    raise Exception(error_msg) from e
                    
                except aiohttp.ClientError as e:
                    # Other client errors
                    last_error = e
                    error_msg = f"Lyzr API connection error: {type(e).__name__}"
                    if str(e):
                        error_msg = f"{error_msg} - {str(e)}"
                    print(f"  Streaming connection error: {error_msg}")
                    lyzr_streaming_breaker.record_failure()
                    raise Exception(error_msg) from e
                    
                except Exception as e:
                    # Unexpected errors
                    last_error = e
                    error_msg = f"Lyzr API streaming error: {type(e).__name__}"
                    if str(e):
                        error_msg = f"{error_msg} - {str(e)}"
                    print(f"  Streaming error: {error_msg}")
                    lyzr_streaming_breaker.record_failure()
                    raise Exception(error_msg) from e
            
            # If we get here, all retry attempts failed
            if last_error:
                lyzr_streaming_breaker.record_failure()
                raise Exception(f"Streaming failed after {max_connection_attempts} attempts") from last_error

        return _astream()

    async def _complete_async(
        self,
        prompt: str,
        system_prompt_variables: Dict[str, str] = None,
        session_id: str = None,
        user_id: str = None
    ) -> CompletionResponse:
        """Async non-streaming completion with retry and circuit breaker"""
        # Check circuit breaker first
        if not lyzr_completion_breaker.should_allow_request():
            raise Exception(
                "Lyzr API circuit breaker is OPEN - service temporarily unavailable. "
                "This usually means the API experienced multiple consecutive failures. "
                "The circuit will automatically test recovery soon."
            )
        
        # Check if we have valid API credentials
        if self.api_key in [None, "", "test_key_placeholder", "your_lyzr_api_key_here"]:
            print(
                f"Warning: Using placeholder/invalid Lyzr API key. Returning mock response."
            )
            return CompletionResponse(
                text="Mock response: Unable to connect to Lyzr API with placeholder credentials."
            )

        if self.agent_id in [
            None,
            "",
            "test_agent_id_placeholder",
            "your_agent_id_here",
        ]:
            print(
                f"Warning: Using placeholder/invalid Lyzr Agent ID. Returning mock response."
            )
            return CompletionResponse(
                text="Mock response: Unable to connect to Lyzr API with placeholder agent ID."
            )

        # Inner function with retry logic
        @async_retry(COMPLETION_RETRY_CONFIG)
        async def _make_request():
            # Generate session_id if not provided
            import uuid
            actual_session_id = session_id or str(uuid.uuid4())
            
            # Build system_prompt_variables with datetime and custom vars
            actual_variables = self._build_system_prompt_variables(system_prompt_variables)
            
            # Use v3 API payload format
            payload = {
                "user_id": user_id or "default_user",  # Use authenticated user_id if provided
                "agent_id": self.agent_id,
                "session_id": actual_session_id,
                "message": prompt,
                "system_prompt_variables": actual_variables
            }

            print(f"Sending to Lyzr API (non-streaming):")
            print(f"  URL: {self._build_url()}")
            print(f"  Headers: {self.headers}")
            print(f"  Payload: {payload}")

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self._build_url(),
                        headers=self.headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        print(f"Received from Lyzr API:")
                        print(f"  Status: {response.status}")
                        print(f"  Headers: {dict(response.headers)}")

                        if response.status != 200:
                            error_text = await response.text()
                            print(f"  Error Response Body: {error_text}")
                            # Raise exception for retry on 5xx errors
                            if response.status >= 500:
                                raise aiohttp.ClientError(f"Server error {response.status}: {error_text}")
                            # Don't retry 4xx errors
                            return CompletionResponse(
                                text=f"Error: Lyzr API returned status {response.status}"
                            )

                        result = await response.json()
                        print(f"  Response Body: {result}")

                        # Extract content from v3 API response
                        # v3 returns: {"response": "text", "session_id": "...", ...}
                        if "response" in result:
                            content = result["response"]
                            # Ensure content is a string and not None
                            if content is not None:
                                return CompletionResponse(text=str(content))
                        
                        # Fallback: try old format (choices array)
                        if "choices" in result and len(result["choices"]) > 0:
                            choice = result["choices"][0]
                            if "message" in choice and "content" in choice["message"]:
                                content = choice["message"]["content"]
                                if isinstance(content, dict) and "response" in content:
                                    content = content["response"]
                                if content is not None:
                                    return CompletionResponse(text=str(content))

                        # If no valid content found, return empty response
                        print(f"No valid content in Lyzr response: {result}")
                        return CompletionResponse(text="No response content from Lyzr API")

            except asyncio.TimeoutError as e:
                error_msg = f"Lyzr API timeout after 30s"
                print(f"Exception calling Lyzr API: {error_msg}")
                raise  # Re-raise for retry
            except aiohttp.ClientError as e:
                error_msg = f"Lyzr API connection error: {type(e).__name__}"
                if str(e):
                    error_msg = f"{error_msg} - {str(e)}"
                print(f"Exception calling Lyzr API: {error_msg}")
                raise  # Re-raise for retry
            except Exception as e:
                error_msg = str(e).strip() if str(e).strip() else f"Lyzr API error: {type(e).__name__}"
                print(f"Exception calling Lyzr API: {error_msg}")
                raise Exception(error_msg) from e

        # Execute with retry, then update circuit breaker
        try:
            result = await _make_request()
            lyzr_completion_breaker.record_success()
            return result
        except Exception as e:
            lyzr_completion_breaker.record_failure()
            # Add retry context to error message
            error_msg = str(e)
            if "after" not in error_msg.lower():  # Don't duplicate retry info
                error_msg = f"{error_msg} (after {COMPLETION_RETRY_CONFIG.max_attempts} attempts with retry)"
            raise Exception(error_msg) from e

    def complete(
        self,
        prompt: str,
        system_prompt_variables: Dict[str, str] = None,
        session_id: str = None,
        user_id: str = None
    ) -> CompletionResponse:
        """Synchronous completion"""
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # If we're already in an async context, we need to use a thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(self._complete_async(prompt, system_prompt_variables, session_id, user_id))
                )
                return future.result()
        else:
            return loop.run_until_complete(self._complete_async(prompt, system_prompt_variables, session_id, user_id))

    def structured_complete(
        self,
        response_model: type[T],
        prompt: str,
        system_prompt_variables: Dict[str, str] = None,
        session_id: str = None,
        user_id: str = None
    ) -> T:
        """Structured completion with Pydantic model"""

        # All models now use JSON schema - no special cases needed
        # The RELATED_QUESTIONS_AGENT was updated to use json_schema response format in v1.2.12

        # For structured completion, we'll add instructions to return JSON
        structured_prompt = f"""
{prompt}

Please respond with a JSON object that matches this structure:
{response_model.model_json_schema()}

Only return valid JSON, no additional text.
"""

        response = self.complete(structured_prompt, system_prompt_variables, session_id, user_id)

        try:
            import json
            import re

            response_text = response.text.strip()
            print(f"Raw structured response: {response_text}")

            # Lyzr API returns schema + data together, find the actual JSON data
            # Look for the last complete JSON object in the response
            json_objects = []
            decoder = json.JSONDecoder()
            idx = 0

            while idx < len(response_text):
                try:
                    obj, end_idx = decoder.raw_decode(response_text, idx)
                    json_objects.append(obj)
                    idx = end_idx
                    # Skip whitespace
                    while idx < len(response_text) and response_text[idx].isspace():
                        idx += 1
                except json.JSONDecodeError:
                    break

            print(f"Found {len(json_objects)} JSON objects: {json_objects}")

            # Try to find the object that matches our expected structure
            for obj in reversed(json_objects):  # Start from the last object
                if isinstance(obj, dict):
                    try:
                        # Check if this object has the expected structure for our model
                        validated = response_model(**obj)
                        print(f"Successfully validated object: {obj}")
                        return validated
                    except Exception as validation_error:
                        print(f"Validation failed for object {obj}: {validation_error}")
                        continue

            # If no object validates, try regex approach as fallback
            json_matches = re.findall(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response_text)
            for match in reversed(json_matches):
                try:
                    obj = json.loads(match)
                    validated = response_model(**obj)
                    print(f"Successfully parsed with regex: {obj}")
                    return validated
                except:
                    continue

            raise Exception(
                f"No valid JSON object found that matches the expected structure"
            )

        except Exception as e:
            print(f"Structured completion error: {e}")
            print(f"Response was: {response.text}")
            raise Exception(f"Could not parse structured response: {e}")

    def _extract_related_queries(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt_variables: Dict[str, str] = None,
        session_id: str = None,
        user_id: str = None
    ) -> T:
        """Special handler for related queries that may not return structured JSON"""
        import re

        # Use a simpler prompt that asks for questions directly
        simple_prompt = f"""
{prompt}

Please provide exactly 3 related follow-up questions, one per line, in this format:
1. First question?
2. Second question?
3. Third question?
"""

        response = self.complete(simple_prompt, system_prompt_variables, session_id, user_id)
        response_text = response.text.strip()

        print(f"Related queries response: {response_text}")

        # Extract numbered questions from the response
        question_patterns = [
            r"^\d+\.\s*(.+\?)\s*$",  # "1. Question?"
            r"^\-\s*(.+\?)\s*$",  # "- Question?"
            r"^(.+\?)\s*$",  # Just "Question?"
        ]

        questions = []
        lines = response_text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            for pattern in question_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    question = match.group(1).strip()
                    if question and len(questions) < 3:
                        questions.append(question)
                    break

        # If we couldn't extract 3 questions, generate some defaults
        if len(questions) < 3:
            fallback_questions = [
                "What are the main applications of this technology?",
                "How does this compare to similar solutions?",
                "What are the potential benefits and limitations?",
            ]
            while len(questions) < 3:
                questions.append(fallback_questions[len(questions)])

        # Take only first 3 questions
        questions = questions[:3]

        print(f"Extracted questions: {questions}")

        # Create the response model instance
        return response_model(related_questions=questions)


class LyzrSpecializedAgents:
    """Manager for specialized Lyzr agents for different tasks"""

    def __init__(self, api_key: str = None, api_base: str = None):
        self.api_key = api_key or os.getenv("LYZR_API_KEY")
        self.api_base = api_base or os.getenv("LYZR_API_BASE", "https://agent-prod.studio.lyzr.ai")

        # Load agent IDs using agent manager (sync - no auto-creation in __init__)
        # Priority: ENV vars → config file
        # Note: Auto-creation should happen at app startup, not per-request
        from config.agent_manager import load_agent_config_sync

        agent_ids = load_agent_config_sync(api_key=self.api_key, api_base=self.api_base)

        if agent_ids:
            # Loaded from env or config file
            self.query_rephrase_agent_id = agent_ids.get("query_rephrase")
            self.answer_generation_agent_id = agent_ids.get("answer_generation")
            self.related_questions_agent_id = agent_ids.get("related_questions")
            self.query_planning_agent_id = agent_ids.get("query_planning")
            self.search_query_agent_id = agent_ids.get("search_query")
        else:
            # No agents found - will need to be created at startup
            # For now, set to None and will fail with clear error message
            print("⚠ Warning: No agent IDs found in environment or config file.")
            print("   Please run agent creation at app startup or set environment variables.")
            self.query_rephrase_agent_id = None
            self.answer_generation_agent_id = None
            self.related_questions_agent_id = None
            self.query_planning_agent_id = None
            self.search_query_agent_id = None

        # Cache agents to avoid recreation
        self._agents_cache = {}

    def _get_agent(self, agent_id: str, task_name: str) -> LyzrAgentLLM:
        """Get or create an agent with caching"""
        if not agent_id:
            raise ValueError(
                f"Agent ID for {task_name} is not configured in environment variables"
            )

        if agent_id not in self._agents_cache:
            print(f"Creating Lyzr agent for {task_name}: {agent_id}")
            self._agents_cache[agent_id] = LyzrAgentLLM(
                agent_id=agent_id, api_key=self.api_key, api_base=self.api_base
            )

        return self._agents_cache[agent_id]

    def get_query_rephrase_agent(self) -> LyzrAgentLLM:
        """Get agent for query rephrasing with history"""
        return self._get_agent(self.query_rephrase_agent_id, "query_rephrase")

    def get_answer_generation_agent(self) -> LyzrAgentLLM:
        """Get agent for main answer generation"""
        return self._get_agent(self.answer_generation_agent_id, "answer_generation")

    def get_related_questions_agent(self) -> LyzrAgentLLM:
        """Get agent for related questions generation"""
        return self._get_agent(self.related_questions_agent_id, "related_questions")

    def get_query_planning_agent(self) -> LyzrAgentLLM:
        """Get agent for query planning (pro mode)"""
        return self._get_agent(self.query_planning_agent_id, "query_planning")

    def get_search_query_agent(self) -> LyzrAgentLLM:
        """Get agent for search query generation (pro mode)"""
        return self._get_agent(self.search_query_agent_id, "search_query")
