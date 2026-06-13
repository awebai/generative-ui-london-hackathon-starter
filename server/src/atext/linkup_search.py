from __future__ import annotations

import asyncio
from typing import Any

from fastapi import HTTPException

from atext.config import Settings
from atext.models import SearchRequest


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


async def run_linkup_search(payload: SearchRequest, *, settings: Settings) -> dict[str, Any]:
    if not settings.linkup_api_key:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "linkup_not_configured",
                "message": "LINKUP_API_KEY is not configured on the genui server.",
            },
        )

    def search() -> Any:
        from linkup import LinkupClient

        client = LinkupClient(api_key=settings.linkup_api_key)
        return client.search(
            query=payload.query,
            depth=payload.depth,
            output_type="sourcedAnswer",
            max_results=payload.max_results,
            include_inline_citations=True,
            include_sources=True,
            timeout=30,
        )

    try:
        result = await asyncio.to_thread(search)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "linkup_search_failed", "message": "LinkUp search failed."},
        ) from exc

    return {"query": payload.query, "depth": payload.depth, "result": _jsonable(result)}
