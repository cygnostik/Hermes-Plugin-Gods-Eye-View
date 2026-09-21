"""Settings validations using temporary assets and mocked executable boundaries."""
import json
import types
from pathlib import Path
from unittest.mock import patch
import unittest
from support import FixtureCase, ROOT, load

settings = load('gev_settings_fixture', ROOT / 'settings.py')

class SettingsTests(FixtureCase):
    def command(self, argv, **kwargs):
        return types.SimpleNamespace(returncode=0, stdout='v24.14.0' if '--version' in argv else 'https://github.com/bilawalsidhu/gods-eye-view.git', stderr='')

    def test_configure_refuses_retargeting_an_active_port(self):
        with patch.object(settings.subprocess, 'run', side_effect=self.command), patch('socket.socket') as sock:
            sock.return_value.__enter__.return_value.connect_ex.return_value = 0
            with self.assertRaisesRegex(ValueError, 'Stop'):
                settings.configure(self.root, self.node, port=4519)
        self.assertEqual(json.loads((self.data / 'config.json').read_text())['port'], 4317)

    def test_declared_engine_range_is_checked_against_actual_node(self):
        (self.root / 'package.json').write_text(json.dumps({'name': 'gods-eye-view', 'engines': {'node': '>=26 <27'}}))
        with patch.object(settings.subprocess, 'run', side_effect=self.command):
            with self.assertRaisesRegex(ValueError, 'engine'):
                settings.node_version(self.node, self.root)

    def test_configuration_does_not_accept_wrong_package_or_plugin_directory(self):
        (self.root / 'package.json').write_text(json.dumps({'name': 'unrelated-app'}))
        with patch.object(settings.subprocess, 'run', side_effect=self.command):
            with self.assertRaises(ValueError):
                settings.configure(self.root, self.node)
        with self.assertRaises(ValueError):
            settings.validate_checkout(ROOT, self.node)

    def test_mutation_lock_rejects_an_independent_handle(self):
        self.assertTrue(callable(getattr(settings, 'mutation_lock', None)))
        other = load('gev_other_settings_fixture', ROOT / 'settings.py')
        with settings.mutation_lock():
            with settings.mutation_lock():  # same request may nest update -> stop/start
                with self.assertRaisesRegex(ValueError, 'in progress'):
                    with other.mutation_lock():
                        self.fail('second lock acquired')
        with other.mutation_lock():
            pass  # release really happened

if __name__ == '__main__': unittest.main(verbosity=2)
