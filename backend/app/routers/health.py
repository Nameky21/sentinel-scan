import httpx
from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health():
    return {"status": "ok"}


@router.get("/api/zap/status")
async def zap_status():
    url = f"{settings.zap_base_url}/JSON/core/view/version/"
    params = {"apikey": settings.zap_api_key}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        return {"connected": True, "version": data.get("version")}
    except httpx.HTTPError as exc:
        return {"connected": False, "error": str(exc)}
