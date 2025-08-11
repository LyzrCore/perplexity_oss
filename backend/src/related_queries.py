from llm.base import BaseLLM
from prompts import RELATED_QUESTION_PROMPT
from schemas import RelatedQueries, SearchResult


async def generate_related_queries(
    query: str, search_results: list[SearchResult], llm: BaseLLM
) -> list[str]:
    context = "\n\n".join([f"{str(result)}" for result in search_results])
    context = context[:4000]
    related = llm.structured_complete(
        RelatedQueries, RELATED_QUESTION_PROMPT.format(query=query, context=context)
    )

    return [query.lower().replace("?", "") for query in related.related_questions]
