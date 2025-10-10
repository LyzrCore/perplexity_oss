"""Lyzr Agent LLM implementation for the Perplexity OSS application."""

import os
import json
import asyncio
from typing import AsyncIterator, Dict, Any, List, TypeVar, Iterator
import aiohttp
from pydantic import BaseModel

from dotenv import load_dotenv

from .base import BaseLLM, CompletionResponse, CompletionResponseAsyncGen

# Type aliases for generators
CompletionResponseGen = Iterator[CompletionResponse]

T = TypeVar("T")

load_dotenv()


class LyzrAgentLLM(BaseLLM):
    """Lyzr Agent implementation for the BaseLLM interface"""

    def __init__(self, agent_id: str, api_key: str = None, api_base: str = None):
        self.agent_id = agent_id
        self.api_key = api_key or os.getenv("LYZR_API_KEY")
        self.api_base = api_base or os.getenv(
            "LYZR_API_BASE", "https://agent.api.lyzr.app"
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
            # Use the chat completions endpoint for non-streaming
            return f"{self.api_base}/v3/inference/{self.agent_id}/chat/completions"

    def _format_messages(self, prompt: str) -> List[Dict[str, Any]]:
        """Format prompt as messages for Lyzr API"""
        return [{"role": "user", "content": prompt}]

    async def astream(self, prompt: str) -> CompletionResponseAsyncGen:
        """Async streaming completion using Lyzr Agent API"""

        async def _astream() -> AsyncIterator[CompletionResponse]:
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

            # Use the streaming endpoint with the correct payload format
            payload = {
                "user_id": "default_user",
                "system_prompt_variables": {},
                "agent_id": self.agent_id,
                "session_id": "default_session",  # You might want to make this dynamic
                "message": prompt,
            }

            print(f"Streaming to Lyzr API:")
            print(f"  URL: {self._build_url(streaming=True)}")
            print(f"  Headers: {self.headers}")
            print(f"  Payload: {payload}")

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        self._build_url(streaming=True), headers=self.headers, json=payload
                    ) as response:
                        print(f"Received streaming response from Lyzr API:")
                        print(f"  Status: {response.status}")
                        print(f"  Headers: {dict(response.headers)}")

                        if response.status != 200:
                            error_text = await response.text()
                            print(f"  Error Response Body: {error_text}")
                            raise Exception(
                                f"Lyzr API error {response.status}: {error_text}"
                            )

                        # OLD CODE - Commented out (was parsing JSON chunks)
                        # buffer = ""
                        # async for chunk in response.content.iter_chunked(8192):
                        #     chunk_str = chunk.decode("utf-8")
                        #     buffer += chunk_str
                        #     print(f"  Streaming chunk received: {chunk_str}")
                        #     # ... JSON parsing logic ...

                        # NEW CODE - Handle plain text SSE tokens from /v3/inference/stream/
                        buffer = ""
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
                                
                                # Check for end marker
                                if line == "[DONE]":
                                    print("  Stream completed: [DONE]")
                                    break
                                
                                # Lyzr's stream endpoint already includes "data: " prefix - strip it
                                if line.startswith("data: "):
                                    token = line[6:]  # Remove "data: " prefix
                                    
                                    # Lyzr API already includes proper spacing in tokens!
                                    # Tokens come with leading spaces when needed (e.g., "data:  I")
                                    # and without spaces when continuing a word (e.g., "data: uc" in "Hallucination")
                                    print(f"  Token received: {repr(token)}")
                                    
                                    if token:  # Only yield non-empty tokens
                                        yield CompletionResponse(text="", delta=token)

                except Exception as e:
                    # If streaming fails, fall back to non-streaming
                    response = await self._complete_async(prompt)
                    yield CompletionResponse(text=response.text, delta=response.text)

        return _astream()

    async def _complete_async(self, prompt: str) -> CompletionResponse:
        """Async non-streaming completion"""
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

        payload = {
            "model": "lyzr-agent",
            "messages": self._format_messages(prompt),
            "stream": False,
        }

        print(f"Sending to Lyzr API:")
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
                        return CompletionResponse(
                            text=f"Error: Lyzr API returned status {response.status}"
                        )

                    result = await response.json()
                    print(f"  Response Body: {result}")

                    # Extract content from response - handle Lyzr's nested structure
                    if "choices" in result and len(result["choices"]) > 0:
                        choice = result["choices"][0]
                        if "message" in choice and "content" in choice["message"]:
                            content = choice["message"]["content"]

                            # Handle nested response structure from Lyzr
                            if isinstance(content, dict) and "response" in content:
                                content = content["response"]

                            # Ensure content is a string and not None
                            if content is not None:
                                return CompletionResponse(text=str(content))

                    # If no valid content found, return empty response
                    print(f"No valid content in Lyzr response: {result}")
                    return CompletionResponse(text="No response content from Lyzr API")

        except Exception as e:
            print(f"Exception calling Lyzr API: {e}")
            return CompletionResponse(text=f"Error connecting to Lyzr API: {str(e)}")

    def complete(self, prompt: str) -> CompletionResponse:
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
                    lambda: asyncio.run(self._complete_async(prompt))
                )
                return future.result()
        else:
            return loop.run_until_complete(self._complete_async(prompt))

    def structured_complete(self, response_model: type[T], prompt: str) -> T:
        """Structured completion with Pydantic model"""

        # For RelatedQueries, use a simpler approach that extracts from text
        if response_model.__name__ == "RelatedQueries":
            return self._extract_related_queries(prompt, response_model)

        # For structured completion, we'll add instructions to return JSON
        structured_prompt = f"""
{prompt}

Please respond with a JSON object that matches this structure:
{response_model.model_json_schema()}

Only return valid JSON, no additional text.
"""

        response = self.complete(structured_prompt)

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

    def _extract_related_queries(self, prompt: str, response_model: type[T]) -> T:
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

        response = self.complete(simple_prompt)
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


class LyzrAgentProvider:
    """Factory for creating LyzrAgentLLM instances"""

    @staticmethod
    def create_agent(
        agent_id: str, api_key: str = None, api_base: str = None
    ) -> LyzrAgentLLM:
        """Create a new LyzrAgentLLM instance"""
        return LyzrAgentLLM(agent_id=agent_id, api_key=api_key, api_base=api_base)

    @staticmethod
    def get_default_agent() -> LyzrAgentLLM:
        """Get the default agent from environment variables"""
        agent_id = os.getenv("LYZR_DEFAULT_AGENT_ID")
        if not agent_id:
            raise ValueError("LYZR_DEFAULT_AGENT_ID environment variable is required")

        return LyzrAgentProvider.create_agent(agent_id)


class LyzrSpecializedAgents:
    """Manager for specialized Lyzr agents for different tasks"""

    def __init__(self, api_key: str = None, api_base: str = None):
        self.api_key = api_key or os.getenv("LYZR_API_KEY")
        self.api_base = api_base or os.getenv("LYZR_API_BASE", "https://agent.api.lyzr.app")

        # Load agent IDs from environment
        self.query_rephrase_agent_id = os.getenv("LYZR_QUERY_REPHRASE_AGENT_ID")
        self.answer_generation_agent_id = os.getenv("LYZR_ANSWER_GENERATION_AGENT_ID")
        self.related_questions_agent_id = os.getenv("LYZR_RELATED_QUESTIONS_AGENT_ID")
        self.query_planning_agent_id = os.getenv("LYZR_QUERY_PLANNING_AGENT_ID")
        self.search_query_agent_id = os.getenv("LYZR_SEARCH_QUERY_AGENT_ID")

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
