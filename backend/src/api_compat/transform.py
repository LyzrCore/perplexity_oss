"""Request/response transformation between OpenAI and internal formats."""

import time
from typing import AsyncGenerator, Dict, List, Optional

from schemas import (
    ChatRequest,
    Message as InternalMessage,
    MessageRole as InternalRole,
    SearchResult,
    StreamEvent,
    ChatResponseEvent,
    TextChunkStream,
    SearchResultStream,
    RelatedQueriesStream,
    StreamEndStream,
)
from api_compat.schemas import (
    ChatCompletionRequest,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChunkDelta,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionMessage,
    UsageInfo,
    MessageRole,
    SearchResultCompat,
)


def apply_domain_filter(query: str, domains: List[str]) -> str:
    """
    Apply domain filtering to query using site: operators.

    Example: ["reddit.com", "stackoverflow.com"] → "query site:reddit.com OR site:stackoverflow.com"
    """
    if not domains:
        return query

    # Build site: filter
    site_filter = " OR ".join([f"site:{domain.strip()}" for domain in domains])
    return f"{query} ({site_filter})"


def openai_to_internal(
    request: ChatCompletionRequest,
    thread_id: Optional[int] = None
) -> ChatRequest:
    """
    Transform OpenAI ChatCompletionRequest to internal ChatRequest format.

    Args:
        request: OpenAI-compatible request
        thread_id: Optional thread ID for conversation tracking

    Returns:
        Internal ChatRequest object
    """
    # Extract the last user message as the query
    user_messages = [msg for msg in request.messages if msg.role == MessageRole.USER]
    if not user_messages:
        raise ValueError("No user message found in request")

    query = user_messages[-1].content

    # Apply domain filtering if specified
    if request.search_domain_filter:
        query = apply_domain_filter(query, request.search_domain_filter)

    # History is now managed by Lyzr via session_id - no need to convert messages
    # The agent will maintain conversation context automatically

    return ChatRequest(
        thread_id=thread_id,  # Deprecated but kept for backwards compat
        session_id=request.session_id,  # Pass through session_id
        query=query,
        pro_search=request.pro_search,
        time_range=request.search_recency_filter,
        max_results=request.max_results,
        start_date=request.start_date,  # Pass through custom date range
        end_date=request.end_date
    )


async def internal_to_openai_stream(
    internal_stream: AsyncGenerator,
    request_id: str,
    model: str,
    created: int,
    include_images: bool = False,
    include_related: bool = False
) -> AsyncGenerator[str, None]:
    """
    Transform internal streaming events to OpenAI SSE format.

    Args:
        internal_stream: Internal event stream
        request_id: Unique request ID
        model: Model name to include in response
        created: Timestamp for response
        include_images: Whether to include image results
        include_related: Whether to include related questions

    Yields:
        SSE formatted strings ("data: {json}\n\n")
    """
    # Track accumulated data
    search_results = []
    related_questions = []
    images = []
    full_message = ""

    # Send initial chunk with role
    initial_chunk = ChatCompletionChunk(
        id=request_id,
        created=created,
        model=model,
        choices=[
            ChatCompletionChunkChoice(
                index=0,
                delta=ChatCompletionChunkDelta(role=MessageRole.ASSISTANT),
                finish_reason=None
            )
        ]
    )
    yield f"data: {initial_chunk.model_dump_json()}\n\n"

    async for event_data in internal_stream:
        # event_data is a ChatResponseEvent Pydantic object
        # Convert to dict for easier access
        from fastapi.encoders import jsonable_encoder
        event_dict = jsonable_encoder(event_data)

        event_type = event_dict.get("event")
        data = event_dict.get("data", {})

        if event_type == StreamEvent.TEXT_CHUNK:
            # Stream text content
            text = data.get("text", "")
            full_message += text

            chunk = ChatCompletionChunk(
                id=request_id,
                created=created,
                model=model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=0,
                        delta=ChatCompletionChunkDelta(content=text),
                        finish_reason=None
                    )
                ]
            )
            yield f"data: {chunk.model_dump_json()}\n\n"

        elif event_type == StreamEvent.SEARCH_RESULTS:
            # Store search results (will be sent in extensions or at end)
            results = data.get("results", [])
            search_results.extend(results)

            if include_images:
                imgs = data.get("images", [])
                images.extend(imgs)

        elif event_type == StreamEvent.RELATED_QUERIES:
            # Store related questions
            if include_related:
                queries = data.get("related_queries", [])
                related_questions.extend(queries)

        elif event_type == StreamEvent.STREAM_END:
            # Send final chunk with finish_reason
            final_chunk = ChatCompletionChunk(
                id=request_id,
                created=created,
                model=model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=0,
                        delta=ChatCompletionChunkDelta(),
                        finish_reason="stop"
                    )
                ]
            )
            yield f"data: {final_chunk.model_dump_json()}\n\n"

            # Send [DONE] marker (OpenAI standard)
            yield "data: [DONE]\n\n"
            break

    # Note: search_results, images, and related_questions are accumulated but not sent
    # in streaming mode (OpenAI spec doesn't support this in stream chunks).
    # They could be sent as custom events or in a final summary chunk if needed.


def internal_to_openai_complete(
    message: str,
    request_id: str,
    model: str,
    created: int,
    search_results: Optional[List[SearchResult]] = None,
    related_questions: Optional[List[str]] = None,
    images: Optional[List[str]] = None,
    include_images: bool = False,
    include_related: bool = False
) -> ChatCompletionResponse:
    """
    Transform internal complete response to OpenAI ChatCompletionResponse.

    Args:
        message: Complete response message
        request_id: Unique request ID
        model: Model name
        created: Timestamp
        search_results: Optional search results
        related_questions: Optional related questions
        images: Optional image URLs
        include_images: Whether to include images in response
        include_related: Whether to include related questions

    Returns:
        OpenAI-compatible ChatCompletionResponse
    """
    # Estimate token usage (rough approximation)
    prompt_tokens = 100  # Placeholder
    completion_tokens = len(message.split()) * 2  # Rough estimate

    usage = UsageInfo(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens
    )

    # Convert search results to compat format
    compat_results = None
    if search_results:
        compat_results = [
            SearchResultCompat(
                title=r.title,
                url=r.url,
                content=r.content
            )
            for r in search_results
        ]

    return ChatCompletionResponse(
        id=request_id,
        created=created,
        model=model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatCompletionMessage(
                    role=MessageRole.ASSISTANT,
                    content=message
                ),
                finish_reason="stop"
            )
        ],
        usage=usage,
        search_results=compat_results,
        related_questions=related_questions if include_related else None,
        images=images if include_images else None
    )
