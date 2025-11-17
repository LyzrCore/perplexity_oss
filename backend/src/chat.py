"""Chat functionality using Lyzr Agents for AI-powered search and response."""

import asyncio
from typing import AsyncIterator, List, Optional

from fastapi import HTTPException

from auth import AuthenticatedUser
from llm.lyzr_agent import LyzrSpecializedAgents
from prompts import CHAT_PROMPT, SEARCH_TERM_EXTRACTION_PROMPT
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


def apply_date_range_filter(query: str, start_date: str = None, end_date: str = None) -> str:
    """
    Apply custom date range filters to a search query using Google-style operators.

    Args:
        query: The original search query
        start_date: Start date in YYYY-MM-DD format (appends 'after:' operator)
        end_date: End date in YYYY-MM-DD format (appends 'before:' operator)

    Returns:
        Modified query with date operators appended

    Example:
        apply_date_range_filter("AI research", "2022-11-01", "2023-07-31")
        -> "AI research after:2022-11-01 before:2023-07-31"
    """
    modified_query = query

    if start_date:
        modified_query += f" after:{start_date}"

    if end_date:
        modified_query += f" before:{end_date}"

    return modified_query


def extract_search_terms(query: str, specialized_agents: LyzrSpecializedAgents, session_id: str = None, user_id: str = None) -> str:
    """
    Extract the core search terms from a query using an agent.
    The agent understands what information to search for while ignoring output format instructions.
    """
    try:
        from datetime import datetime
        agent = specialized_agents.get_query_rephrase_agent()  # Reuse this agent for extraction
        # Format the prompt with the actual query (system_prompt_variables only work in agent instructions, not messages)
        now = datetime.now()
        current_datetime = now.strftime("%A, %B %d, %Y %I:%M %p")
        formatted_prompt = (SEARCH_TERM_EXTRACTION_PROMPT
                           .replace("{{ user_query }}", query)
                           .replace("{{ current_datetime }}", current_datetime))
        print(f"Using agent to extract search terms from query")
        search_terms = agent.complete(
            formatted_prompt,
            session_id=session_id,
            user_id=user_id
        ).text.strip().replace('"', '')
        return search_terms if search_terms else query
    except Exception as e:
        print(f"Error in search term extraction, using original query: {e}")
        return query


def rephrase_query_with_context(
    question: str, session_id: str, specialized_agents: LyzrSpecializedAgents, user_id: str = None
) -> str:
    """
    Rephrase user query using the query rephrase agent with conversation context.

    The query rephrase agent has MEMORY enabled, so it can access conversation history
    to understand contextual references like "it", "that", "their", etc.
    """
    try:
        # Use dedicated query rephrase agent (has MEMORY enabled for context)
        agent = specialized_agents.get_query_rephrase_agent()
        print(f"Using query rephrase agent with conversation context")

        # The query rephrase agent has conversation memory and knows how to handle contextual queries
        # Just pass the query directly - the agent's instructions handle the rest
        rephrased = agent.complete(question, session_id=session_id, user_id=user_id).text.strip()

        # Clean up common prefixes
        rephrased = rephrased.replace('"', '').replace("'", '')
        for prefix in ['Rephrased query:', 'Rephrased Query:', 'Rephrased question:', 'Rephrased Question:', 'The rephrased question is:', 'Here is the rephrased question:']:
            if rephrased.startswith(prefix):
                rephrased = rephrased[len(prefix):].strip()

        print(f"Original: {question}")
        print(f"Rephrased: {rephrased}")
        return rephrased if rephrased else question
    except Exception as e:
        print(f"Error in query rephrasing: {e}")
        # Don't fail completely - just use original query
        return question


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
        import uuid
        api_key = os.getenv("LYZR_API_KEY") or (user.api_key if user else None)
        user_id = user.user_id if user else None
        specialized_agents = LyzrSpecializedAgents(
            api_key=api_key,
            api_base=None  # Use default
        )

        yield ChatResponseEvent(
            event=StreamEvent.BEGIN_STREAM,
            data=BeginStream(query=request.query),
        )

        # Generate or use provided session_id
        session_id = request.session_id or str(uuid.uuid4())

        # First, rephrase the query with conversation context if this is a follow-up
        # Use dedicated query rephrase agent which has MEMORY enabled
        query = request.query
        if request.session_id:  # Only rephrase if we have an existing session (follow-up)
            query = rephrase_query_with_context(request.query, session_id, specialized_agents, user_id)

        # Extract search terms from the contextualized query using an agent
        search_query = extract_search_terms(query, specialized_agents, session_id, user_id)

        # Apply custom date range filters if provided
        search_query = apply_date_range_filter(
            search_query,
            start_date=request.start_date,
            end_date=request.end_date
        )

        print(f"Original query: {request.query}")
        print(f"Session ID: {session_id}")
        print(f"Search terms extracted: {search_query}")

        search_response = await perform_search(
            search_query,  # Use extracted search terms for SearXNG
            time_range=request.time_range,
            num_results=request.max_results
        )

        search_results = search_response.results
        images = search_response.images

        # Only create the task first if the model is not local
        related_queries_task = None
        related_queries_task = asyncio.create_task(
            generate_related_queries(
                query,
                search_results,
                specialized_agents.get_related_questions_agent(),
                session_id  # Pass session_id for context continuity
            )
        )

        yield ChatResponseEvent(
            event=StreamEvent.SEARCH_RESULTS,
            data=SearchResultStream(
                results=search_results,
                images=images,
            ),
        )

        # Use specialized answer generation agent with system_prompt_variables
        answer_agent = specialized_agents.get_answer_generation_agent()
        print(f"Using answer generation agent for main response")

        # Build system_prompt_variables for the agent
        from datetime import datetime
        now = datetime.now()
        current_datetime = now.strftime("%A, %B %d, %Y %I:%M %p")

        # Add date range context to user query if date filters are active
        query_with_context = query
        if request.start_date or request.end_date:
            if request.start_date and request.end_date:
                query_with_context = f"{query} (searching for results between {request.start_date} and {request.end_date})"
            elif request.start_date:
                query_with_context = f"{query} (searching for results from {request.start_date} onwards)"
            else:
                query_with_context = f"{query} (searching for results up to {request.end_date})"

        system_prompt_vars = {
            "search_context": format_context(search_results),
            "user_query": query_with_context,  # Include date range context
            "current_datetime": current_datetime
        }

        full_response = ""
        # Don't send the query as the message - the agent instructions already include it
        # Send a simple instruction to trigger the answer generation
        response_gen = await answer_agent.astream(
            prompt="Please provide a comprehensive answer to the user's question based on the search context provided above.",
            system_prompt_variables=system_prompt_vars,
            session_id=session_id,
            user_id=user_id
        )
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
                query, search_results, specialized_agents.get_related_questions_agent(), session_id
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
            data=StreamEndStream(
                thread_id=thread_id,  # Deprecated but kept for backwards compat
                session_id=session_id  # Return session_id so frontend can persist it
            ),
        )

    except Exception as e:
        # Ensure we have a meaningful error message
        detail = str(e).strip() if str(e).strip() else f"Chat processing error: {type(e).__name__}"
        print(f"Error in stream_qa_objects: {detail}")
        raise HTTPException(status_code=500, detail=detail)
