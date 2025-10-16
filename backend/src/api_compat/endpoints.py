"""OpenAI-compatible API endpoints."""

import asyncio
import json
import time
import traceback
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from sse_starlette.sse import EventSourceResponse

from api_compat.middleware import verify_api_key
from api_compat.schemas import ChatCompletionRequest, ChatCompletionResponse
from api_compat.transform import (
    openai_to_internal,
    internal_to_openai_stream,
    internal_to_openai_complete,
)
from chat import stream_qa_objects
from agent_search import stream_pro_search_qa
from schemas import StreamEvent

# Create router for compatibility endpoints
router = APIRouter(prefix="/v1", tags=["OpenAI Compatible"])


@router.post("/chat/completions")
async def chat_completions(
    completion_request: ChatCompletionRequest,
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    """
    OpenAI-compatible chat completions endpoint.

    Supports both streaming and non-streaming responses.
    Accepts OpenAI format and Perplexity-compatible extensions.

    Authentication: Bearer token via Authorization header
    """
    # Generate request metadata
    request_id = f"chatcmpl-{int(time.time() * 1000)}"
    created = int(time.time())
    model = completion_request.model

    # Transform OpenAI request to internal format
    try:
        internal_request = openai_to_internal(completion_request)
    except ValueError as e:
        return {"error": {"message": str(e), "type": "invalid_request_error"}}

    # Handle streaming vs non-streaming
    if completion_request.stream:
        return await handle_streaming(
            internal_request=internal_request,
            request=request,
            request_id=request_id,
            model=model,
            created=created,
            include_images=completion_request.return_images,
            include_related=completion_request.return_related_questions,
            pro_search=completion_request.pro_search,
        )
    else:
        return await handle_non_streaming(
            internal_request=internal_request,
            request_id=request_id,
            model=model,
            created=created,
            include_images=completion_request.return_images,
            include_related=completion_request.return_related_questions,
            pro_search=completion_request.pro_search,
        )


async def handle_streaming(
    internal_request,
    request: Request,
    request_id: str,
    model: str,
    created: int,
    include_images: bool,
    include_related: bool,
    pro_search: bool,
) -> EventSourceResponse:
    """Handle streaming chat completion."""

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Choose appropriate stream function
            stream_fn = stream_pro_search_qa if pro_search else stream_qa_objects

            # Get internal event stream (passing None for session and user)
            internal_stream = stream_fn(
                request=internal_request,
                session=None,
                user=None  # Will use LYZR_API_KEY from environment
            )

            # Transform to OpenAI format and yield
            async for sse_data in internal_to_openai_stream(
                internal_stream=internal_stream,
                request_id=request_id,
                model=model,
                created=created,
                include_images=include_images,
                include_related=include_related,
            ):
                if await request.is_disconnected():
                    break
                yield sse_data
                await asyncio.sleep(0)

        except Exception as e:
            # Send error in OpenAI format
            error_response = {
                "error": {
                    "message": str(e),
                    "type": "internal_error",
                    "code": 500
                }
            }
            yield f"data: {json.dumps(error_response)}\n\n"
            yield "data: [DONE]\n\n"
            print(f"Error in streaming endpoint: {traceback.format_exc()}")

    return EventSourceResponse(event_generator(), media_type="text/event-stream")


async def handle_non_streaming(
    internal_request,
    request_id: str,
    model: str,
    created: int,
    include_images: bool,
    include_related: bool,
    pro_search: bool,
) -> ChatCompletionResponse:
    """Handle non-streaming chat completion."""
    try:
        # Choose appropriate stream function
        stream_fn = stream_pro_search_qa if pro_search else stream_qa_objects

        # Collect all events from internal stream
        full_message = ""
        search_results = []
        related_questions = []
        images = []

        async for event_data in stream_fn(
            request=internal_request,
            session=None,
            user=None  # Will use LYZR_API_KEY from environment
        ):
            # event_data is ChatResponseEvent
            event_dict = jsonable_encoder(event_data)
            event_type = event_dict.get("event")
            data = event_dict.get("data", {})

            if event_type == StreamEvent.TEXT_CHUNK:
                full_message += data.get("text", "")

            elif event_type == StreamEvent.SEARCH_RESULTS:
                from schemas import SearchResult
                results = data.get("results", [])
                # Convert dicts back to SearchResult objects
                search_results = [
                    SearchResult(**r) if isinstance(r, dict) else r
                    for r in results
                ]
                if include_images:
                    images = data.get("images", [])

            elif event_type == StreamEvent.RELATED_QUERIES:
                if include_related:
                    related_questions = data.get("related_queries", [])

            elif event_type == StreamEvent.STREAM_END:
                break

        # Transform to OpenAI format
        response = internal_to_openai_complete(
            message=full_message,
            request_id=request_id,
            model=model,
            created=created,
            search_results=search_results if search_results else None,
            related_questions=related_questions if related_questions else None,
            images=images if images else None,
            include_images=include_images,
            include_related=include_related,
        )

        return response

    except Exception as e:
        print(f"Error in non-streaming endpoint: {traceback.format_exc()}")
        return {
            "error": {
                "message": str(e),
                "type": "internal_error",
                "code": 500
            }
        }


@router.get("/models")
async def list_models(api_key: str = Depends(verify_api_key)):
    """
    List available models (OpenAI-compatible endpoint).

    Returns a simple model list. The actual model used is determined
    by the backend configuration.
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "default",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "perplexity-oss"
            }
        ]
    }
