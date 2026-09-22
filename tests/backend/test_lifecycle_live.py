"""Small native-OS smoke: real Node/HTTP/processes, no providers or downloads."""
import json
import shutil
import socket
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from support import gev


@unittest.skipUnless(sys.platform in ("win32", "darwin"), "Windows/macOS lifecycle")
class NativeLifecycleTests(unittest.TestCase):
    def test_start_adopt_stop_and_restart_exact_engine(self):
        node = shutil.which("node")
        assert node is not None, "Install a supported Node runtime before running tests"
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "engine"; root.mkdir()
            data = base / "profile"; data.mkdir()
            (root / "package.json").write_text(json.dumps({
                "name": "gods-eye-view", "version": "fixture",
                "engines": {"node": ">=24.14.0 <25 || >=26 <27"},
            }))
            script = root / "node_modules/vite/bin/vite.js"
            script.parent.mkdir(parents=True)
            script.write_text("""
const http = require('node:http');
const port = Number(process.argv[process.argv.indexOf('--port') + 1]);
http.createServer((req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.end(JSON.stringify({keys: [], setCount: 0, total: 0}));
}).listen(port, '127.0.0.1');
""")
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
            config = {"root": str(root), "node": str(Path(node).resolve()),
                      "npm_cli": None, "port": port, "node_version": "test"}
            storage = types.ModuleType("plugins.plugin_storage")
            setattr(storage, "plugin_data_dir", lambda name: data)
            with patch.object(gev.settings, "load", return_value=config), patch.object(gev.settings, "data_path", return_value=data), patch.dict(sys.modules, {"plugins.plugin_storage": storage}):
                gev._STATES.clear()
                processes = []
                try:
                    for _ in range(2):
                        result = gev.start_gev()
                        process = gev._state()["proc"]; processes.append(process)
                        self.assertTrue(result["ok"])
                        self.assertTrue(gev.status()["platform_supported"])
                        self.assertTrue(gev.status()["running"])
                        self.assertEqual(gev._server_pid(), process.pid)
                        # A fresh backend must safely adopt its exact existing engine.
                        gev._state()["proc"] = None
                        self.assertTrue(gev.stop_gev()["ok"])
                        self.assertFalse(gev._port_open(port))
                        process.wait(timeout=10)
                finally:
                    for process in processes:
                        if process.poll() is None:
                            process.kill(); process.wait(timeout=10)
                    gev._STATES.clear()


if __name__ == "__main__":
    unittest.main()
