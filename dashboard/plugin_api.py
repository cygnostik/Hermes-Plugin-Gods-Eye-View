"""GEV dashboard API: explicit desktop lifecycle and profile-safe onboarding.

Mounted by Hermes under /api/plugins/gods-eye-view. No import-time side effects.
Updates affect ONLY the configured official upstream app, never this plugin.
"""
from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys
import time
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
from threading import RLock

import httpx
from fastapi import APIRouter, HTTPException

# Dashboard routers are imported as standalone modules by Hermes.
_spec = importlib.util.spec_from_file_location("gev_dashboard_settings", Path(__file__).resolve().parents[1] / "settings.py")
settings = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(settings)
router = APIRouter()
_MUTATION_LOCK = RLock()
_CONFIG = ContextVar("gev_request_config", default=None)
_STATES: dict = {}
HERMES_BRIDGE = frozenset({
    "OPENAI_API_KEY", "AISSTREAM_API_KEY", "FIRMS_MAP_KEY", "TOMTOM_API_KEY",
    "CESIUM_ION_TOKEN", "OPENSKY_CLIENT_ID", "OPENSKY_CLIENT_SECRET",
    "LL2_API_TOKEN", "GOOGLE_MAPS_API_KEY", "GOOGLE_MAPS_SERVER_API_KEY",
})


def _config() -> dict:
    cached = _CONFIG.get()
    if cached is not None:
        return cached
    try:
        return {**settings.load(), "data": settings.data_path()}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None


def _state() -> dict:
    c = _config()
    identity = (str(c["data"]), c["root"], c["node"], c["port"])
    return _STATES.setdefault(identity, {"proc": None, "updates": {"commits_behind": None, "checked_at": None}})


