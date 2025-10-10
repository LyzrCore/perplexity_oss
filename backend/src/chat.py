"""Chat functionality using Lyzr Agents for AI-powered search and response."""

import asyncio
from typing import AsyncIterator, List, Optional

from fastapi import HTTPException

from auth import AuthenticatedUser
from llm.lyzr_agent import LyzrSpecializedAgents
from prompts import CHAT_PROMPT, HISTORY_QUERY_REPHRASE
from related_queries import generate_related_queries
from schemas import (
    BeginStream,
    ChatRequest,
    ChatResponseEvent,
    FinalResponseStream,
    Message,
    RelatedQueriesStream,
    SearchResult,
    SearchResultStream,
    StreamEndStream,
    StreamEvent,
    TextChunkStream,
)
from search.search_service import perform_search


def rephrase_query_with_history(
    question: str, history: List[Message], specialized_agents: LyzrSpecializedAgents
) -> str:
    """Rephrase user query considering conversation history using Lyzr query rephrase agent."""
    if not history:
        return question

    try:
        # Use specialized query rephrase agent
        agent = specialized_agents.get_query_rephrase_agent()
        history_str = "\n".join(f"{msg.role}: {msg.content}" for msg in history)
        formatted_query = HISTORY_QUERY_REPHRASE.format(
            chat_history=history_str, question=question
        )
        print(f"Using query rephrase agent for history processing")
        question = agent.complete(formatted_query).text.replace('"', "")
        return question
    except Exception as e:
        print(f"Error in query rephrase agent: {e}")
        raise HTTPException(
            status_code=500, detail="Model is at capacity. Please try again later."
        )


def format_context(search_results: List[SearchResult]) -> str:
    """Format search results into a context string for the LLM."""
    return "\n\n".join(
        [f"Citation {i+1}. {str(result)}" for i, result in enumerate(search_results)]
    )


async def stream_qa_objects(
    request: ChatRequest, session: Optional[any] = None, user: Optional[AuthenticatedUser] = None
) -> AsyncIterator[ChatResponseEvent]:
    """Stream chat responses using Lyzr agents for search and answer generation."""
    try:
        # Initialize specialized agents with user credentials
        # Use LYZR_API_KEY from env with user.api_key fallback
        import os
        api_key = os.getenv("LYZR_API_KEY") or (user.api_key if user else None)
        specialized_agents = LyzrSpecializedAgents(
            api_key=api_key,
            api_base=None  # Use default
        )

        yield ChatResponseEvent(
            event=StreamEvent.BEGIN_STREAM,
            data=BeginStream(query=request.query),
        )

        query = rephrase_query_with_history(
            request.query, request.history, specialized_agents
        )

        search_response = await perform_search(query)

        search_results = search_response.results
        images = search_response.images

        # Only create the task first if the model is not local
        related_queries_task = None
        related_queries_task = asyncio.create_task(
            generate_related_queries(
                query,
                search_results,
                specialized_agents.get_related_questions_agent(),
            )
        )

        yield ChatResponseEvent(
            event=StreamEvent.SEARCH_RESULTS,
            data=SearchResultStream(
                results=search_results,
                images=images,
            ),
        )

        fmt_qa_prompt = CHAT_PROMPT.format(
            my_context=format_context(search_results),
            my_query=query,
        )

        # Use specialized answer generation agent
        answer_agent = specialized_agents.get_answer_generation_agent()
        print(f"Using answer generation agent for main response")

        full_response = ""
        response_gen = await answer_agent.astream(fmt_qa_prompt)
        print("Response gen", response_gen)
        async for completion in response_gen:
            full_response += completion.delta or ""
            yield ChatResponseEvent(
                event=StreamEvent.TEXT_CHUNK,
                data=TextChunkStream(text=completion.delta or ""),
            )

        related_queries = await (
            related_queries_task
            if related_queries_task
            else generate_related_queries(
                query, search_results, specialized_agents.get_related_questions_agent()
            )
        )

        yield ChatResponseEvent(
            event=StreamEvent.RELATED_QUERIES,
            data=RelatedQueriesStream(related_queries=related_queries),
        )

        # Database disabled - no persistence
        thread_id = None

        yield ChatResponseEvent(
            event=StreamEvent.FINAL_RESPONSE,
            data=FinalResponseStream(message=full_response),
        )

        yield ChatResponseEvent(
            event=StreamEvent.STREAM_END,
            data=StreamEndStream(thread_id=thread_id),
        )

    except Exception as e:
        detail = str(e)
        raise HTTPException(status_code=500, detail=detail)
