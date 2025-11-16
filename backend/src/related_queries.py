from llm.base import BaseLLM
from prompts import RELATED_QUESTION_PROMPT
from schemas import RelatedQueries, SearchResult


async def generate_related_queries(
    query: str, search_results: list[SearchResult], llm: BaseLLM, session_id: str = None
) -> list[str]:
    # Format context from search results
    context = "\n\n".join([f"{str(result)}" for result in search_results])
    context = context[:4000]

    # Pass context via system_prompt_variables instead of formatting into prompt
    system_prompt_vars = {
        "user_query": query,
        "search_context": context
    }

    # Note: Not passing session_id - related questions should be fresh for each query,
    # not influenced by conversation history
    related = llm.structured_complete(
        RelatedQueries,
        RELATED_QUESTION_PROMPT,
        system_prompt_variables=system_prompt_vars
    )

    return [query.lower().replace("?", "") for query in related.related_questions]
