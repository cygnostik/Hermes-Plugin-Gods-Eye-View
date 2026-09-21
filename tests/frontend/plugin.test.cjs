// Run from the repository root: npm ci && npm test
// Executes desktop/plugin.js directly; only the Hermes host boundary is stubbed.
const { test, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const pluginPath = path.resolve(__dirname, '../../desktop/plugin.js');
const React = require('react');
const { JSDOM } = require('jsdom');
const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://localhost/' });
Object.assign(globalThis, { window: dom.window, document: dom.window.document, HTMLElement: dom.window.HTMLElement, IS_REACT_ACT_ENVIRONMENT: true });
const { createRoot } = require('react-dom/client');
const query = require('@tanstack/react-query');
const jsxRuntime = require('react/jsx-runtime');
const cleanups = [];
afterEach(async () => { for (const fn of cleanups.splice(0)) await fn(); });
function atom(value) { const listeners = new Set(); return { get: () => value, subscribe: fn => { listeners.add(fn); return () => listeners.delete(fn); }, set: next => { value = next; listeners.forEach(fn => fn()); } }; }
async function boot(initial = { running: true, installed: true, url: 'http://localhost:4173', version: 'test' }) {
  const filename = pluginPath;
  assert.ok(fs.existsSync(filename), 'public desktop/plugin.js must exist');
  const profile = atom('default'), connectionId = atom('local');
  const calls = [], notices = [], external = [], registrations = [];
  let status = initial, failure = null, reply = { ok: true }, externalResult = true;
  const ctx = { registerMany: entries => registrations.push(...entries), onDispose: () => {}, os: { openExternal: async url => { external.push(url); return externalResult; } }, rest: async (route, options) => { calls.push([route, options]); if (route === '/status') { if (failure) throw failure; return status; } return typeof reply === 'function' ? reply(route) : reply; } };
  const sdk = { ...query, host: { state: { profile, connectionId }, navigate: () => {}, notify: n => notices.push(n) }, useValue: a => React.useSyncExternalStore(a.subscribe, a.get, a.get), ROUTES_AREA: 'routes', SIDEBAR_NAV_AREA: 'sidebar', PALETTE_AREA: 'palette', STATUSBAR_AREAS: { right: 'status.right' } };
  const context = vm.createContext({ console, URL, setTimeout, clearTimeout, window: dom.window, document: dom.window.document });
  const module = new vm.SourceTextModule(fs.readFileSync(filename, 'utf8'), { context, identifier: filename });
  await module.link(specifier => { const exports = { '@hermes/plugin-sdk': sdk, react: React, 'react/jsx-runtime': jsxRuntime }[specifier]; assert.ok(exports, 'unsupported import: ' + specifier); return new vm.SyntheticModule(Object.keys(exports), function () { for (const [key, value] of Object.entries(exports)) this.setExport(key, value); }, { context }); });
  await module.evaluate(); module.namespace.default.register(ctx);
  const client = new query.QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  const container = document.createElement('div'); document.body.append(container);
  const root = createRoot(container);
  const page = registrations.find(r => r.area === 'routes'); assert.ok(page, 'registers workspace route');
  await React.act(async () => { root.render(React.createElement(query.QueryClientProvider, { client }, page.render())); await new Promise(r => setTimeout(r, 10)); });
  const settle = () => React.act(async () => { await new Promise(r => setTimeout(r, 10)); });
  await settle();
  cleanups.push(async () => { await React.act(async () => root.unmount()); client.clear(); container.remove(); });
  const button = label => Array.from(container.querySelectorAll('button')).find(el => el.textContent.trim() === label || el.getAttribute('aria-label') === label);
  return { container, calls, notices, external, registrations, client, profile, connectionId, button, settle, namespace: module.namespace,
    click: async label => { const el = button(label); assert.ok(el, 'button exists: ' + label); assert.equal(el.disabled, false, label + ' enabled'); await React.act(async () => el.click()); await settle(); },
    status: async next => { status = next; failure = null; await React.act(async () => { await client.invalidateQueries(); }); await settle(); },
    failStatus: async () => { failure = new Error('connection lost'); await React.act(async () => { await client.invalidateQueries(); }); await settle(); },
    reply: next => { reply = next; }, externalResult: value => { externalResult = value; },
    event: async (node, type, properties = {}) => { await React.act(async () => node.dispatchEvent(Object.assign(new dom.window.Event(type), properties))); await settle(); }
  };
}
test('native workspace keeps a single flexible guest and scopes lightweight health to profile and connection', async () => {
  const ui = await boot();
  const guest = ui.container.querySelector('webview');
  assert.ok(guest); assert.equal(guest.getAttribute('partition'), 'persist:hermes-preview');
  assert.equal(guest.style.display, 'flex'); assert.equal(ui.container.querySelector('iframe'), null);
  assert.match(ui.container.textContent, /Engine running/);
  assert.equal(ui.container.querySelector('header').style.height, '40px');
  assert.equal(ui.container.querySelector('[role="dialog"]'), null);
  const cached = ui.client.getQueryCache().getAll()[0];
  assert.deepEqual(Array.from(cached.queryKey), ['gods-eye-view', 'status', 'default', 'local']);
  assert.ok(cached.options.refetchInterval >= 15000 && cached.options.refetchInterval <= 30000);
  await ui.status({ running: true, installed: true, url: 'http://localhost:4173', version: 'next' });
  assert.equal(ui.container.querySelector('webview'), guest, 'health polling must not remount the guest');
});
test('unconfigured installs explain setup without offering a broken start', async () => {
  const ui = await boot({ running: false, installed: false, node24_ok: false });
  assert.match(ui.container.textContent, /Setup required/);
  assert.match(ui.container.textContent, /README/);
  assert.match(ui.container.textContent, /hermes gev configure --root <existing GEV checkout> --node <node executable>/);
  assert.equal(ui.container.querySelector('webview'), null);
  assert.equal(ui.button('Start engine').disabled, true);
  await ui.click('Control room');
  for (const button of ui.container.querySelectorAll('button')) {
    if (['Start engine', 'Check updates', 'Update engine'].includes(button.textContent.trim())) assert.equal(button.disabled, true);
  }
  assert.equal(ui.calls.some(([route]) => route === '/start'), false);
  await ui.status({ running: false, installed: true, node24_ok: false });
  assert.match(ui.container.textContent, /hermes gev configure/);
  assert.equal(ui.button('Start engine').disabled, true, 'missing runtime still requires setup');
  await ui.status({ running: false, installed: true, node24_ok: true });
  assert.equal(ui.button('Start engine').disabled, false, 'configured offline engine can start');
});

test('failed engine launch retains the backend reason and explains configuration recovery', async () => {
  const ui = await boot({ running: false, installed: true, node24_ok: true });
  ui.reply({ ok: false, detail: 'GEV dependencies are missing.' });
  await ui.click('Start engine');
  const alert = ui.container.querySelector('[role="alert"]');
  assert.ok(alert);
  assert.match(alert.textContent, /GEV dependencies are missing/);
  assert.match(alert.textContent, /README/);
  assert.match(alert.textContent, /hermes gev configure/);
  assert.equal(ui.calls.filter(([route]) => route === '/start').length, 1);
  assert.equal(ui.container.querySelector('webview'), null);
});

test('invalid backend JSON is a connection error, never an offline engine', async () => {
  const ui = await boot({ error: 'Headless backend (hermes serve): web UI disabled' });
  assert.match(ui.container.textContent, /Plugin backend not loaded/);
  assert.match(ui.container.textContent, /Reconnect Desktop after installing backend/);
  assert.match(ui.container.querySelector('[role="alert"]').textContent, /README/);
  assert.match(ui.container.querySelector('[role="alert"]').textContent, /hermes gev configure/);
  assert.doesNotMatch(ui.container.textContent, /Engine offline/);
  assert.equal(ui.container.querySelector('webview'), null);
});
test('guest readiness, render failure and transient status errors preserve the existing guest', async () => {
  const ui = await boot(); const guest = ui.container.querySelector('webview');
  assert.match(ui.container.textContent, /Loading globe/);
  await ui.event(guest, 'dom-ready'); assert.match(ui.container.textContent, /Globe ready/);
  await ui.failStatus();
  assert.match(ui.container.textContent, /Connection interrupted/);
  assert.equal(ui.container.querySelector('webview'), guest);
  await ui.event(guest, 'render-process-gone', { reason: 'crashed' });
  assert.match(ui.container.textContent, /Globe renderer stopped/);
  let reloads = 0; guest.reload = () => reloads++;
  await ui.click('Reload globe'); assert.equal(reloads, 1);
  await ui.status({ running: true, installed: true, url: 'http://localhost:4173' });
  assert.equal(ui.container.querySelector('webview'), guest);
});
test('profile changes discard the previous guest rather than leak a working scene across accounts', async () => {
  const ui = await boot(); const guest = ui.container.querySelector('webview');
  await React.act(async () => ui.profile.set('different')); await ui.settle();
  assert.notEqual(ui.container.querySelector('webview'), guest);
  assert.ok(ui.client.getQueryCache().getAll().some(q => q.queryKey[2] === 'different'));
});
test('Control room gates updates behind confirmation and reports failed actions without false success', async () => {
  const ui = await boot();
  await ui.click('Control room'); assert.ok(ui.container.querySelector('[role="dialog"]'));
  assert.match(ui.container.querySelector('[role="dialog"]').textContent, /upstream GEV app, not this Hermes plugin/);
  assert.doesNotMatch(ui.container.textContent, /drop file/i);
  await ui.click('Check updates'); assert.ok(ui.calls.some(([p,o]) => p === '/updates/check' && o.method === 'POST'));
  await ui.click('Update engine'); assert.equal(ui.calls.filter(([p]) => p === '/update').length, 0);
  ui.reply({ ok: false, detail: 'Dirty checkout: preserve local changes' });
  await ui.click('Confirm update');
  assert.match(ui.container.textContent, /Dirty checkout: preserve local changes/);
  assert.equal(ui.calls.filter(([p]) => p === '/update').length, 1);
  ui.reply({ error: 'Headless backend: web UI disabled' });
  await ui.click('Stop engine'); assert.match(ui.container.textContent, /Headless backend/);
  assert.equal(ui.calls.filter(([p]) => p === '/keys/hermes').length, 0);
  await ui.click('Close Control room');
  const guest = ui.container.querySelector('webview');
  await ui.click('Focus'); assert.equal(ui.container.querySelector('header'), null);
  await ui.click('Show flight deck'); assert.ok(ui.container.querySelector('header'));
  assert.equal(ui.container.querySelector('webview'), guest);
});
test('guest external handoff validates exact preload channel and web schemes and disposes on unmount', async () => {
  const ui = await boot(); const guest = ui.container.querySelector('webview');
  await ui.event(guest, 'ipc-message', { channel: 'other', args: ['https://example.com/'] });
  await ui.event(guest, 'ipc-message', { channel: 'preview-open-external', args: ['file:///C:/secret'] });
  assert.equal(ui.external.length, 0);
  ui.externalResult(false);
  await ui.event(guest, 'ipc-message', { channel: 'preview-open-external', args: ['https://example.com/'] });
  assert.deepEqual(ui.external, ['https://example.com/']);
  assert.match(ui.container.textContent, /Could not open the browser/);
  await ui.status({ running: false, installed: true });
  await ui.event(guest, 'ipc-message', { channel: 'preview-open-external', args: ['https://example.org/'] });
  assert.equal(ui.external.length, 1);
});
test('Provider Settings uses the grounded native affordance and degrades honestly when unsupported', async () => {
  const ui = await boot(); const guest = ui.container.querySelector('webview');
  await ui.event(guest, 'dom-ready'); await ui.click('Control room');
  await ui.click('Provider Settings'); assert.match(ui.container.textContent, /Open Provider Settings inside the globe/);
  let clicked = 0;
  guest.getURL = () => 'http://localhost:4173/';
  const panel = { hidden: true };
  guest.executeJavaScript = async code => vm.runInNewContext(code, { document: { querySelector: selector => selector === '#key-setup-chip' ? { click: () => { clicked++; panel.hidden = false; } } : selector === '#key-setup[data-initialized="true"]' ? panel : null } });
  await ui.click('Provider Settings'); assert.equal(clicked, 1);
  assert.equal(ui.container.querySelector('[role="dialog"]'), null);
});
test('action detail errors are never promoted to success and drawer re-entry requires fresh update confirmation', async () => {
  const ui = await boot(); await ui.click('Control room');
  ui.reply({ ok: true, detail: 'Backend rejected this request' });
  await ui.click('Check updates');
  assert.ok(ui.container.querySelector('[role="alert"]'), 'detail response must render an error alert');
  assert.match(ui.container.querySelector('[role="alert"]').textContent, /Backend rejected/);
  await ui.click('Update engine');
  await ui.click('Control room'); await ui.click('Control room');
  assert.equal(Boolean(ui.button('Confirm update')), false, 'closing the drawer clears update confirmation');
});
test('rejects incomplete status and non-web guest URLs', async () => {
  const ui = await boot({ running: false });
  assert.match(ui.container.textContent, /Plugin backend not loaded/);
  await ui.status({ running: true, installed: true, url: 'javascript:alert(1)' });
  assert.equal(ui.container.querySelector('webview'), null);
  assert.match(ui.container.textContent, /invalid globe URL/);
});

test('registers a truthful glanceable engine status contribution', async () => {
  const ui = await boot();
  const chip = ui.registrations.find(r => r.area === 'status.right');
  assert.ok(chip, 'the original status chip remains available');
  const container = document.createElement('div'); document.body.append(container);
  const root = createRoot(container);
  try {
    await React.act(async () => root.render(React.createElement(query.QueryClientProvider, {client: ui.client}, chip.render())));
    assert.match(container.textContent, /GEV/);
    assert.match(container.querySelector('button').title, /Engine running/);
    assert.doesNotMatch(container.querySelector('button').title, /live/i);
    await ui.status({ running: false, installed: false, node24_ok: false });
    assert.match(container.querySelector('button').title, /Setup required/);
  } finally { await React.act(async () => root.unmount()); container.remove(); }
});

test('background fetch loading does not demote a ready globe', async () => {
  const ui = await boot(); const guest = ui.container.querySelector('webview');
  await ui.event(guest, 'dom-ready');
  await ui.event(guest, 'did-start-loading');
  assert.match(ui.container.querySelector('header').textContent, /Globe ready/);
});

test('missed dom-ready is recovered from actual guest document readiness', async () => {
  const ui = await boot(); const guest = ui.container.querySelector('webview');
  guest.getURL = () => 'http://localhost:4173/';
  guest.executeJavaScript = async () => true;
  await React.act(async () => { await new Promise(resolve => setTimeout(resolve, 1000)); });
  assert.match(ui.container.querySelector('header').textContent, /Globe ready/);
});
test('large surfaces use neutral surface tokens, not primary button fills',()=>{const code=fs.readFileSync(pluginPath,'utf8');for(const selector of ['gev-shell','gev-header','gev-drawer']){const rule=code.slice(code.indexOf('.'+selector+'{')).split('}')[0];assert.doesNotMatch(rule,/--ui-bg-primary/);assert.match(rule,/--ui-bg-(chrome|editor|elevated)/)}})
