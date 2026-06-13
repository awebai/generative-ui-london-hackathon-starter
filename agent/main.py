"""Retired LangGraph sidecar.

GenUI no longer runs a concierge/chat service. Human-facing agents call the
cert-auth server directly with ``aw id request --team-auth``:

- POST /v1/search for server-side LinkUp search
- POST /v1/artifacts to store an A2UI doc view
- POST /v1/present to mint the human URL

This tiny app exists only so old process supervisors fail clearly instead of
silently starting the retired /fixed and /dynamic AG-UI endpoints.
"""
from __future__ import annotations

import uvicorn
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Retired genui agent sidecar")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "status": "retired",
        "message": "Use the genui server directly; the concierge LangGraph service is retired.",
    }


@app.api_route("/{_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def retired(_path: str) -> None:
    raise HTTPException(status_code=410, detail="The genui concierge agent service is retired.")


def main() -> None:
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8123,
        reload=True,
    )


if __name__ == "__main__":
    main()
