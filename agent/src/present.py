"""Agent-side presentation link tool for genui.

The tool deliberately shells out to ``aw id request --team-auth`` instead of
reimplementing AWID request signing. That keeps hackathon auth on the same
real envelope path the server verifies.
"""
from __future__ import annotations

import json
import os
import subprocess
from typing import Any
from uuid import uuid4

from copilotkit import a2ui
from langchain.tools import tool

from src.catalog import CATALOG_ID

DEFAULT_SERVER_ORIGIN = "http://localhost:8200"
DEFAULT_TTL_SECONDS = 60 * 60 * 24


def _server_origin() -> str:
    return os.getenv("SERVER_ORIGIN", DEFAULT_SERVER_ORIGIN).rstrip("/")


def _aw_cwd() -> str | None:
    # Optional escape hatch for demos where the FastAPI agent runs outside the
    # initialized aw workspace. If unset, aw uses the agent process cwd/env.
    return os.getenv("GENUI_AW_CWD") or None


def _json_arg(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _run_aw_request(method: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    result = subprocess.run(
        [
            "aw",
            "id",
            "request",
            method,
            f"{_server_origin()}{path}",
            "--team-auth",
            "--raw",
            "--body",
            _json_arg(body),
        ],
        cwd=_aw_cwd(),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (
            (result.stderr or result.stdout).strip()
            or f"aw exited {result.returncode}"
        )
        raise RuntimeError(detail)
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"server returned non-JSON response: {result.stdout[:240]}"
        ) from exc
    if not isinstance(data, dict):
        raise RuntimeError("server returned JSON that was not an object")
    return data


def _coerce_envelope(surface_or_doc: str) -> dict[str, Any]:
    text = surface_or_doc.strip()
    if text:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            if isinstance(parsed.get("a2ui_operations"), list):
                return parsed
        if isinstance(parsed, list):
            return {"a2ui_operations": parsed}

    # If the caller passes prose rather than an envelope, present it as a small
    # readable A2UI surface so the tool remains callable with a document/ask.
    body = text or "The agent did not provide surface content."
    surface_id = f"present-{uuid4().hex[:10]}"
    operations = [
        a2ui.create_surface(surface_id, catalog_id=CATALOG_ID),
        a2ui.update_components(
            surface_id,
            [
                {
                    "id": "root",
                    "component": "Stack",
                    "children": ["eyebrow", "title", "body"],
                    "gap": "md",
                },
                {
                    "id": "eyebrow",
                    "component": "Overline",
                    "text": "Presented by agent",
                },
                {
                    "id": "title",
                    "component": "Heading",
                    "text": "Agent presentation",
                    "level": "1",
                },
                {"id": "body", "component": "Text", "text": body[:4000], "size": "md"},
            ],
        ),
    ]
    rendered = json.loads(a2ui.render(operations=operations))
    if isinstance(rendered, dict) and isinstance(
        rendered.get("a2ui_operations"), list
    ):
        return rendered
    return {"a2ui_operations": operations}


@tool()
def present_to_human(
    surface_or_doc: str,
    slug: str = "",
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> str:
    """Store an A2UI surface and return a safe /present/<token> URL.

    Args:
        surface_or_doc: A JSON A2UI envelope such as
            {"a2ui_operations":[...]} or raw operations array. If prose is
            supplied, it is wrapped in a simple A2UI text surface.
        slug: Optional human-readable artifact slug.
        ttl_seconds: Optional presentation-link lifetime. Defaults to 24h.
    """

    a2ui_envelope = _coerce_envelope(surface_or_doc)
    artifact_body: dict[str, Any] = {"a2ui": a2ui_envelope}
    if slug:
        artifact_body["slug"] = slug

    try:
        try:
            artifact = _run_aw_request("POST", "/v1/artifacts", artifact_body)
        except RuntimeError as exc:
            # Demo/chat runs are intentionally repeatable. If the model reuses a
            # human slug from a prior take, keep the friendly base but retry with
            # a short unique suffix instead of failing the presentation step.
            if slug and "409" in str(exc):
                artifact_body["slug"] = f"{slug}-{uuid4().hex[:8]}"
                artifact = _run_aw_request("POST", "/v1/artifacts", artifact_body)
            else:
                raise
        artifact_id = artifact.get("artifact_id")
        version = artifact.get("version")
        if not isinstance(artifact_id, str):
            raise RuntimeError(
                "POST /v1/artifacts response did not include artifact_id"
            )
        present_body: dict[str, Any] = {
            "artifact_id": artifact_id,
            "ttl_seconds": ttl_seconds,
        }
        if isinstance(version, int):
            present_body["version"] = version
        link = _run_aw_request("POST", "/v1/present", present_body)
    except (OSError, RuntimeError) as exc:
        return (
            "Presentation server unavailable; could not mint a safe link yet. "
            f"Start genui server at {_server_origin()} with AWID team-auth configured. "
            f"Details: {exc}"
        )

    url = link.get("url")
    if isinstance(url, str) and url:
        return url
    return "Presentation link minted, but the server response did not include url."
