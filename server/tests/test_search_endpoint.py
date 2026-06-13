from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException
from pydantic import BaseModel

from atext.config import Settings
from atext.linkup_search import run_linkup_search
from atext.models import SearchRequest


class FakeLinkupResult(BaseModel):
    answer: str
    sources: list[dict[str, str]]


@pytest.mark.asyncio
async def test_linkup_search_requires_server_side_key() -> None:
    payload = SearchRequest(query="agent-first UI")

    with pytest.raises(HTTPException) as raised:
        await run_linkup_search(payload, settings=Settings(linkup_api_key=None))

    assert raised.value.status_code == 503
    assert raised.value.detail["code"] == "linkup_not_configured"


@pytest.mark.asyncio
async def test_linkup_search_uses_real_client_shape_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []

    class FakeClient:
        def __init__(self, *, api_key: str) -> None:
            calls.append({"api_key": api_key})

        def search(self, **kwargs: Any) -> FakeLinkupResult:
            calls.append(kwargs)
            return FakeLinkupResult(
                answer="LinkUp and CopilotKit help agents produce cited UI.",
                sources=[{"title": "LinkUp", "url": "https://linkup.so"}],
            )

    monkeypatch.setattr("linkup.LinkupClient", FakeClient)

    payload = SearchRequest(query="LinkUp CopilotKit", depth="deep", max_results=3)
    response = await run_linkup_search(payload, settings=Settings(linkup_api_key="test-linkup-key"))

    assert response == {
        "query": "LinkUp CopilotKit",
        "depth": "deep",
        "result": {
            "answer": "LinkUp and CopilotKit help agents produce cited UI.",
            "sources": [{"title": "LinkUp", "url": "https://linkup.so"}],
        },
    }
    assert calls == [
        {"api_key": "test-linkup-key"},
        {
            "query": "LinkUp CopilotKit",
            "depth": "deep",
            "output_type": "sourcedAnswer",
            "max_results": 3,
            "include_inline_citations": True,
            "include_sources": True,
            "timeout": 30,
        },
    ]
