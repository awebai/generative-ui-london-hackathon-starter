from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException
from pgdbm import AsyncDatabaseManager

from atext.auth import Principal
from atext.config import Settings


def _json_value(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=500, detail="Stored A2UI envelope is malformed") from exc
    return value


def _json_bytes(value: Any) -> str:
    try:
        return json.dumps(value, separators=(",", ":"))
    except TypeError as exc:
        raise HTTPException(status_code=400, detail="A2UI envelope must be JSON serializable") from exc


async def create_document(
    db: AsyncDatabaseManager,
    *,
    principal: Principal,
    slug: str,
    title: str,
    body: str,
) -> dict:
    document_id = uuid4()
    version_id = uuid4()
    try:
        async with db.transaction() as tx:
            await tx.execute(
                """
                INSERT INTO {{tables.documents}}
                  (document_id, team_id, slug, title, created_by_did_key, created_by_did_aw, created_by_alias)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                document_id,
                principal.team_id,
                slug,
                title,
                principal.did_key,
                principal.did_aw,
                principal.alias,
            )
            await tx.execute(
                """
                INSERT INTO {{tables.document_versions}}
                  (version_id, document_id, version_number, body, created_by_did_key,
                   created_by_did_aw, created_by_address, created_by_alias, certificate_id)
                VALUES ($1, $2, 1, $3, $4, $5, $6, $7, $8)
                """,
                version_id,
                document_id,
                body,
                principal.did_key,
                principal.did_aw,
                principal.address,
                principal.alias,
                principal.certificate_id,
            )
    except Exception as exc:
        if "unique" in str(exc).lower():
            raise HTTPException(status_code=409, detail="Document slug already exists for this team") from exc
        raise
    return await get_document(db, principal=principal, slug=slug)


async def list_documents(db: AsyncDatabaseManager, *, principal: Principal) -> list[dict]:
    rows = await db.fetch_all(
        """
        SELECT d.document_id, d.slug, d.title, d.created_at, d.updated_at,
               COALESCE(MAX(v.version_number), 0) AS current_version
        FROM {{tables.documents}} d
        LEFT JOIN {{tables.document_versions}} v ON v.document_id = d.document_id
        WHERE d.team_id = $1
        GROUP BY d.document_id, d.slug, d.title, d.created_at, d.updated_at
        ORDER BY d.updated_at DESC, d.slug ASC
        """,
        principal.team_id,
    )
    return [dict(row) for row in rows]


async def get_document(db: AsyncDatabaseManager, *, principal: Principal, slug: str) -> dict:
    row = await db.fetch_one(
        """
        SELECT d.document_id, d.slug, d.title, d.created_at, d.updated_at,
               v.version_id, v.version_number, v.body, v.created_by_did_key,
               v.created_by_did_aw, v.created_by_address, v.created_by_alias,
               v.certificate_id, v.created_at AS version_created_at
        FROM {{tables.documents}} d
        JOIN {{tables.document_versions}} v ON v.document_id = d.document_id
        WHERE d.team_id = $1 AND d.slug = $2
        ORDER BY v.version_number DESC
        LIMIT 1
        """,
        principal.team_id,
        slug,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Document not found")
    data = dict(row)
    return {
        "document_id": data["document_id"],
        "slug": data["slug"],
        "title": data["title"],
        "body": data["body"],
        "current_version": data["version_number"],
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
        "latest": {
            "version_id": data["version_id"],
            "version_number": data["version_number"],
            "body": data["body"],
            "created_by_did_key": data["created_by_did_key"],
            "created_by_did_aw": data["created_by_did_aw"],
            "created_by_address": data["created_by_address"],
            "created_by_alias": data["created_by_alias"],
            "certificate_id": data["certificate_id"],
            "created_at": data["version_created_at"],
        },
    }


async def append_version(db: AsyncDatabaseManager, *, principal: Principal, slug: str, body: str) -> dict:
    document = await db.fetch_one(
        "SELECT document_id FROM {{tables.documents}} WHERE team_id = $1 AND slug = $2",
        principal.team_id,
        slug,
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    document_id: UUID = document["document_id"]
    version_id = uuid4()
    async with db.transaction() as tx:
        current = await tx.fetch_one(
            "SELECT COALESCE(MAX(version_number), 0) AS n FROM {{tables.document_versions}} WHERE document_id = $1",
            document_id,
        )
        next_version = int(current["n"] if current is not None else 0) + 1
        await tx.execute(
            """
            INSERT INTO {{tables.document_versions}}
              (version_id, document_id, version_number, body, created_by_did_key,
               created_by_did_aw, created_by_address, created_by_alias, certificate_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            version_id,
            document_id,
            next_version,
            body,
            principal.did_key,
            principal.did_aw,
            principal.address,
            principal.alias,
            principal.certificate_id,
        )
        await tx.execute("UPDATE {{tables.documents}} SET updated_at = NOW() WHERE document_id = $1", document_id)
    return await get_document(db, principal=principal, slug=slug)


async def list_versions(db: AsyncDatabaseManager, *, principal: Principal, slug: str) -> list[dict]:
    document = await db.fetch_one(
        "SELECT document_id FROM {{tables.documents}} WHERE team_id = $1 AND slug = $2",
        principal.team_id,
        slug,
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    rows = await db.fetch_all(
        """
        SELECT version_id, version_number, NULL::TEXT AS body, created_by_did_key,
               created_by_did_aw, created_by_address, created_by_alias,
               certificate_id, created_at
        FROM {{tables.document_versions}}
        WHERE document_id = $1
        ORDER BY version_number DESC
        """,
        document["document_id"],
    )
    return [dict(row) for row in rows]


async def create_artifact(
    db: AsyncDatabaseManager,
    *,
    principal: Principal,
    kind: str,
    slug: str | None,
    a2ui: Any,
) -> dict:
    artifact_id = uuid4()
    artifact_version_id = uuid4()
    try:
        async with db.transaction() as tx:
            await tx.execute(
                """
                INSERT INTO {{tables.artifacts}}
                  (artifact_id, team_id, slug, kind, created_by_did_key, created_by_did_aw,
                   created_by_address, created_by_alias, certificate_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                artifact_id,
                principal.team_id,
                slug,
                kind,
                principal.did_key,
                principal.did_aw,
                principal.address,
                principal.alias,
                principal.certificate_id,
            )
            await tx.execute(
                """
                INSERT INTO {{tables.artifact_versions}}
                  (artifact_version_id, artifact_id, version_number, envelope, created_by_did_key,
                   created_by_did_aw, created_by_address, created_by_alias, certificate_id)
                VALUES ($1, $2, 1, $3::jsonb, $4, $5, $6, $7, $8)
                """,
                artifact_version_id,
                artifact_id,
                _json_bytes(a2ui),
                principal.did_key,
                principal.did_aw,
                principal.address,
                principal.alias,
                principal.certificate_id,
            )
    except Exception as exc:
        if "unique" in str(exc).lower():
            raise HTTPException(status_code=409, detail="Artifact slug already exists for this team") from exc
        raise
    return await get_artifact(db, principal=principal, artifact_id=artifact_id)


async def list_artifacts(db: AsyncDatabaseManager, *, principal: Principal) -> list[dict]:
    rows = await db.fetch_all(
        """
        SELECT a.artifact_id, a.slug, a.kind, a.created_at, a.updated_at,
               COALESCE(MAX(v.version_number), 0) AS current_version
        FROM {{tables.artifacts}} a
        LEFT JOIN {{tables.artifact_versions}} v ON v.artifact_id = a.artifact_id
        WHERE a.team_id = $1
        GROUP BY a.artifact_id, a.slug, a.kind, a.created_at, a.updated_at
        ORDER BY a.updated_at DESC, a.created_at DESC
        """,
        principal.team_id,
    )
    return [dict(row) for row in rows]


async def get_artifact(db: AsyncDatabaseManager, *, principal: Principal, artifact_id: UUID) -> dict:
    row = await db.fetch_one(
        """
        SELECT a.artifact_id, a.slug, a.kind, a.created_at, a.updated_at,
               a.team_id, v.artifact_version_id, v.version_number, v.envelope, v.created_by_did_key,
               v.created_by_did_aw, v.created_by_address, v.created_by_alias,
               v.certificate_id, v.created_at AS version_created_at
        FROM {{tables.artifacts}} a
        JOIN {{tables.artifact_versions}} v ON v.artifact_id = a.artifact_id
        WHERE a.team_id = $1 AND a.artifact_id = $2
        ORDER BY v.version_number DESC
        LIMIT 1
        """,
        principal.team_id,
        artifact_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return _artifact_response(row)


def _artifact_response(row: Any) -> dict[str, Any]:
    data = dict(row)
    return {
        "artifact_id": data["artifact_id"],
        "team_id": data["team_id"],
        "slug": data["slug"],
        "kind": data["kind"],
        "current_version": data["version_number"],
        "a2ui": _json_value(data["envelope"]),
        "created_by_alias": data["created_by_alias"],
        "created_at": data["created_at"],
    }


async def mint_presentation_link(
    db: AsyncDatabaseManager,
    *,
    principal: Principal,
    settings: Settings,
    artifact_id: UUID,
    version: int | None,
    ttl_seconds: int | None,
) -> dict[str, Any]:
    selected = await db.fetch_one(
        """
        SELECT a.artifact_id, COALESCE($3::integer, MAX(v.version_number)) AS version_number
        FROM {{tables.artifacts}} a
        JOIN {{tables.artifact_versions}} v ON v.artifact_id = a.artifact_id
        WHERE a.team_id = $1 AND a.artifact_id = $2
        GROUP BY a.artifact_id
        """,
        principal.team_id,
        artifact_id,
        version,
    )
    if selected is None or selected["version_number"] is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    version_number = int(selected["version_number"])
    exists = await db.fetch_one(
        "SELECT 1 FROM {{tables.artifact_versions}} WHERE artifact_id = $1 AND version_number = $2",
        artifact_id,
        version_number,
    )
    if exists is None:
        raise HTTPException(status_code=404, detail="Artifact version not found")

    ttl = min(ttl_seconds or settings.default_present_ttl_seconds, settings.max_present_ttl_seconds)
    expires_at = datetime.now(UTC) + timedelta(seconds=ttl)
    token = secrets.token_urlsafe(32)
    await db.execute(
        """
        INSERT INTO {{tables.presentation_links}}
          (token, artifact_id, version_number, team_id, created_by_did_key, expires_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        token,
        artifact_id,
        version_number,
        principal.team_id,
        principal.did_key,
        expires_at,
    )
    presentation_origin = (settings.presentation_origin or settings.public_origin).rstrip("/")
    return {
        "token": token,
        "url": f"{presentation_origin}/present/{token}",
        "expires_at": expires_at,
    }


async def revoke_presentation_link(
    db: AsyncDatabaseManager,
    *,
    principal: Principal,
    token: str,
) -> None:
    row = await db.fetch_one(
        "SELECT token FROM {{tables.presentation_links}} WHERE token = $1 AND team_id = $2",
        token,
        principal.team_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Presentation not found")
    await db.execute(
        "UPDATE {{tables.presentation_links}} SET revoked_at = NOW() WHERE token = $1 AND team_id = $2",
        token,
        principal.team_id,
    )


async def get_presented_envelope(db: AsyncDatabaseManager, *, token: str) -> dict[str, Any]:
    row = await db.fetch_one(
        """
        SELECT v.envelope, p.expires_at
        FROM {{tables.presentation_links}} p
        JOIN {{tables.artifact_versions}} v
          ON v.artifact_id = p.artifact_id AND v.version_number = p.version_number
        WHERE p.token = $1 AND p.revoked_at IS NULL AND p.expires_at > NOW()
        """,
        token,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return {"a2ui": _json_value(row["envelope"]), "expires_at": row["expires_at"]}
