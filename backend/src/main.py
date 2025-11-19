"""
Perplexity OSS - FastAPI application powered by Lyzr AI.

This application provides AI-powered search and chat functionality using specialized
Lyzr agents for different tasks including query processing, search, and response generation.
"""

import asyncio
import json
import os
import traceback
from typing import Generator

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from agent_search import stream_pro_search_qa
from auth import get_authenticated_user, AuthenticatedUser
from chat import stream_qa_objects
from schemas import (
    ChatRequest,
    ChatResponseEvent,
    ErrorStream,
    StreamEvent,
)

load_dotenv()


def create_error_event(detail: str) -> ServerSentEvent:
    """Create a Server-Sent Event for error responses."""
    obj = ChatResponseEvent(
        data=ErrorStream(detail=detail),
        event=StreamEvent.ERROR,
    )
    return ServerSentEvent(
        data=json.dumps(jsonable_encoder(obj)),
        event=StreamEvent.ERROR,
    )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Perplexity OSS",
        description="AI-powered search engine powered by Lyzr AI",
        version="1.0.0",
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()

# Include OpenAI-compatible API routes
from api_compat.endpoints import router as compat_router
app.include_router(compat_router)


@app.on_event("startup")
async def startup_event():
    """Initialize agents on application startup."""
    print("\n" + "=" * 70)
    print("🚀 Perplexity OSS - Initializing...")
    print("=" * 70 + "\n")

    try:
        from config.agent_manager import ensure_agents_exist_async

        # Ensure all agents exist (will auto-create if needed)
        agent_ids = await ensure_agents_exist_async()

        print("\n✅ All agents initialized successfully!")
        print(f"   Agent IDs: {list(agent_ids.keys())}")

    except Exception as e:
        print(f"\n⚠️  Warning: Could not initialize agents: {e}")
        print("   The application will still start, but may fail on requests.")
        print("   Please check your LYZR_API_KEY and try again.\n")
        import traceback
        traceback.print_exc()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "perplexity-oss", "version": "2.0.0"}


@app.post("/chat")
async def chat(
    chat_request: ChatRequest, 
    request: Request,
    user: AuthenticatedUser = Depends(get_authenticated_user)
) -> EventSourceResponse:
    """
    Main chat endpoint that processes user queries using Lyzr agents.
    
    Supports both simple chat and advanced pro search modes.
    Returns a stream of responses including search results and AI-generated answers.
    Requires authentication.
    """
    async def generator():
        try:
            # Choose between simple chat and advanced pro search
            stream_fn = (
                stream_pro_search_qa if chat_request.pro_search else stream_qa_objects
            )
            
            async for obj in stream_fn(request=chat_request, session=None, user=user):
                if await request.is_disconnected():
                    break
                yield json.dumps(jsonable_encoder(obj))
                await asyncio.sleep(0)
                
        except Exception as e:
            print(f"Error in chat endpoint: {traceback.format_exc()}")
            # Ensure we always have a meaningful error message
            error_detail = str(e).strip() if str(e).strip() else "An unexpected error occurred during chat processing"
            error_type = type(e).__name__
            full_detail = f"{error_type}: {error_detail}" if error_detail != "An unexpected error occurred during chat processing" else error_detail
            yield create_error_event(full_detail)
            await asyncio.sleep(0)
            return

    return EventSourceResponse(generator(), media_type="text/event-stream")