import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.mark.asyncio
async def test_crawl_endpoint_empty_list():
    """Verifica se a API rejeita lista vazia com erro 400."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/pokemon/crawl", json={"names": []})
    
    assert response.status_code == 400
    assert "não pode estar vazia" in response.json()["detail"]

@pytest.mark.asyncio
async def test_crawl_endpoint_invalid_json():
    """Verifica erro de validação do Pydantic na API."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/pokemon/crawl", json={"names": "não é uma lista"})
    
    assert response.status_code == 422 # Unprocessable Entity
