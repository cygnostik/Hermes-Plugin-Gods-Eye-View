"""Behavioral regressions. HTTP/process boundaries use labelled fixtures; no live writes."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Import before FixtureCase.setUp patches httpx.Client, TestClient's base class.
from fastapi.testclient import TestClient

from support import FixtureCase, gev

class BackendTests(FixtureCase):
    def test_health_poll_is_read_only_and_does_not_spawn_processes(self):
        fixture = {'keys': [], 'setCount': 0, 'total': 0, 'store': 'fixture'}
        with patch.object(gev, '_gev_key_status', return_value=fixture), patch.object(gev, '_run', side_effect=AssertionError('health spawned a subprocess')):
            result = gev.status()
        self.assertTrue(result['running'])
        self.assertIsNone(result['commits_behind'])

    def test_failed_dependency_install_never_reports_update_success(self):
        def command(argv, **kwargs):
            if 'ci' in argv:
                return 1, 'fixture install failed'
            if 'rev-parse' in argv:
                return 0, 'fixture-revision'
            if 'status' in argv:
                return 0, ''
            return 0, 'Already up to date.'
        with patch.object(gev, '_run', side_effect=command), patch.object(gev, '_port_open', return_value=False), patch.object(gev, '_gev_key_status', return_value=None):
            with self.assertRaises(gev.HTTPException) as raised:
                gev.update_gev()
        self.assertIn('npm', str(raised.exception.detail).lower())

    def test_every_update_stage_aborts_on_failure(self):
        for failure in ['fetch', 'pull', 'esbuild', 'rev-parse']:
            with self.subTest(failure=failure):
                def command(argv, **kwargs):
                    stage = 'esbuild' if any('esbuild/install.js' in a for a in argv) else next((a for a in ['fetch','pull','rev-parse','ci','status'] if a in argv), '')
                    if stage == failure:
                        return 1, 'fixture failure'
                    return 0, '' if stage == 'status' else 'fixture success'
                with patch.object(gev, '_run', side_effect=command), patch.object(gev, '_port_open', return_value=False), patch.object(gev, '_gev_key_status', return_value=None):
                    with self.assertRaises(gev.HTTPException):
                        gev.update_gev()

    def test_dirty_checkout_is_refused_before_stopping_server(self):
        with patch.object(gev, '_run', return_value=(0, ' M package.json')), patch.object(gev, '_port_open', return_value=True), patch.object(gev, 'stop_gev') as stop:
            with self.assertRaises(gev.HTTPException) as raised:
                gev.update_gev()
        self.assertEqual(raised.exception.status_code, 409)
        stop.assert_not_called()

    def test_start_does_not_leave_an_undrained_pipe_and_uses_portable_node(self):
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as temp, patch.object(gev, '_port_open', side_effect=[False, True]), patch.object(gev, '_gev_key_status', side_effect=[None, {'keys': [], 'total': 0, 'setCount': 0}]), patch.object(gev.subprocess, 'Popen') as launch:
            launch.return_value.poll.return_value = None
            try:
                gev.start_gev()
                kwargs = launch.call_args.kwargs
                self.assertNotEqual(kwargs['stdout'], gev.subprocess.PIPE)
                self.assertEqual(kwargs['env']['PATH'].split(os.pathsep)[0], str(self.node.parent))
            finally:
                gev._state()["proc"] = None

    def test_stop_refuses_an_unowned_listener(self):
        with patch.object(gev, '_server_pid', return_value=None), patch.object(gev, '_port_open', return_value=True), patch.object(gev, '_run') as command:
            with self.assertRaises(gev.HTTPException) as raised:
                gev.stop_gev()
        self.assertEqual(raised.exception.status_code, 409)
        command.assert_not_called()

    def test_mac_stop_continues_when_a_verified_process_exits_first(self):
        import psutil
        from types import SimpleNamespace
        from unittest.mock import Mock
        for stage in ('lookup', 'terminate', 'kill'):
            with self.subTest(stage=stage):
                parent, child = Mock(), Mock()
                parent.children.return_value = [child]
                if stage != 'lookup':
                    getattr(child, stage).side_effect = psutil.NoSuchProcess(998)
                waits = [([], [child, parent]), ([child, parent], [])] if stage == 'kill' else [([child, parent], []), ([], [])]
                with patch.object(gev, 'sys', SimpleNamespace(platform='darwin')), patch.object(gev, '_server_pid', return_value=999), patch.object(gev, '_port_open', side_effect=[True, False]), patch.object(psutil, 'Process', return_value=parent, side_effect=psutil.NoSuchProcess(999) if stage == 'lookup' else None), patch.object(psutil, 'wait_procs', side_effect=waits), patch.object(gev.time, 'sleep'):
                    self.assertTrue(gev.stop_gev()['ok'])
                if stage != 'lookup':
                    parent.terminate.assert_called_once()
                if stage == 'kill':
                    parent.kill.assert_called_once()

    def test_process_discovery_requires_the_actual_listening_socket(self):
        import psutil
        from unittest.mock import Mock
        candidate = Mock()
        candidate.exe.return_value = str(self.node)
        candidate.cwd.return_value = str(self.root)
        candidate.cmdline.return_value = [str(self.node), str(self.root / 'node_modules/vite/bin/vite.js')]
        candidate.net_connections.return_value = []
        with patch.object(psutil, 'process_iter', return_value=[candidate]):
            self.assertIsNone(gev._server_pid())
        candidate.net_connections.assert_called_once_with(kind='tcp')

    def test_explicit_update_check_does_not_stop_or_install(self):
        from fastapi import FastAPI
        app = FastAPI(); app.include_router(gev.router)
        seen = []
        def command(argv, **kwargs):
            seen.append(argv)
            if 'rev-list' in argv: return 0, '2'
            if 'status' in argv: return 0, ' M package.json'
            return 0, 'fixture'
        with patch.object(gev, '_run', side_effect=command), patch.object(gev, 'stop_gev') as stop:
            response = TestClient(app).post('/updates/check')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['commits_behind'], 2)
        self.assertTrue(response.json()['dirty'])
        self.assertFalse(any('ci' in cmd for cmd in seen))
        stop.assert_not_called()
        gev._state()['updates'] = {'commits_behind': None, 'checked_at': None}

    def test_successful_update_restores_running_state(self):
        def command(argv, **kwargs):
            return (0, '') if 'status' in argv else (0, 'fixture-success')
        with patch.object(gev, '_run', side_effect=command), patch.object(gev, '_port_open', return_value=True), patch.object(gev, 'stop_gev') as stop, patch.object(gev, 'start_gev', return_value={'ok': True}) as start:
            result = gev.update_gev()
        stop.assert_called_once()
        start.assert_called_once()
        self.assertTrue(result['restarted'])

    def test_command_runner_pins_portable_node_for_child_scripts(self):
        import os
        with patch.object(gev.subprocess, 'run') as run:
            run.return_value.returncode = 0; run.return_value.stdout = ''; run.return_value.stderr = ''
            gev._run(['fixture'], cwd=self.root)
        self.assertEqual(run.call_args.kwargs.get('env', {}).get('PATH', '').split(os.pathsep)[0], str(self.node.parent))

    def test_stop_failure_does_not_report_success(self):
        import psutil
        with patch.object(gev, '_server_pid', return_value=999), patch.object(gev, '_port_open', return_value=True), patch.object(gev, '_run', return_value=(1, 'fixture failure')), patch.object(psutil, 'Process', side_effect=psutil.AccessDenied(999)), patch.object(gev.time, 'sleep'):
            with self.assertRaises(gev.HTTPException):
                gev.stop_gev()

    def test_concurrent_lifecycle_action_returns_busy(self):
        import threading
        lock = threading.RLock(); acquired = threading.Event(); release = threading.Event()
        def holder():
            with lock:
                acquired.set(); release.wait(5)
        thread = threading.Thread(target=holder); thread.start(); self.assertTrue(acquired.wait(2))
        try:
            with patch.object(gev, '_MUTATION_LOCK', lock, create=True), patch.object(gev, '_gev_key_status', return_value={'keys': []}):
                with self.assertRaises(gev.HTTPException) as raised:
                    gev.start_gev()
            self.assertEqual(raised.exception.status_code, 409)
        finally:
            release.set(); thread.join(2)

    def test_health_rejects_non_gev_json(self):
        with patch.object(gev.httpx, 'Client') as client:
            response = client.return_value.__enter__.return_value.get.return_value
            response.status_code = 200; response.json.return_value = {'ok': True}
            self.assertIsNone(gev._gev_key_status())

    def test_runtime_log_does_not_dirty_upstream_checkout(self):
        self.assertFalse((self.data / "gev-runtime.log").resolve().is_relative_to(self.root.resolve()))

    def test_key_write_requires_gev_identity_not_just_open_port(self):
        with patch.object(gev, '_port_open', return_value=True), patch.object(gev, '_gev_key_status', return_value=None), patch.object(gev, '_post_keys') as post:
            with self.assertRaises(gev.HTTPException):
                gev.post_keys({'OPENAI_API_KEY': 'fixture-only-not-a-real-key'})
        post.assert_not_called()

    def test_provider_error_does_not_echo_response_body(self):
        with patch.object(gev.httpx, 'Client') as client:
            response = client.return_value.__enter__.return_value.post.return_value
            response.status_code = 400; response.text = 'fixture-sensitive-value'
            with self.assertRaises(gev.HTTPException) as raised:
                gev._post_keys({'OPENAI_API_KEY': 'fixture-sensitive-value'})
        self.assertNotIn('fixture-sensitive-value', str(raised.exception.detail))

    def test_key_success_uses_message_not_error_detail_field(self):
        with patch.object(gev.httpx, 'Client') as client:
            client.return_value.__enter__.return_value.post.return_value.status_code = 200
            result = gev._post_keys({'OPENAI_API_KEY': 'fixture-not-real'})
        self.assertTrue(result['ok'])
        self.assertNotIn('detail', result)

if __name__ == '__main__':
    unittest.main(verbosity=2)
