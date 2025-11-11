import asyncio

import httpx

from schemas import SearchResponse, SearchResult
from search.providers.base import SearchProvider


class SearxngSearchProvider(SearchProvider):
    def __init__(self, host: str):
        self.host = host

    async def search(self, query: str, time_range: str = None, num_results: int = 10) -> SearchResponse:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                link_results = await self.get_link_results(client, query, num_results=num_results, time_range=time_range)
                # Skip image results to avoid timeout issues
                image_results = []

            except Exception as e:
                print(f"Search failed: {e}")
                link_results = []
                image_results = []

        return SearchResponse(results=link_results, images=image_results)

    async def get_link_results(
        self, client: httpx.AsyncClient, query: str, num_results: int = 10, time_range: str = None
    ) -> list[SearchResult]:
        try:
            # Build search parameters
            params = {"q": query, "format": "json"}

            # Add time_range filter if specified
            # SearXNG supports: "day", "week", "month", "year"
            if time_range and time_range in ["day", "week", "month", "year"]:
                params["time_range"] = time_range

            response = await client.get(
                f"{self.host}/search",
                params=params,
            )
            response.raise_for_status()
            results = response.json()

            return [
                SearchResult(
                    title=result.get("title", ""),
                    url=result.get("url", ""),
                    content=result.get("content", ""),
                    published_date=result.get("publishedDate") or result.get("pubdate"),  # Extract date if available
                )
                for result in results.get("results", [])[:num_results]
                if result.get("url")  # Only include results with URLs
            ]
        except Exception as e:
            print(f"Failed to get link results: {e}")
            return []

    async def get_image_results(
        self, client: httpx.AsyncClient, query: str, num_results: int = 4
    ) -> list[str]:
        try:
            response = await client.get(
                f"{self.host}/search",
                params={"q": query, "format": "json", "categories": "images"},
            )
            response.raise_for_status()
            results = response.json()
            return [
                result["img_src"] 
                for result in results.get("results", [])[:num_results]
                if result.get("img_src")  # Only include results with image sources
            ]
        except Exception as e:
            print(f"Failed to get image results: {e}")
            return []
