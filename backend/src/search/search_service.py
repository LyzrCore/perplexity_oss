"""
Simplified search service using only SearXNG provider.
"""

import os
from dotenv import load_dotenv
from fastapi import HTTPException

from schemas import SearchResponse
from search.providers.searxng import SearxngSearchProvider

load_dotenv()


def get_searxng_base_url():
    """Get SearXNG base URL from environment variables."""
    searxng_base_url = os.getenv("SEARXNG_BASE_URL")
    if not searxng_base_url:
        raise HTTPException(
            status_code=500,
            detail="SEARXNG_BASE_URL is not set in the environment variables.",
        )
    return searxng_base_url


def get_search_provider() -> SearxngSearchProvider:
    """Get the SearXNG search provider instance."""
    searxng_base_url = get_searxng_base_url()
    return SearxngSearchProvider(searxng_base_url)


async def perform_search(query: str, time_range: str = None, num_results: int = 10) -> SearchResponse:
    """
    Perform search using SearXNG provider.

    Args:
        query: Search query string
        time_range: Optional time filter ("day", "week", "month", "year")
        num_results: Number of results to return (default: 10, max: 100)

    Returns:
        SearchResponse object containing search results
    """
    search_provider = get_search_provider()

    try:
        results = await search_provider.search(query, time_range=time_range, num_results=num_results)
        return results
    except Exception as e:
        print(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=500, detail="There was an error while searching."
        )