from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import httpx
import pytest

pytestmark = pytest.mark.e2e

SERVER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SERVER_ROOT.parent
AWID_URL = os.environ.get("GENUI_E2E_AWID_URL", "http://127.0.0.1:18011")
POSTGRES_URL = os.environ.get(
    "GENUI_E2E_DATABASE_URL",
    "postgresql://genui:genui@127.0.0.1:55433/genui",
)
COMPOSE = ["docker", "compose", "-p", "genui-e2e", "-f", str(REPO_ROOT / "docker-compose.e2e.yml")]


@dataclass(frozen=True)
class CapturedRequest:
    method: str
    path: str
    headers: dict[str, str]
    body: bytes


class RecordingProxy(ThreadingHTTPServer):
    backend_origin: str
    last_request: CapturedRequest | None

    def __init__(self, server_address: tuple[str, int], backend_origin: str) -> None:
        super().__init__(server_address, _RecordingProxyHandler)
        self.backend_origin = backend_origin.rstrip("/")
        self.last_request = None


class _RecordingProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    @property
    def proxy(self) -> RecordingProxy:
        return self.server  # type: ignore[return-value]

    def do_GET(self) -> None:  # noqa: N802
        self._proxy()

    def do_POST(self) -> None:  # noqa: N802
        self._proxy()

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _proxy(self) -> None:
        length = int(self.headers.get("Content-Length") or "0")
        body = self.rfile.read(length) if length else b""
        headers = {key: value for key, value in self.headers.items()}
        self.proxy.last_request = CapturedRequest(self.command, self.path, headers, body)
        forward_headers = {
            key: value
            for key, value in headers.items()
            if key.lower() not in {"host", "content-length", "connection", "accept-encoding"}
        }
        try:
            with httpx.Client(timeout=15.0, follow_redirects=False) as client:
                upstream = client.request(
                    self.command,
                    f"{self.proxy.backend_origin}{self.path}",
                    headers=forward_headers,
                    content=body,
                )
        except Exception as exc:  # pragma: no cover
            response = str(exc).encode("utf-8", errors="replace")
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)
            self.close_connection = True
            return

        self.send_response(upstream.status_code)
        for key, value in upstream.headers.items():
            if key.lower() in {"content-length", "connection", "transfer-encoding", "content-encoding"}:
                continue
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(upstream.content)))
        self.end_headers()
        self.wfile.write(upstream.content)
        self.close_connection = True


@dataclass(frozen=True)
class RunningServer:
    origin: str
    backend_origin: str
    proxy: RecordingProxy


@dataclass(frozen=True)
class AWWorkspace:
    path: Path
    env: dict[str, str]


@dataclass(frozen=True)
class E2ETeam:
    workspace: AWWorkspace
    namespace: str
    team: str
    team_id: str
    alias: str
    address: str
    did_key: str
    certificate_id: str


