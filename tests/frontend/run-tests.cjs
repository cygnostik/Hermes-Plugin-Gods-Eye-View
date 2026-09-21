const { spawnSync } = require('node:child_process');
const path = require('node:path');

// No copied/transformed plugin: syntax-check and execute the public entrypoint.
const commands = [
  ['--check', path.resolve(__dirname, '../../desktop/plugin.js')],
  ['--experimental-vm-modules', '--test', path.join(__dirname, 'plugin.test.cjs')],
];
for (const args of commands) {
  const result = spawnSync(process.execPath, args, { stdio: 'inherit', timeout: 90000 });
  if (result.error) console.error(result.error.message);
  if (result.status !== 0) {
    process.exitCode = result.status || 1;
    break;
  }
}
