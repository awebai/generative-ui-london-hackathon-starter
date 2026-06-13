from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request
from pgdbm import AsyncDatabaseManager

from atext.auth import AWIDTeamCache, Principal, authenticate_request
from atext.config import Settings, get_settings
from atext.db import GenUIDatabase
from atext.models import (
    ArtifactCreateResponse,
    ArtifactResponse,
    ArtifactSummary,
    CreateArtifactRequest,
    CreateDocumentRequest,
    CreatePresentationRequest,
    DocumentResponse,
    DocumentSummary,
    DocumentVersion,
    PresentationResponse,
)
from atext.repository import (
    append_version,
    create_artifact,
    create_document,
    get_artifact,
    get_document,
    get_presented_envelope,
    list_artifacts,
    list_documents,
    list_versions,
    mint_presentation_link,
    revoke_presentation_link,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    holder: dict[str, object] = {}

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        database = GenUIDatabase(resolved)
        await database.connect()
        holder["db"] = database
        holder["team_cache"] = AWIDTeamCache(
            registry_url=resolved.awid_registry_url,
            ttl_seconds=resolved.auth_cache_ttl_seconds,
        )
        try:
            yield
        finally:
            await database.disconnect()

    app = FastAPI(title="genui server", version="0.1.0", lifespan=lifespan)

    def db() -> AsyncDatabaseManager:
        database = holder.get("db")
        if not isinstance(database, GenUIDatabase):
            raise RuntimeError("genui database is not initialized")
        return database.db

    def team_cache() -> AWIDTeamCache:
        cache = holder.get("team_cache")
        if not isinstance(cache, AWIDTeamCache):
            raise RuntimeError("genui auth cache is not initialized")
        return cache

    async def principal(
        request: Request,
        database: Annotated[AsyncDatabaseManager, Depends(db)],
        cache: Annotated[AWIDTeamCache, Depends(team_cache)],
    ) -> Principal:
        return await authenticate_request(request, settings=resolved, team_cache=cache, db=database)

    @app.get("/health")
    @app.get("/live")
    @app.get("/ready")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "genui-server"}

    @app.post("/v1/documents", response_model=DocumentResponse)
    async def create_document_route(
        request: Request,
        actor: Annotated[Principal, Depends(principal)],
        database: Annotated[AsyncDatabaseManager, Depends(db)],
    ) -> dict:
        payload = CreateDocumentRequest.model_validate(await request.json())
        return await create_document(
            database,
            principal=actor,
            slug=payload.slug,
            title=payload.title,
            body=payload.body,
        )

    @app.get("/v1/documents", response_model=list[DocumentSummary])
    async def list_documents_route(
        actor: Annotated[Principal, Depends(principal)],
        database: Annotated[AsyncDatabaseManager, Depends(db)],
    ) -> list[dict]:
        return await list_documents(database, principal=actor)

    @app.get("/v1/documents/{slug}", response_model=DocumentResponse)
    async def get_document_route(
        slug: str,
        actor: Annotated[Principal, Depends(principal)],
        database: Annotated[AsyncDatabaseManager, Depends(db)],
    ) -> dict:
        return await get_document(database, principal=actor, slug=slug)

    @app.post("/v1/documents/{slug}/versions", response_model=DocumentResponse)
    async def append_version_route(
        slug: str,
        request: Request,
        actor: Annotated[Principal, Depends(principal)],
        database: Annotated[AsyncDatabaseManager, Depends(db)],
    ) -> dict:
        try:
            body = (await request.body()).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="Version body must be valid UTF-8") from exc
        return await append_version(database, principal=actor, slug=slug, body=body)

    @app.get("/v1/documents/{slug}/versions", response_model=list[DocumentVersion])
    async def list_versions_route(
        slug: str,
        actor: Annotated[Principal, Depends(principal)],
        database: Annotated[AsyncDatabaseManager, Depends(db)],
    ) -> list[dict]:
        return await list_versions(database, principal=actor, slug=slug)

    @app.post("/v1/artifacts", response_model=ArtifactCreateResponse)
    async def create_artifact_route(
        request: Request,
        actor: Annotated[Principal, Depends(principal)],
        database: Annotated[AsyncDatabaseManager, Depends(db)],
    ) -> dict:
        raw_payload = await request.json()
        if not isinstance(raw_payload, dict):
            raise HTTPException(status_code=400, detail="Artifact envelope must be a JSON object")
        if "envelope" in raw_payload:
            payload = CreateArtifactRequest.model_validate(raw_payload)
            slug = payload.slug
            kind = payload.kind
            envelope = payload.envelope
        else:
            slug = None
            kind = "a2ui"
            envelope = raw_payload
        artifact = await create_artifact(database, principal=actor, kind=kind, slug=slug, envelope=envelope)
        return {"artifact_id": artifact["artifact_id"], "version": artifact["current_version"]}

    @app.get("/v1/artifacts", response_model=list[ArtifactSummary])
    async def list_artifacts_route(
        actor: Annotated[Principal, Depends(principal)],
        database: Annotated[AsyncDatabaseManager, Depends(db)],
    ) -> list[dict]:
        return await list_artifacts(database, principal=actor)

    @app.get("/v1/artifacts/{artifact_id}", response_model=ArtifactResponse)
    async def get_artifact_route(
        artifact_id: UUID,
        actor: Annotated[Principal, Depends(principal)],
        database: Annotated[AsyncDatabaseManager, Depends(db)],
    ) -> dict:
        return await get_artifact(database, principal=actor, artifact_id=artifact_id)

    @app.post("/v1/present", response_model=PresentationResponse)
    async def create_presentation_route(
        request: Request,
        actor: Annotated[Principal, Depends(principal)],
        database: Annotated[AsyncDatabaseManager, Depends(db)],
    ) -> dict:
        payload = CreatePresentationRequest.model_validate(await request.json())
        return await mint_presentation_link(
            database,
            principal=actor,
            settings=resolved,
            artifact_id=payload.artifact_id,
            version=payload.version,
            ttl_seconds=payload.ttl_seconds,
        )

    @app.post("/v1/present/{token}/revoke")
    async def revoke_presentation_route(
        token: str,
        actor: Annotated[Principal, Depends(principal)],
        database: Annotated[AsyncDatabaseManager, Depends(db)],
    ) -> dict[str, bool]:
        await revoke_presentation_link(database, principal=actor, token=token)
        return {"revoked": True}

    @app.get("/present/{token}")
    async def present_route(
        token: str,
        database: Annotated[AsyncDatabaseManager, Depends(db)],
    ) -> dict:
        return await get_presented_envelope(database, token=token)

    return app


app = create_app()