def _require_e2e_enabled() -> None:
    if os.environ.get("GENUI_E2E") != "1":
        pytest.skip("set GENUI_E2E=1 or run `make e2e` to execute docker-backed e2e tests")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_http_ok(url: str, *, timeout_seconds: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            response = httpx.get(url, timeout=2.0)
            if response.status_code < 500:
                return
        except Exception as exc:  # pragma: no cover
            last_error = exc
        time.sleep(0.25)
    raise RuntimeError(f"timed out waiting for {url}: {last_error}")


def _compose(*args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [*COMPOSE, *args],
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            "docker compose command failed\n"
            f"cmd: {' '.join([*COMPOSE, *args])}\n"
            f"exit: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}\n"
        )
    return result


def _run_aw(workspace: AWWorkspace, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["aw", "--json", *args],
        cwd=workspace.path,
        env=workspace.env,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            "aw command failed\n"
            f"cmd: aw --json {' '.join(args)}\n"
            f"exit: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}\n"
        )
    return result


def _run_aw_json(workspace: AWWorkspace, *args: str) -> dict[str, Any]:
    result = _run_aw(workspace, *args)
    payload = json.loads(result.stdout)
    assert isinstance(payload, dict)
    return payload


def _aw_request(team: E2ETeam, method: str, url: str, *, body: str | None = None) -> subprocess.CompletedProcess[str]:
    args = ["aw", "id", "request", method, url, "--team-auth", "--raw"]
    if body is not None:
        args.extend(["--body", body])
    return subprocess.run(
        args,
        cwd=team.workspace.path,
        env=team.workspace.env,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )


def _assert_aw_success(result: subprocess.CompletedProcess[str], *, context: str) -> str:
    assert result.returncode == 0, (
        f"aw id request failed: {context}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    return result.stdout


def _assert_aw_status(result: subprocess.CompletedProcess[str], status: int, *, context: str) -> None:
    assert result.returncode != 0, f"expected HTTP {status} failure for {context}, got success: {result.stdout}"
    assert f"HTTP {status}" in result.stderr, (
        f"expected HTTP {status} for {context}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def _aw_json(result: subprocess.CompletedProcess[str], *, context: str) -> Any:
    stdout = _assert_aw_success(result, context=context)
    return json.loads(stdout)


@pytest.fixture(scope="session")
def genui_server() -> Iterator[RunningServer]:
    _require_e2e_enabled()
    _wait_http_ok(f"{AWID_URL}/health", timeout_seconds=60.0)

    backend_port = _free_port()
    proxy_port = _free_port()
    backend_origin = f"http://127.0.0.1:{backend_port}"
    proxy_origin = f"http://127.0.0.1:{proxy_port}"
    env = os.environ.copy()
    env.update(
        {
            "GENUI_SERVER_DATABASE_URL": POSTGRES_URL,
            "GENUI_SERVER_AWID_REGISTRY_URL": AWID_URL,
            "GENUI_SERVER_AUTH_CACHE_TTL_SECONDS": "2",
            "GENUI_SERVER_PUBLIC_ORIGIN": proxy_origin,
            "GENUI_SERVER_PRESENTATION_ORIGIN": proxy_origin,
        }
    )
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "atext.api:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(backend_port),
        ],
        cwd=SERVER_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    proxy = RecordingProxy(("127.0.0.1", proxy_port), backend_origin)
    thread = threading.Thread(target=proxy.serve_forever, name="genui-e2e-proxy", daemon=True)
    thread.start()
    try:
        _wait_http_ok(f"{proxy_origin}/health")
        yield RunningServer(origin=proxy_origin, backend_origin=backend_origin, proxy=proxy)
    finally:
        proxy.shutdown()
        proxy.server_close()
        thread.join(timeout=5)
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
        if proc.returncode not in (0, -15, -9, None):
            stdout = proc.stdout.read() if proc.stdout else ""
            stderr = proc.stderr.read() if proc.stderr else ""
            raise RuntimeError(f"uvicorn exited with {proc.returncode}\nstdout:\n{stdout}\nstderr:\n{stderr}")


@pytest.fixture()
def aw_workspace_factory(tmp_path: Path) -> Callable[[str], AWWorkspace]:
    _require_e2e_enabled()

    def make(name: str) -> AWWorkspace:
        workspace = tmp_path / name / "workspace"
        home = tmp_path / name / "home"
        workspace.mkdir(parents=True)
        home.mkdir(parents=True)
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(home),
                "AWEB_URL": "http://127.0.0.1:1",
                "AWID_REGISTRY_URL": AWID_URL,
                "NO_COLOR": "1",
            }
        )
        return AWWorkspace(path=workspace, env=env)

    return make


def _write_workspace_binding(workspace: AWWorkspace, *, team_id: str, alias: str, cert_path: str) -> None:
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    workspace_id = str(uuid.uuid4())
    (workspace.path / ".aw" / "workspace.yaml").write_text(
        f"""aweb_url: http://127.0.0.1:1
memberships:
  - team_id: {team_id}
    alias: {alias}
    workspace_id: {workspace_id}
    cert_path: {cert_path}
    joined_at: \"{now}\"
human_name: e2e
agent_type: agent
workspace_path: {workspace.path}
updated_at: \"{now}\"
""",
        encoding="utf-8",
    )


def _provision_team(workspace: AWWorkspace, *, alias: str) -> E2ETeam:
    unique = uuid.uuid4().hex[:12]
    namespace = f"genui-{unique}.test"
    team = "default"
    address = f"{namespace}/{alias}"

    _run_aw(
        workspace,
        "id",
        "create",
        "--domain",
        namespace,
        "--name",
        alias,
        "--registry",
        AWID_URL,
        "--skip-dns-verify",
    )
    _run_aw(workspace, "id", "team", "create", "--namespace", namespace, "--name", team, "--registry", AWID_URL)
    add_member = _run_aw_json(workspace, "id", "team", "add-member", "--namespace", namespace, "--team", team, "--member", address)
    certificate_id = str(add_member["certificate_id"])
    fetch_cert = _run_aw_json(
        workspace,
        "id",
        "team",
        "fetch-cert",
        "--namespace",
        namespace,
        "--team",
        team,
        "--cert-id",
        certificate_id,
        "--registry",
        AWID_URL,
    )
    team_id = f"{team}:{namespace}"
    _run_aw(workspace, "id", "team", "switch", team_id)
    _write_workspace_binding(workspace, team_id=team_id, alias=alias, cert_path=str(fetch_cert["cert_path"]))
    cert = _run_aw_json(workspace, "id", "cert", "show")
    return E2ETeam(
        workspace=workspace,
        namespace=namespace,
        team=team,
        team_id=team_id,
        alias=alias,
        address=address,
        did_key=str(cert["member_did_key"]),
        certificate_id=certificate_id,
    )


