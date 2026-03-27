import json

import pytest
import respx
from httpx import Response

from app.config import settings
from app.models import SuggestionRequest, ToneProfile
from app.services.linkedin_discovery import ApifyLinkedInDiscoveryAdapter
from app.services.post_ranking import rank_posts


def _request() -> SuggestionRequest:
    return SuggestionRequest(
        persona="Founder",
        topic="AI agents",
        keywords=["linkedin", "distribution"],
        tone=ToneProfile(
            professional_casual=62,
            reserved_warm=68,
            measured_bold=71,
            conventional_fresh=57,
        ),
    )


def _posts_fixture() -> list[dict]:
    return [
        {
            "activity_id": "1001",
            "post_url": "https://www.linkedin.com/posts/alpha_founder-ai-agents-distribution-1001",
            "text": "AI agents need distribution discipline to become useful.",
            "full_urn": "urn:li:ugcPost:1001",
            "author": {
                "name": "Alpha Founder",
                "headline": "Founder building AI workflow products",
                "profile_url": "https://www.linkedin.com/in/alpha-founder",
            },
            "stats": {
                "total_reactions": 45,
                "comments": 12,
                "shares": 3,
                "reactions": [{"type": "LIKE", "count": 45}],
            },
            "posted_at": {"timestamp": 1700000300},
            "hashtags": ["AIAgents", "Distribution"],
            "search_input": "AI agents linkedin distribution founder",
        },
        {
            "activity_id": "1002",
            "post_url": "https://www.linkedin.com/posts/bravo_leadership-productivity-1002",
            "text": "General leadership lessons with no AI angle at all.",
            "full_urn": "urn:li:ugcPost:1002",
            "author": {
                "name": "Bravo Executive",
                "headline": "Executive coach",
                "profile_url": "https://www.linkedin.com/in/bravo-executive",
            },
            "stats": {
                "total_reactions": 600,
                "comments": 180,
                "shares": 40,
                "reactions": [{"type": "LIKE", "count": 600}],
            },
            "posted_at": {"timestamp": 1700000200},
            "hashtags": ["Leadership"],
            "search_input": "AI agents linkedin distribution founder",
        },
        {
            "activity_id": "1003",
            "post_url": "https://www.linkedin.com/posts/delta_ai-agents-founder-growth-1004",
            "text": (
                "Founders using AI agents for distribution should study "
                "comment velocity."
            ),
            "full_urn": "urn:li:ugcPost:1004",
            "author": {
                "name": "Delta Founder",
                "headline": "Founder sharing weekly growth experiments",
                "profile_url": "https://www.linkedin.com/in/delta-founder",
            },
            "stats": {
                "total_reactions": 120,
                "comments": 35,
                "shares": 8,
                "reactions": [{"type": "PRAISE", "count": 120}],
            },
            "posted_at": {"timestamp": 1700000400},
            "hashtags": ["AIAgents", "Growth"],
            "search_input": "AI agents linkedin distribution founder",
        },
    ]


def _reactions_fixture() -> list[dict]:
    return [
        {
            "id": "reaction-1",
            "reactionType": "LIKE",
            "postId": "urn:li:ugcPost:1001",
            "actor": {
                "id": "reactor-1",
                "name": "Alice Signal",
                "linkedinUrl": "https://www.linkedin.com/in/alice-signal",
                "position": "Revenue operator",
            },
            "query": {
                "post": "https://www.linkedin.com/posts/alpha_founder-ai-agents-distribution-1001"
            },
        },
        {
            "id": "reaction-2",
            "reactionType": "INTEREST",
            "postId": "urn:li:ugcPost:1004",
            "actor": {
                "id": "reactor-2",
                "name": "Ben Demand",
                "linkedinUrl": "https://www.linkedin.com/in/ben-demand",
                "position": "Founder",
            },
            "query": {
                "post": "https://www.linkedin.com/posts/delta_ai-agents-founder-growth-1004"
            },
        },
    ]


@pytest.mark.asyncio
@respx.mock
async def test_discovery_adapter_normalizes_posts_and_reactions(monkeypatch):
    monkeypatch.setattr(settings, "apify_api_token", "test-token")
    monkeypatch.setattr(settings, "reaction_enrichment_count", 3)
    monkeypatch.setattr(settings, "max_reactions_per_post", 5)

    posts_route = respx.post(
        "https://api.apify.com/v2/acts/apimaestro~linkedin-posts-search-scraper-no-cookies/run-sync-get-dataset-items"
    ).mock(return_value=Response(200, json=_posts_fixture()))
    reactions_route = respx.post(
        "https://api.apify.com/v2/acts/harvestapi~linkedin-post-reactions/run-sync-get-dataset-items"
    ).mock(return_value=Response(200, json=_reactions_fixture()))

    adapter = ApifyLinkedInDiscoveryAdapter()
    posts = await adapter.discover(_request())

    assert posts_route.called
    assert reactions_route.called
    assert len(posts) == 3

    search_payload = json.loads(posts_route.calls[0].request.content.decode())
    assert "AI agents" in search_payload["keyword"]
    assert "linkedin" in search_payload["keyword"].lower()
    assert "founder" in search_payload["keyword"].lower()

    first = posts[0]
    assert first.author_name == "Alpha Founder"
    assert first.author_headline == "Founder building AI workflow products"
    assert first.total_reactions == 45
    assert first.total_comments == 12
    assert first.total_shares == 3
    assert first.reaction_samples[0].reactor_name == "Alice Signal"
    assert first.reaction_samples[0].reaction_type == "LIKE"


def test_ranker_prefers_relevance_first_then_engagement():
    ranked = rank_posts(
        _request(),
        posts=[*ApifyLinkedInDiscoveryAdapter.normalize_posts(_posts_fixture())],
    )

    assert [post.author_name for post in ranked] == [
        "Delta Founder",
        "Alpha Founder",
        "Bravo Executive",
    ]
