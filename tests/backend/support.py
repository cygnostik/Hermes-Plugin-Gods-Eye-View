"""Portable, offline boundaries. Every path is temporary; no real server access."""
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from contextvars import ContextVar
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

gev = load('gev_backend_fixture', ROOT / 'dashboard/plugin_api.py')

class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.temp = self.enterContext(tempfile.TemporaryDirectory())
        self.base = Path(self.temp)
        self.home = ContextVar('fixture_home', default=self.base / 'profile-a')
        self.root = self.base / 'checkout'; self.root.mkdir()
        (self.root / '.git').mkdir()
        (self.root / 'package.json').write_text(json.dumps({'name': 'gods-eye-view', 'version': 'fixture', 'engines': {'node': '>=24.14.0 <25 || >=26 <27'}}))
        self.node = self.base / 'runtime/node.exe'; self.node.parent.mkdir(); self.node.touch()
        self.npm = self.node.parent / 'node_modules/npm/bin/npm-cli.js'; self.npm.parent.mkdir(parents=True); self.npm.touch()
        vite = self.root / 'node_modules/vite/bin/vite.js'; vite.parent.mkdir(parents=True); vite.touch()
        constants = types.ModuleType('hermes_constants'); constants.get_hermes_home = self.home.get
        storage = types.ModuleType('plugins.plugin_storage')
        def data_dir(name):
            path = self.home.get() / 'plugin-data' / name; path.mkdir(parents=True, exist_ok=True); return path
        storage.plugin_data_dir = data_dir
        self.enterContext(patch.dict(sys.modules, {'hermes_constants': constants, 'plugins.plugin_storage': storage}))
        self.data = data_dir('gods-eye-view')
        self.config = {'root': str(self.root), 'node': str(self.node), 'npm_cli': str(self.npm), 'port': 4317, 'node_version': '24.14.0'}
        (self.data / 'config.json').write_text(json.dumps(self.config))
        self.enterContext(patch('subprocess.run', side_effect=AssertionError('unmocked subprocess')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('unmocked launch')))
        self.enterContext(patch.object(gev, '_port_open', side_effect=AssertionError('unmocked port probe')))
        self.enterContext(patch('psutil.process_iter', side_effect=AssertionError('unmocked process discovery')))
        self.enterContext(patch('httpx.Client', side_effect=AssertionError('unmocked HTTP')))
        if hasattr(gev, '_require_supported_platform'):
            self.enterContext(patch.object(gev, '_require_supported_platform'))
        if hasattr(gev, 'settings'):
            self.enterContext(patch.object(gev.settings, 'node_version', return_value='24.14.0'))
            self.enterContext(patch.object(gev.settings, 'validate_checkout'))
        if hasattr(gev, '_STATES'):
            gev._STATES.clear()
