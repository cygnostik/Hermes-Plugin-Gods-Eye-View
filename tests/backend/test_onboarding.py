"""Offline onboarding fixtures; never touch an installed plugin or live server."""
import argparse
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import types
import unittest
from contextvars import ContextVar
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

entry = load('gev_entry_fixture', ROOT / '__init__.py')

class OnboardingTests(unittest.TestCase):
    def test_register_is_read_only_and_exposes_argparse_configure(self):
        ctx = Mock()
        with patch('subprocess.run', side_effect=AssertionError('registration spawned')), patch.object(Path, 'mkdir', side_effect=AssertionError('registration wrote')):
            entry.register(ctx)
        ctx.register_cli_command.assert_called_once()
        call = ctx.register_cli_command.call_args.kwargs
        self.assertEqual(call['name'], 'gev')
        parser = argparse.ArgumentParser()
        call['setup_fn'](parser)
        args = parser.parse_args(['configure', '--root', 'fixture-root', '--node', 'fixture-node', '--port', '4317'])
        self.assertEqual(args.port, 4317)
        self.assertEqual(args.root, 'fixture-root')
        self.assertTrue(callable(call['handler_fn']))

    def test_configure_validates_existing_assets_and_writes_profile_storage(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / 'profile'
            root = Path(temp) / 'checkout'; root.mkdir()
            (root / '.git').mkdir()
            (root / 'package.json').write_text(json.dumps({'name': 'gods-eye-view', 'engines': {'node': '>=24.14.0 <25 || >=26 <27'}}))
            node = Path(temp) / 'node.exe'; node.touch()
            npm = Path(temp) / 'node_modules/npm/bin/npm-cli.js'; npm.parent.mkdir(parents=True); npm.touch()
            constants = types.ModuleType('hermes_constants'); constants.get_hermes_home = lambda: home
            storage = types.ModuleType('plugins.plugin_storage')
            def data_dir(name):
                path = home / 'plugin-data' / name; path.mkdir(parents=True, exist_ok=True); return path
            storage.plugin_data_dir = Mock(side_effect=data_dir)
            ctx = Mock(); entry.register(ctx)
            call = ctx.register_cli_command.call_args.kwargs
            parser = argparse.ArgumentParser(); call['setup_fn'](parser)
            args = parser.parse_args(['configure', '--root', str(root), '--node', str(node), '--port', '4317'])
            def run(argv, **kwargs):
                return types.SimpleNamespace(returncode=0, stdout='v24.14.0' if '--version' in argv else 'https://github.com/bilawalsidhu/gods-eye-view.git', stderr='')
            with patch.dict(sys.modules, {'hermes_constants': constants, 'plugins.plugin_storage': storage}), patch('subprocess.run', side_effect=run), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(call['handler_fn'](args), 0)
            config = json.loads((home / 'plugin-data/gods-eye-view/config.json').read_text())
            self.assertEqual(config['port'], 4317)
            self.assertEqual(config['root'], str(root.resolve()))
            self.assertEqual(config['npm_cli'], str(npm.resolve()))
            self.assertEqual(config['node_version'], '24.14.0')
            self.assertEqual(set(config), {'root', 'node', 'npm_cli', 'port', 'node_version'})
            storage.plugin_data_dir.assert_called_with('gods-eye-view')

if __name__ == '__main__':
    unittest.main(verbosity=2)
