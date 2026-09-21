"""Public-release safety and portability regressions (offline fixtures only)."""
from pathlib import Path
from unittest.mock import patch
from support import FixtureCase, gev
import unittest

class PublicBackendTests(FixtureCase):
    def test_unconfigured_status_is_actionable_read_only_and_does_not_probe_default_port(self):
        (self.data / 'config.json').unlink()
        with patch.object(Path, 'mkdir', side_effect=AssertionError('status wrote')), patch.object(gev, '_gev_key_status', side_effect=AssertionError('unconfigured probe')):
            value = gev.status()
        self.assertFalse(value['installed'])
        self.assertFalse(value['running'])
        self.assertFalse(value['node24_ok'])
        self.assertIsNone(value['keys'])
        self.assertIn('hermes gev configure', value['configuration_error'])
        with self.assertRaises(gev.HTTPException) as error:
            gev.start_gev()
        self.assertEqual(error.exception.status_code, 400)
        self.assertIn('hermes gev configure', error.exception.detail)

    def test_public_routes_have_no_dropfile_reader(self):
        self.assertFalse(hasattr(gev, '_read_drop_file'))
        self.assertNotIn('/keys/dropfile', {route.path for route in gev.router.routes})
        with patch.object(gev, '_gev_key_status', return_value=None):
            self.assertEqual(gev.get_keys(), {'gev_live_status': None})

    def test_profile_switch_never_reuses_settings_or_process_state(self):
        import json
        with patch.object(gev, '_gev_key_status', return_value=None):
            self.assertEqual(gev.status()['port'], 4317)
            token = self.home.set(self.base / 'profile-b')
            try:
                self.assertFalse(gev.status()['configured'])
                directory = self.home.get() / 'plugin-data/gods-eye-view'; directory.mkdir(parents=True)
                (directory / 'config.json').write_text(json.dumps({**self.config, 'port': 4418}))
                self.assertEqual(gev.status()['port'], 4418)
                self.assertIsNone(gev.status()['pid'])
            finally:
                self.home.reset(token)
            self.assertEqual(gev.status()['port'], 4317)

    def test_arbitrary_port_is_used_in_conflict_error(self):
        with patch.object(gev, '_gev_key_status', return_value=None), patch.object(gev, '_port_open', return_value=True):
            with self.assertRaises(gev.HTTPException) as error:
                gev.start_gev()
        self.assertIn('4317', error.exception.detail)
        self.assertNotIn('4173', error.exception.detail)

    def test_bridge_uses_scoped_accessor_and_not_ambient_environment(self):
        import os, sys, types
        from unittest.mock import Mock
        secret = types.ModuleType('agent.secret_scope')
        secret.get_secret = Mock(side_effect=lambda name: 'fixture-scoped' if name == 'OPENAI_API_KEY' else None)
        with patch.dict(sys.modules, {'agent.secret_scope': secret}), patch.dict(os.environ, {'OPENAI_API_KEY': 'fixture-other-profile'}), patch.object(gev, '_gev_key_status', return_value={'keys': []}), patch.object(gev, '_post_keys', return_value={'ok': True}) as post:
            gev.bridge_hermes_keys()
        self.assertEqual(post.call_args.args[0], {'OPENAI_API_KEY': 'fixture-scoped'})
        secret.get_secret.assert_any_call('OPENAI_API_KEY')

    def test_child_environment_does_not_inherit_provider_credentials(self):
        import os
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'fixture-other-profile', 'UNRELATED_SECRET': 'fixture-hidden'}, clear=True):
            env = gev._node_env()
        self.assertNotIn('OPENAI_API_KEY', env)
        self.assertNotIn('UNRELATED_SECRET', env)

if __name__ == '__main__': unittest.main(verbosity=2)