def _scoped(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        token = _CONFIG.set(_config())
        try:
            return fn(*args, **kwargs)
        finally:
            _CONFIG.reset(token)
    return wrapped


def _exclusive(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not _MUTATION_LOCK.acquire(blocking=False):
            raise HTTPException(409, "Another GEV action is in progress. Wait for it to finish.")
        try:
            return _scoped(fn)(*args, **kwargs)
        finally:
            _MUTATION_LOCK.release()
    return wrapped


def _require_supported_platform():
    if sys.platform not in ("win32", "darwin"):
        raise HTTPException(400, "GEV lifecycle management supports Windows and macOS.")


def _url() -> str:
    return f"http://localhost:{_config()['port']}/"


def _node_env() -> dict[str, str]:
    return settings.child_env(Path(_config()["node"]))


def _run(cmd: list[str], cwd: Path, timeout: int = 120) -> tuple[int, str]:
    try:
        result = subprocess.run(cmd, cwd=str(cwd), env=_node_env(),
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                                capture_output=True, text=True, timeout=timeout,
                                encoding="utf-8", errors="replace")
        return result.returncode, (result.stdout or "") + (result.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except OSError:
        return 1, "Could not execute command."


def _port_open(port: int) -> bool:
    for family in (socket.AF_INET, socket.AF_INET6):
        addr = ("127.0.0.1", port) if family == socket.AF_INET else ("::1", port)
        try:
            with socket.socket(family, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                if sock.connect_ex(addr) == 0:
                    return True
        except OSError:
            continue
    return False


def _server_pid() -> int | None:
    """Only adopt an exact runtime/checkout/Vite loopback listener."""
    import psutil
    c = _config()
    root, node = Path(c["root"]), Path(c["node"])
    # macOS denies system-wide socket enumeration without root. Inspect only
    # processes matching our executable, checkout and script before their sockets.
    for proc in psutil.process_iter():
        try:
            if Path(proc.exe()).resolve() != node.resolve() or Path(proc.cwd()).resolve() != root.resolve():
                continue
            args = proc.cmdline()
            script = Path(args[1]) if len(args) > 1 else Path("missing")
            if not script.is_absolute():
                script = root / script
            if script.resolve() != (root / "node_modules/vite/bin/vite.js").resolve():
                continue
            connections = getattr(proc, "net_connections", None) or proc.connections
            for conn in connections(kind="tcp"):
                if conn.status == psutil.CONN_LISTEN and conn.laddr and conn.laddr.port == c["port"] and conn.laddr.ip in ("127.0.0.1", "::1"):
                    return proc.pid
        except (psutil.Error, OSError):
            continue
    return None


@router.get("/status")
def status() -> dict:
    # No mkdir, subprocess, git fetch or process enumeration. Unconfigured means
    # no network probe either (especially not a different profile's default port).
    try:
        c = _config()
    except HTTPException as exc:
        return {"configured": False, "configuration_error": exc.detail,
                "installed": False, "running": False, "url": "http://localhost:4173/", "port": 4173,
                "version": None, "commits_behind": None, "checked_at": None,
                "pid": None, "node24_ok": False, "keys": None, "platform_supported": sys.platform in ("win32", "darwin")}
    token = _CONFIG.set(c)
    try:
        keys = _gev_key_status()
        root = Path(c["root"])
        try:
            version = json.loads((root / "package.json").read_text(encoding="utf-8")).get("version")
        except (OSError, ValueError, AttributeError):
            version = None
        state = _state()
        proc = state["proc"]
        return {"configured": True, "configuration_error": None,
                "installed": (root / "package.json").is_file(), "running": keys is not None,
                "url": _url(), "port": c["port"], "version": version, **state["updates"],
                "pid": proc.pid if proc is not None and proc.poll() is None else None,
                # Historical frontend field name; Node 26 is supported too.
                "node24_ok": Path(c["node"]).is_file(), "node_version": c["node_version"],
                "keys": keys, "platform_supported": sys.platform in ("win32", "darwin")}
    finally:
        _CONFIG.reset(token)


def _log_event(event: str):
    # Do NOT persist raw upstream stdout/stderr: a provider may print a key.
    # Diagnostics intentionally contain only plugin-owned lifecycle messages.
    from plugins.plugin_storage import plugin_data_dir
    log = plugin_data_dir("gods-eye-view") / "gev-runtime.log"
    if log.exists() and log.stat().st_size > 2_000_000:
        log.replace(log.with_suffix(".previous.log"))
    with log.open("a", encoding="utf-8") as stream:
        stream.write(event + "\n")


@router.post("/start")
@_exclusive
def start_gev() -> dict:
    _require_supported_platform()
    c = _config()
    if _gev_key_status() is not None:
        return {"ok": True, "already_running": True, "url": _url()}
    if _port_open(c["port"]):
        raise HTTPException(409, f"Port {c['port']} is occupied but is not responding as GEV. No process was changed.")
    state = _state()
    if state["proc"] is not None and state["proc"].poll() is None:
        raise HTTPException(409, "GEV is still starting. Refresh status before retrying.")
    root, node = Path(c["root"]), Path(c["node"])
    if not node.is_file() or not (root / "node_modules/vite/bin/vite.js").is_file():
        raise HTTPException(400, "Configured Node or GEV dependencies are missing. Install upstream dependencies explicitly using its official instructions. " + settings.SETUP_HINT)
    try:
        settings.node_version(node, root)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    _log_event("Starting GEV; upstream output suppressed to keep provider values out of logs.")
    try:
        proc = subprocess.Popen([str(node), str(root / "node_modules/vite/bin/vite.js"), "--host", "localhost", "--port", str(c["port"]), "--strictPort"],
                                cwd=str(root), env=_node_env(), stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=sys.platform != "win32",
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except OSError:
        raise HTTPException(500, "Could not launch the configured Node runtime.") from None
    state["proc"] = proc
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if _gev_key_status() is not None:
            _log_event("GEV responded to its setup-status probe.")
            return {"ok": True, "url": _url(), "pid": proc.pid}
        if proc.poll() is not None:
            _log_event("GEV exited during startup.")
            raise HTTPException(500, "GEV exited during startup. Check Node and the upstream dependency installation; raw upstream output is not logged.")
        time.sleep(0.5)
    raise HTTPException(504, "GEV startup timed out. The process may still be starting; refresh status before retrying.")


@router.post("/stop")
@_exclusive
def stop_gev() -> dict:
    _require_supported_platform()
    c = _config()
    pid = _server_pid()
    if _port_open(c["port"]) and pid is None:
        raise HTTPException(409, f"Port {c['port']} belongs to an unverified process. Nothing was stopped.")
    stopped = []
    if pid:
        if sys.platform == "win32":
            code, _ = _run(["taskkill", "/PID", str(pid), "/T", "/F"], cwd=Path(c["root"]), timeout=30)
            if code:
                raise HTTPException(500, "GEV stop command failed. Refresh status; no success was assumed.")
        else:
            import psutil
            try:
                parent = psutil.Process(pid)
                processes = parent.children(recursive=True) + [parent]
                for process in processes:
                    try:
                        process.terminate()
                    except psutil.NoSuchProcess:
                        pass
                _, alive = psutil.wait_procs(processes, timeout=10)
                for process in alive:
                    try:
                        process.kill()
                    except psutil.NoSuchProcess:
                        pass
                _, alive = psutil.wait_procs(alive, timeout=5)
                if alive:
                    raise HTTPException(500, "GEV did not exit after the stop attempt.")
            except psutil.NoSuchProcess:
                pass  # The verified parent exited before process-tree inspection.
            except psutil.Error:
                raise HTTPException(500, "GEV stop failed. Refresh status; no success was assumed.") from None
        stopped.append(pid)
    state = _state()
    proc = state["proc"]
    if proc is not None and proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            raise HTTPException(500, "GEV did not exit after the stop attempt.") from None
        if proc.pid not in stopped:
            stopped.append(proc.pid)
    state["proc"] = None
    time.sleep(1)
    if _port_open(c["port"]):
        raise HTTPException(500, f"Port {c['port']} is still listening after the stop attempt. No success was assumed; refresh status.")
    return {"ok": True, "still_listening": False, "killed": stopped}


def _checked(stage: str, cmd: list[str], timeout: int = 120) -> str:
    code, out = _run(cmd, cwd=Path(_config()["root"]), timeout=timeout)
    if code != 0:
        raise HTTPException(500, f"{stage} failed (exit {code}). Update incomplete; retry to repair dependencies.")
    return out.strip()


def _upstream_checkout():
    c = _config()
    try:
        settings.validate_checkout(Path(c["root"]), Path(c["node"]))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None


@router.post("/updates/check")
@_exclusive
def check_updates() -> dict:
    from datetime import datetime, timezone
    _require_supported_platform()
    _upstream_checkout()
    _checked("git fetch", ["git", "fetch", "origin"], 120)
    count = _checked("git rev-list", ["git", "rev-list", "--count", "HEAD..origin/main"], 15)
    if not count.isdigit():
        raise HTTPException(500, "Git returned an invalid update count.")
    dirty = _checked("git status", ["git", "status", "--porcelain", "--untracked-files=normal"], 15)
    updates = _state()["updates"]
    updates.update(commits_behind=int(count), dirty=bool(dirty), checked_at=datetime.now(timezone.utc).isoformat())
    return {"ok": True, **updates}


@router.post("/update")
@_exclusive
def update_gev() -> dict:
    """Explicit upstream-app update, NEVER an update of the catalog plugin."""
    _require_supported_platform()
    c = _config()
    _upstream_checkout()
    if not c["npm_cli"] or not Path(c["npm_cli"]).is_file():
        raise HTTPException(400, "npm-cli.js is missing; configure --npm-cli before updating the upstream app. " + settings.SETUP_HINT)
    dirty = _checked("git status", ["git", "status", "--porcelain", "--untracked-files=normal"], 15)
    if dirty:
        raise HTTPException(409, "Update paused: the GEV checkout has local changes. They have been preserved; resolve or back them up before updating.")
    was_running = _port_open(c["port"])
    if was_running:
        stop_gev()
    _checked("git fetch", ["git", "fetch", "origin"])
    _checked("git pull", ["git", "pull", "--ff-only", "origin", "main"])
    _checked("npm ci", [c["node"], c["npm_cli"], "ci", "--ignore-scripts"], 900)
    _checked("esbuild install", [c["node"], "node_modules/esbuild/install.js"], 60)
    version = _checked("git rev-parse", ["git", "rev-parse", "--short", "HEAD"], 15)
    if was_running:
        start_gev()
    _state()["updates"].update(commits_behind=0, dirty=False)
    return {"ok": True, "version": version, "restarted": was_running}


def _gev_key_status() -> dict | None:
    try:
        with httpx.Client(timeout=5, trust_env=False, follow_redirects=False) as client:
            r = client.get(_url() + "api/setup/status", headers={"Origin": _url().rstrip("/")})
            if r.status_code == 200:
                value = r.json()
                if isinstance(value, dict) and isinstance(value.get("keys"), list) and type(value.get("setCount")) is int and type(value.get("total")) is int and value["total"] == len(value["keys"]) and all(isinstance(k, dict) and isinstance(k.get("id"), str) and isinstance(k.get("set"), bool) for k in value["keys"]):
                    return {"keys": [{field: k[field] for field in ("id", "title", "set", "description") if field in k} for k in value["keys"]], "setCount": value["setCount"], "total": value["total"]}
    except (httpx.HTTPError, ValueError, HTTPException):
        pass
    return None


@router.get("/keys")
def get_keys() -> dict:
    try:
        _config()
    except HTTPException:
        return {"gev_live_status": None}
    return {"gev_live_status": _gev_key_status()}


@router.post("/keys/hermes")
@_exclusive
def bridge_hermes_keys() -> dict:
    """Explicit opt-in bridge; the Hermes accessor enforces active secret scope."""
    if _gev_key_status() is None:
        raise HTTPException(400, "GEV server not running")
    try:
        from agent.secret_scope import get_secret
        found = {name: value for name in sorted(HERMES_BRIDGE) if (value := get_secret(name))}
    except Exception:
        raise HTTPException(503, "Profile-scoped Hermes secrets are unavailable. Use native GEV Provider Settings.") from None
    if not found:
        raise HTTPException(404, "No matching provider keys found in the active Hermes secret scope.")
    return _post_keys(found)


@router.post("/keys")
@_exclusive
def post_keys(payload: dict) -> dict:
    if _gev_key_status() is None:
        raise HTTPException(400, "GEV server not running")
    updates = {k: v.strip() for k, v in payload.items() if k in HERMES_BRIDGE and isinstance(v, str) and v.strip()}
    if not updates:
        raise HTTPException(400, "No known keys in payload")
    return _post_keys(updates)


def _post_keys(updates: dict[str, str]) -> dict:
    try:
        with httpx.Client(timeout=10, trust_env=False, follow_redirects=False) as client:
            r = client.post(_url() + "api/setup/keys", json=updates,
                            headers={"Origin": _url().rstrip("/"), "Content-Type": "application/json"})
            if r.status_code == 200:
                return {"ok": True, "applied": sorted(updates), "message": "GEV restart scheduled by its own server"}
            raise HTTPException(502, f"GEV refused the key update (HTTP {r.status_code}). Check the provider fields in native Provider Settings.")
    except httpx.HTTPError:
        raise HTTPException(502, "GEV unreachable during key update. No provider values were logged.") from None
