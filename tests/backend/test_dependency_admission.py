"""Package declarations must coexist with Hermes' platform-specific psutil pins.

Android is not a supported GEV Desktop target. Its Hermes-only psutil source
must not be constrained by this Desktop integration during a universal lock.
These are dependency-marker data tests, not emulated operating-system tests.
"""
from pathlib import Path
import unittest

from packaging.requirements import Requirement
from packaging.markers import default_environment
import yaml

ROOT = Path(__file__).resolve().parents[2]


class DependencyAdmissionTests(unittest.TestCase):
    def test_android_core_pin_is_not_constrained_by_desktop_plugin(self):
        manifest = yaml.safe_load((ROOT / 'plugin.yaml').read_text(encoding='utf-8'))
        env = {**default_environment(), 'sys_platform': 'android',
               'python_version': '3.14', 'python_full_version': '3.14.0'}
        active = [Requirement(spec) for spec in manifest['python_dependencies']
                  if Requirement(spec).name == 'psutil'
                  and (Requirement(spec).marker is None or Requirement(spec).marker.evaluate(env))]
        self.assertEqual(active, [], 'Android is deferred; do not constrain Hermes Android psutil')

    def test_supported_desktop_platforms_keep_bounded_compatible_psutil(self):
        manifest = yaml.safe_load((ROOT / 'plugin.yaml').read_text(encoding='utf-8'))
        for platform in ('win32', 'darwin'):
            with self.subTest(platform=platform):
                env = {**default_environment(), 'sys_platform': platform,
                       'python_version': '3.14', 'python_full_version': '3.14.0'}
                active = [Requirement(spec) for spec in manifest['python_dependencies']
                          if Requirement(spec).name == 'psutil'
                          and (Requirement(spec).marker is None or Requirement(spec).marker.evaluate(env))]
                self.assertTrue(active)
                self.assertTrue(all('7.2.2' in req.specifier for req in active))
                self.assertTrue(all('8.0.0' not in req.specifier for req in active))


if __name__ == '__main__':
    unittest.main()
