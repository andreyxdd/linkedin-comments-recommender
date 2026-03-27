from typing import Protocol

import httpx

from app.models import DataItem


class DataFetcher(Protocol):
    """Protocol for fetching external data. Implement this for your domain.

    Examples:
        - WikipediaFetcher (included demo)
        - ApifyFetcher (LinkedIn, Twitter, etc.)
        - Custom API fetcher
    """

    async def fetch(self, topic: str, context: str) -> list[DataItem]: ...


class WikipediaFetcher:
    """Demo implementation: fetches Wikipedia articles via the REST API."""

    BASE_URL = "https://en.wikipedia.org/api/rest_v1"
    SEARCH_URL = "https://en.wikipedia.org/w/api.php"

    async def fetch(self, topic: str, context: str) -> list[DataItem]:
        search_query = f"{topic} {context}".strip()
        headers = {
            "User-Agent": "ai-fullstack-app/0.1.0 "
            "(https://github.com/andreyxdd/ai-fullstack-app)"
        }
        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            search_resp = await client.get(
                self.SEARCH_URL,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": search_query,
                    "srlimit": 3,
                    "format": "json",
                },
            )
            search_resp.raise_for_status()
            search_data = search_resp.json()
            results = search_data.get("query", {}).get("search", [])

            items: list[DataItem] = []
            for result in results:
                title = result["title"]
                page_resp = await client.get(
                    f"{self.BASE_URL}/page/summary/{title.replace(' ', '_')}"
                )
                if page_resp.status_code == 200:
                    page_data = page_resp.json()
                    items.append(
                        DataItem(
                            title=page_data.get("title", title),
                            content=page_data.get("extract", ""),
                            source_url=page_data.get("content_urls", {})
                            .get("desktop", {})
                            .get("page", ""),
                        )
                    )

            return items


class MockDataFetcher:
    """Mock fetcher for development and testing. No API keys needed."""

    async def fetch(self, topic: str, context: str) -> list[DataItem]:
        return [
            DataItem(
                title=f"Introduction to {topic}",
                content=(
                    f"{topic} is a broad subject within {context}. "
                    f"It encompasses key concepts including fundamental principles, "
                    f"practical applications, and theoretical foundations. "
                    f"Understanding {topic} requires familiarity with core terminology "
                    f"and the ability to apply concepts in real-world scenarios."
                ),
                source_url="https://example.com/intro",
            ),
            DataItem(
                title=f"Advanced {topic} Concepts",
                content=(
                    f"Advanced study of {topic} in {context} involves deeper analysis "
                    f"of underlying mechanisms, critical evaluation "
                    f"of competing theories, and synthesis of "
                    f"knowledge across related domains. Key areas "
                    f"include methodology, empirical evidence, "
                    f"and emerging trends."
                ),
                source_url="https://example.com/advanced",
            ),
        ]