def _create_artifact(server: RunningServer, team: E2ETeam, *, slug: str, marker: str, named_team_id: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "a2ui": {"a2ui_operations": [{"createSurface": {"surfaceId": marker}}]},
        "slug": slug,
    }
    if named_team_id is not None:
        payload["team_id"] = named_team_id
    result = _aw_request(team, "POST", f"{server.origin}/v1/artifacts", body=json.dumps(payload, separators=(",", ":")))
    data = _aw_json(result, context=f"create artifact {slug}")
    assert isinstance(data, dict)
    return data


def _create_document(server: RunningServer, team: E2ETeam, *, slug: str, body: dict[str, Any]) -> dict[str, Any]:
    result = _aw_request(team, "POST", f"{server.origin}/v1/documents", body=json.dumps(body, separators=(",", ":")))
    data = _aw_json(result, context=f"create document {slug}")
    assert isinstance(data, dict)
    return data


def test_cross_team_artifact_and_present_isolation(
    genui_server: RunningServer,
    aw_workspace_factory: Callable[[str], AWWorkspace],
) -> None:
    team_a = _provision_team(aw_workspace_factory("team-a"), alias="concierge")
    team_b = _provision_team(aw_workspace_factory("team-b"), alias="concierge")

    artifact = _create_artifact(genui_server, team_a, slug="team-a-surface", marker="team-a-surface")
    artifact_id = artifact["artifact_id"]

    team_a_read = _aw_json(
        _aw_request(team_a, "GET", f"{genui_server.origin}/v1/artifacts/{artifact_id}"),
        context="team A reads own artifact",
    )
    assert team_a_read["artifact_id"] == artifact_id
    assert team_a_read["team_id"] == team_a.team_id
    assert team_a_read["a2ui"]["a2ui_operations"][0]["createSurface"]["surfaceId"] == "team-a-surface"

    team_b_read = _aw_request(team_b, "GET", f"{genui_server.origin}/v1/artifacts/{artifact_id}")
    _assert_aw_status(team_b_read, 404, context="team B reads team A artifact id")

    team_b_list = _aw_json(_aw_request(team_b, "GET", f"{genui_server.origin}/v1/artifacts"), context="team B lists artifacts")
    assert isinstance(team_b_list, list)
    assert artifact_id not in {item["artifact_id"] for item in team_b_list}

    cross_mint = _aw_request(
        team_b,
        "POST",
        f"{genui_server.origin}/v1/present",
        body=json.dumps({"artifact_id": artifact_id, "ttl_seconds": 3600}, separators=(",", ":")),
    )
    _assert_aw_status(cross_mint, 404, context="team B mints present link for team A artifact")

    named = _create_document(
        genui_server,
        team_a,
        slug="body-named-team",
        body={"team_id": team_b.team_id, "slug": "body-named-team", "title": "Body named team", "body": "belongs to A"},
    )
    assert named["slug"] == "body-named-team"
    assert _assert_aw_success(
        _aw_request(team_a, "GET", f"{genui_server.origin}/v1/documents/body-named-team"),
        context="team A reads body-named document",
    )
    _assert_aw_status(
        _aw_request(team_b, "GET", f"{genui_server.origin}/v1/documents/body-named-team"),
        404,
        context="team B cannot read body-named document",
    )

    own_mint = _aw_json(
        _aw_request(
            team_a,
            "POST",
            f"{genui_server.origin}/v1/present",
            body=json.dumps({"artifact_id": artifact_id, "ttl_seconds": 3600}, separators=(",", ":")),
        ),
        context="team A mints own present link",
    )
    public = httpx.get(own_mint["url"], timeout=10.0)
    assert public.status_code == 200, public.text
    public_body = public.json()
    assert set(public_body) == {"a2ui", "expires_at"}
    assert public_body["a2ui"]["a2ui_operations"][0]["createSurface"]["surfaceId"] == "team-a-surface"
    assert "team_id" not in public_body
    assert "artifact_id" not in public_body
    assert "created_by_alias" not in public_body

    missing = httpx.get(f"{genui_server.origin}/present/not-a-token", timeout=10.0)
    assert missing.status_code == 404, missing.text
