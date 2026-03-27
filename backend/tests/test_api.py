import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_generate_requires_linkedin_request_fields(client: AsyncClient):
    response = await client.post("/api/generate", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_rejects_out_of_range_tone_values(client: AsyncClient):
    response = await client.post(
        "/api/generate",
        json={
            "persona": "Founder",
            "topic": "AI agents",
            "keywords": ["distribution"],
            "tone": {
                "professional_casual": 120,
                "reserved_warm": 55,
                "measured_bold": 65,
                "conventional_fresh": 40,
            },
        },
    )

    assert response.status_code == 422
