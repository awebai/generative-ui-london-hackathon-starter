from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi import HTTPException

from atext.auth import Principal
from atext.config import Settings
from atext.repository import (
    create_artifact,
    get_presented_envelope,
    mint_presentation_link,
    revoke_presentation_link,
)


@pytest.fixture
def principal() -> Principal:
    return Principal(
        team_id="backend:example.com",
        did_key="did:key:zMember",
        did_aw=None,
        address="example.com/alice",
        alias="alice",
        certificate_id="cert-1",
        team_did_key="did:key:zTeam",
    )


class FakeDB:
    def __init__(self, *, team_id: str = "backend:example.com", version: int = 2) -> None:
        self.artifact_id = uuid4()
        self.team_id = team_id
        self.version = version
        self.inserted: dict[str, Any] | None = None
        self.revoked = False
        self.presented: dict[str, Any] = {"a2ui_operations": [{"createSurface": {"surfaceId": "s1"}}]}

    async def fetch_one(self, sql: str, *args: Any) -> dict[str, Any] | None:
        compact = " ".join(sql.split())
        if "FROM {{tables.artifacts}} a JOIN {{tables.artifact_versions}}" in compact:
            requested_team, requested_artifact, requested_version = args
            if requested_team != self.team_id or requested_artifact != self.artifact_id:
                return None
            return {"artifact_id": self.artifact_id, "version_number": requested_version or self.version}
        if "SELECT 1 FROM {{tables.artifact_versions}}" in compact:
            requested_artifact, requested_version = args
            if requested_artifact == self.artifact_id and int(requested_version) == self.version:
                return {"?column?": 1}
            return None
        if "SELECT token FROM {{tables.presentation_links}}" in compact:
            token, team_id = args
            if self.inserted is not None and token == self.inserted["token"] and team_id == self.team_id:
                return {"token": token}
            return None
        if "FROM {{tables.presentation_links}} p" in compact:
            token = args[0]
            if self.inserted is not None and token == self.inserted["token"] and not self.revoked:
                return {"envelope": self.presented}
            return None
        raise AssertionError(f"unexpected SQL: {compact}")

    async def execute(self, sql: str, *args: Any) -> None:
        compact = " ".join(sql.split())
        if compact.startswith("INSERT INTO {{tables.presentation_links}}"):
            token, artifact_id, version_number, team_id, did_key, expires_at = args
            self.inserted = {
                "token": token,
                "artifact_id": artifact_id,
                "version_number": version_number,
                "team_id": team_id,
                "did_key": did_key,
                "expires_at": expires_at,
            }
            return
        if compact.startswith("UPDATE {{tables.presentation_links}} SET revoked_at"):
            token, team_id = args
            if self.inserted is not None and token == self.inserted["token"] and team_id == self.team_id:
                self.revoked = True
            return
        raise AssertionError(f"unexpected SQL: {compact}")

    def transaction(self) -> Any:
        raise AssertionError("transaction not used in presentation-link tests")


@pytest.mark.asyncio
async def test_mint_presentation_link_is_opaque_team_scoped_and_expiring(principal: Principal) -> None:
    db = FakeDB()
    settings = Settings(public_origin="https://genui.example", default_present_ttl_seconds=3600, max_present_ttl_seconds=7200)

    response = await mint_presentation_link(
        db,  # type: ignore[arg-type]
        principal=principal,
        settings=settings,
        artifact_id=db.artifact_id,
        version=None,
        ttl_seconds=99_999,
    )

    assert db.inserted is not None
    assert response["token"] == db.inserted["token"]
    assert len(response["token"]) >= 43
    assert response["url"] == f"https://genui.example/present/{response['token']}"
    assert db.inserted["team_id"] == principal.team_id
    assert db.inserted["version_number"] == 2
    assert db.inserted["expires_at"] <= datetime.now(UTC) + timedelta(seconds=7205)

    assert await get_presented_envelope(db, token=response["token"]) == db.presented  # type: ignore[arg-type]

    await revoke_presentation_link(db, principal=principal, token=response["token"])  # type: ignore[arg-type]
    with pytest.raises(HTTPException) as raised:
        await get_presented_envelope(db, token=response["token"])  # type: ignore[arg-type]
    assert raised.value.status_code == 404


@pytest.mark.asyncio
async def test_mint_presentation_link_404s_for_cross_team_artifact(principal: Principal) -> None:
    db = FakeDB(team_id="other:team")

    with pytest.raises(HTTPException) as raised:
        await mint_presentation_link(
            db,  # type: ignore[arg-type]
            principal=principal,
            settings=Settings(),
            artifact_id=db.artifact_id,
            version=None,
            ttl_seconds=None,
        )

    assert raised.value.status_code == 404


@pytest.mark.asyncio
async def test_unknown_presentation_token_returns_404() -> None:
    db = FakeDB()

    with pytest.raises(HTTPException) as raised:
        await get_presented_envelope(db, token="missing")  # type: ignore[arg-type]

    assert raised.value.status_code == 404


@pytest.mark.asyncio
async def test_artifact_rejects_non_a2ui_envelope(principal: Principal) -> None:
    db = FakeDB()

    with pytest.raises(HTTPException) as raised:
        await create_artifact(
            db,  # type: ignore[arg-type]
            principal=principal,
            kind="a2ui",
            slug=None,
            envelope={"not_a2ui_operations": []},
        )

    assert raised.value.status_code == 400
