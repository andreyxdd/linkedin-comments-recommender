import pytest

from app.services.data_fetcher import MockDataFetcher


@pytest.mark.asyncio
async def test_mock_fetcher_returns_items():
    fetcher = MockDataFetcher()
    items = await fetcher.fetch("photosynthesis", "biology")
    assert len(items) == 2
    assert "photosynthesis" in items[0].title.lower()
    assert items[0].content
    assert items[0].source_url


@pytest.mark.asyncio
async def test_mock_fetcher_includes_context():
    fetcher = MockDataFetcher()
    items = await fetcher.fetch("algorithms", "computer science")
    assert "computer science" in items[0].content
