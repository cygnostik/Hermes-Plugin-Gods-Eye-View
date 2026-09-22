"""Non-secret, profile-scoped settings. Reads never create directories."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import socket
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

_LOCKED = ContextVar("gev_settings_lock", default=None)


@contextmanager
def mutation_lock():
    """Cross-process, profile-local lock; kernel releases it even after a crash."""
    directory = data_path()
    if _LOCKED.get() == directory:
        yield
        return
    from plugins.plugin_storage import plugin_data_dir
    directory = plugin_data_dir(PLUGIN_NAME)
    with (directory / "action.lock").open("a+b") as stream:
        if stream.seek(0, 2) == 0:
            stream.write(b"0"); stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise ValueError("Another GEV action is in progress. Wait for it to finish.") from None
        token = _LOCKED.set(directory)
        try:
            yield
        finally:
            _LOCKED.reset(token)
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

PLUGIN_NAME = "gods-eye-view"
SETUP_HINT = 'Run hermes gev configure --root "<official GEV checkout>" --node "<node executable>" [--npm-cli "<npm-cli.js>"] [--port 4173].'


def data_path() -> Path:
    # plugin_data_dir creates directories, so use its documented path for READS.
    from hermes_constants import get_hermes_home
    return get_hermes_home() / "plugin-data" / PLUGIN_NAME


def child_env(node: Path) -> dict[str, str]:
    # Do not inherit another profile's credentials into Node, npm or Git.
    names = ("PATH", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "TMPDIR", "HOME", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "SYSTEMDRIVE", "LANG", "LC_ALL")
    env = {name: os.environ[name] for name in names if name in os.environ}
    env["PATH"] = str(node.parent) + os.pathsep + env.get("PATH", "")
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _command(argv, cwd, node):
    try:
        result = subprocess.run(argv, cwd=str(cwd), env=child_env(node), capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=15,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError("Could not run Git or the selected Node runtime; check the paths and Git installation.") from None
    if result.returncode:
        raise ValueError("Git or Node validation failed. Use an existing official checkout and working Node executable.")
    return result.stdout.strip()


def node_version(node: Path, root: Path) -> str:
    value = _command([str(node), "--version"], root, node)
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError("Node returned an invalid version.")
    version = tuple(map(int, match.groups()))
    if not ((24, 14, 0) <= version < (25, 0, 0) or (26, 0, 0) <= version < (27, 0, 0)):
        raise ValueError("GEV requires Node >=24.14.0 <25 or >=26 <27.")
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    engine = package.get("engines", {}).get("node", "")
    # Upstream uses bounded comparator ranges. Reject unfamiliar syntax clearly.
    def allows(clause):
        parts = clause.split()
        if not parts:
            return False
        for part in parts:
            bound = re.fullmatch(r"(>=|<=|>|<|=)?(\d+)(?:\.(\d+))?(?:\.(\d+))?", part)
            if not bound:
                return False
            op = bound[1] or "="
            target = tuple(int(n or 0) for n in bound.groups()[1:])
            if not {">=": version >= target, "<=": version <= target,
                    ">": version > target, "<": version < target, "=": version == target}[op]:
                return False
        return True
    if not isinstance(engine, str) or not any(allows(c) for c in engine.split("||")):
        raise ValueError("Selected Node does not satisfy the checkout's supported engine range.")
    return ".".join(match.groups())


def validate_checkout(root: Path, node: Path) -> None:
    if not root.is_dir() or not (root / ".git").exists() or not (root / "package.json").is_file():
        raise ValueError("--root must be an existing official GEV Git checkout containing package.json.")
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    if package.get("name") != "gods-eye-view" or root.resolve() == Path(__file__).resolve().parent:
        raise ValueError("Select the official GEV application checkout, not this plugin or another package.")
    remote = _command(["git", "remote", "get-url", "origin"], root, node)
    if remote not in {"https://github.com/bilawalsidhu/gods-eye-view", "https://github.com/bilawalsidhu/gods-eye-view.git", "git@github.com:bilawalsidhu/gods-eye-view.git", "ssh://git@github.com/bilawalsidhu/gods-eye-view.git"}:
        raise ValueError("The checkout origin must be the official bilawalsidhu/gods-eye-view repository.")


def configure(root, node, npm_cli=None, port=4173) -> dict:
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError("--port must be an integer from 1024 to 65535.")
    root = Path(root).expanduser().resolve()
    node = Path(node).expanduser().resolve()
    if not node.is_file():
        raise ValueError("--node must point to an existing Node executable.")
    validate_checkout(root, node)
    version = node_version(node, root)
    candidates = [node.parent / "node_modules/npm/bin/npm-cli.js",
                  node.parent.parent / "lib/node_modules/npm/bin/npm-cli.js",
                  (node.parent / "npm").resolve()]
    npm = Path(npm_cli).expanduser().resolve() if npm_cli else next(
        (path for path in candidates if path.is_file() and path.name == "npm-cli.js"), candidates[0])
    if npm_cli and not npm.is_file():
        raise ValueError("--npm-cli must point to an existing npm-cli.js.")
    value = {"root": str(root), "node": str(node), "npm_cli": str(npm) if npm.is_file() else None,
             "port": port, "node_version": version}
    with mutation_lock():
        previous = data_path() / "config.json"
        if previous.exists():
            old = json.loads(previous.read_text(encoding="utf-8"))
            if any(old.get(k) != value[k] for k in ("root", "node", "port")):
                for family, address in ((socket.AF_INET, ("127.0.0.1", old["port"])),
                                        (socket.AF_INET6, ("::1", old["port"]))):
                    try:
                        with socket.socket(family, socket.SOCK_STREAM) as sock:
                            sock.settimeout(0.5)
                            if sock.connect_ex(address) == 0:
                                raise ValueError("Stop the existing GEV engine before changing its configuration.")
                    except OSError:
                        continue
        from plugins.plugin_storage import plugin_data_dir
        directory = plugin_data_dir(PLUGIN_NAME)
        fd, temporary = tempfile.mkstemp(prefix="config-", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(value, stream, indent=2)
                stream.write("\n")
            os.replace(temporary, directory / "config.json")
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return {"ok": True, "configuration": value, "config_file": str(directory / "config.json"),
            "message": "Configured existing assets; no dependencies installed and no server started."}


def load() -> dict:
    path = data_path() / "config.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError("GEV is not configured. " + SETUP_HINT) from None
    except (OSError, ValueError):
        raise ValueError("GEV configuration cannot be read. " + SETUP_HINT) from None
    if not isinstance(value, dict) or set(value) != {"root", "node", "npm_cli", "port", "node_version"}:
        raise ValueError("Invalid GEV configuration. " + SETUP_HINT)
    if any(not isinstance(value[key], str) or not Path(value[key]).is_absolute() for key in ("root", "node")) or type(value["port"]) is not int or not 1024 <= value["port"] <= 65535:
        raise ValueError("Invalid GEV paths or port. " + SETUP_HINT)
    if value["npm_cli"] is not None and (not isinstance(value["npm_cli"], str) or not Path(value["npm_cli"]).is_absolute()):
        raise ValueError("Invalid npm-cli path. " + SETUP_HINT)
    return value
