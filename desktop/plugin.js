import { host, useValue, useQuery, useQueryClient, ROUTES_AREA, SIDEBAR_NAV_AREA, PALETTE_AREA, STATUSBAR_AREAS } from '@hermes/plugin-sdk'
import { useEffect, useRef, useState } from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'

const ID = 'gods-eye-view'
const ROUTE = '/gods-eye-view'
const SETUP_GUIDANCE = 'See the plugin README for Windows setup. Run hermes gev configure --root <existing GEV checkout> --node <node executable> with your checkout and supported Node runtime paths, then refresh engine status.'

function errorText(value) {
  const detail = value?.data?.detail || value?.detail || value?.error || value?.message
  return typeof detail === 'string' ? detail : 'The request could not be completed.'
}
function webURL(value) {
  try { const u = new URL(value); return typeof value === 'string' && ['http:', 'https:'].includes(u.protocol) && !u.username && !u.password ? u.href : null } catch { return null }
}
function useStatus(ctx) {
  const profile = useValue(host.state.profile)
  const connection = useValue(host.state.connectionId)
  const queryKey = [ID, 'status', profile, connection]
  const query = useQuery({ queryKey, queryFn: async () => {
    const result = await ctx.rest('/status')
    if (!result || result.ok === false || result.error || result.detail || typeof result.running !== 'boolean' || typeof result.installed !== 'boolean') {
      throw new Error('Plugin backend not loaded. Reconnect Desktop after installing backend. ' + errorText(result) + ' ' + SETUP_GUIDANCE)
    }
    if (result.running && !webURL(result.url)) throw new Error('The engine returned an invalid globe URL.')
    return result
  }, refetchInterval: 20000, retry: false })
  return { ...query, queryKey, scope: JSON.stringify([profile, connection]) }
}

function Emblem({ blueprint = false }) {
  return jsxs('svg', { viewBox: '0 0 240 240', fill: 'none', 'aria-hidden': true, className: blueprint ? 'gev-blueprint' : 'gev-emblem', children: [
    jsx('circle', { cx: 120, cy: 120, r: 82, stroke: 'currentColor' }),
    jsx('ellipse', { cx: 120, cy: 120, rx: 36, ry: 82, stroke: 'currentColor' }),
    jsx('ellipse', { cx: 120, cy: 120, rx: 82, ry: 31, stroke: 'currentColor' }),
    jsx('ellipse', { cx: 120, cy: 120, rx: 111, ry: 51, transform: 'rotate(-35 120 120)', stroke: 'currentColor' }),
    jsx('path', { d: 'M120 17v22M120 201v22M17 120h22M201 120h22M108 120h24M120 108v24', stroke: 'currentColor' }),
    jsx('circle', { cx: 210, cy: 65, r: 4, fill: 'currentColor' })
  ] })
}

const CSS = `
.gev-shell{position:absolute;inset:0;display:flex;flex-direction:column;min-width:0;min-height:0;overflow:hidden;background:var(--ui-bg-chrome);color:var(--ui-text-primary);font-family:inherit;isolation:isolate}
.gev-header{flex-shrink:0;display:flex;align-items:center;gap:12px;padding:0 12px;border-bottom:1px solid var(--ui-stroke-secondary);background:var(--ui-bg-chrome);z-index:2}
.gev-emblem{width:26px;height:26px;flex:none;color:var(--ui-accent);stroke-width:5}
.gev-title{font-size:11px;letter-spacing:.13em;text-transform:uppercase;font-weight:650;white-space:nowrap;margin:0}
.gev-health{font-size:11px;color:var(--ui-text-secondary);margin-left:auto;white-space:nowrap}
.gev-stage{position:relative;display:flex;flex:1;min-height:0;min-width:0;overflow:hidden}
.gev-empty{display:flex;flex:1;position:relative;align-items:center;justify-content:center;flex-direction:column;padding:28px;text-align:center;overflow:auto;background:radial-gradient(ellipse at 50% 35%,color-mix(in srgb,var(--ui-accent) 7%,transparent),transparent 65%)}
.gev-blueprint{width:clamp(120px,24vw,290px);max-height:34vh;flex:none;color:var(--ui-accent);opacity:.48;stroke-width:.65;margin-bottom:22px}
.gev-kicker{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--ui-text-secondary);margin:0 0 12px}
.gev-empty h2{font-size:clamp(24px,3.4vw,44px);font-weight:450;letter-spacing:-.045em;margin:0 0 12px;line-height:1.1}
.gev-copy{font-size:13px;line-height:1.65;color:var(--ui-text-secondary);max-width:440px;margin:0 0 20px}
.gev-caption{font-size:10px;color:var(--ui-text-tertiary,var(--ui-text-secondary));letter-spacing:.08em;margin-top:28px}
.gev-button{font:inherit;font-size:12px;line-height:1.3;padding:7px 11px;min-height:30px;border:1px solid var(--ui-stroke-secondary);border-radius:6px;background:var(--ui-bg-secondary);color:var(--ui-text-primary);cursor:pointer;transition:background 160ms ease,border-color 160ms ease,transform 160ms ease}
.gev-button:hover:enabled{border-color:var(--ui-accent);background:color-mix(in srgb,var(--ui-accent) 9%,var(--ui-bg-chrome))}
.gev-button:active:enabled{transform:translateY(1px)}
.gev-button:focus-visible{outline:2px solid var(--ui-accent);outline-offset:3px}
.gev-button:disabled{opacity:.45;cursor:not-allowed}
.gev-body{display:flex;flex:1;min-height:0;min-width:0;position:relative}
.gev-notice{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 14px;border-bottom:1px solid var(--ui-stroke-secondary);background:var(--ui-bg-secondary);font-size:12px;line-height:1.5;max-height:120px;overflow:auto;flex-shrink:0}
.gev-notice[role=alert]{border-left:3px solid var(--ui-danger,var(--ui-accent))}
.gev-notice span{min-width:0;overflow-wrap:anywhere}
.gev-drawer{box-sizing:border-box;width:350px;max-width:100%;flex:none;padding:22px;overflow:auto;overscroll-behavior:contain;border-left:1px solid var(--ui-stroke-secondary);background:var(--ui-bg-chrome);animation:gev-arrive 220ms cubic-bezier(.2,.8,.2,1);z-index:3}
.gev-drawer-title{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:20px}
.gev-drawer-title h2{margin:0;font-size:25px;letter-spacing:-.04em;font-weight:500}
.gev-drawer .gev-copy{font-size:12px;margin:10px 0 15px}
.gev-group{border-top:1px solid var(--ui-stroke-secondary);padding:20px 0}
.gev-group h3{font-size:12px;font-weight:650;letter-spacing:.04em;margin:0}
.gev-actions{display:flex;flex-wrap:wrap;gap:7px}
.gev-confirm{padding:14px;margin-top:14px;border:1px solid var(--ui-accent);border-radius:8px;background:color-mix(in srgb,var(--ui-accent) 5%,transparent)}
.gev-confirm h4{font-size:13px;margin:0}.gev-confirm button+button{margin-left:8px}
.gev-keys{list-style:none;padding:0;margin:16px 0;font-size:11px;line-height:1.9;color:var(--ui-text-secondary)}
.gev-compat{font-size:12px;margin-top:18px}.gev-compat summary{cursor:pointer;color:var(--ui-text-secondary)}.gev-compat label{display:block;line-height:1.6;margin-bottom:10px}.gev-compat input{accent-color:var(--ui-accent)}
.gev-restore{position:absolute;top:8px;right:12px;z-index:4;opacity:.8}.gev-restore:hover,.gev-restore:focus-visible{opacity:1}
.gev-health{min-width:0;overflow:hidden;text-overflow:ellipsis}
.gev-header>.gev-button{flex-shrink:0}
@keyframes gev-arrive{from{opacity:0;transform:translateX(12px)}to{opacity:1;transform:translateX(0)}}
@media(max-width:700px){.gev-drawer{position:absolute;inset:0 0 0 auto;width:min(350px,100%)}.gev-title{display:none}.gev-health{margin-left:0;flex:1}}
@media(prefers-reduced-motion:reduce){.gev-shell *{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
@media(max-width:560px){.gev-header{gap:7px;padding:0 8px}.gev-title{max-width:110px;overflow:hidden;text-overflow:ellipsis}.gev-health{font-size:10px}}
`
function Guest({ url, guestRef, onState, ctx, onMessage }) {
  useEffect(() => {
    const guest = guestRef.current
    if (!guest) return
    let timer, probeTimer, active = true, generation = 0
    const cancel = () => { clearTimeout(timer); clearTimeout(probeTimer) }
    const ready = () => { cancel(); onState({ phase: 'ready', text: 'Globe ready' }) }
    const probe = async epoch => {
      if (!active || epoch !== generation) return
      try {
        if (typeof guest.executeJavaScript === 'function' && typeof guest.getURL === 'function' && new URL(guest.getURL()).origin === new URL(url).origin) {
          const loaded = await guest.executeJavaScript(`document.readyState !== 'loading' && Boolean(document.querySelector('canvas'))`)
          if (active && epoch === generation && loaded === true) { ready(); return }
        }
      } catch { /* Guest may not be attached yet. Retry only within this load. */ }
      if (active && epoch === generation) probeTimer = setTimeout(() => probe(epoch), 500)
    }
    const waiting = () => {
      cancel(); const epoch = ++generation
      onState({ phase: 'loading', text: 'Loading globe' })
      timer = setTimeout(() => { generation++; clearTimeout(probeTimer); onState({ phase: 'error', text: 'The globe is taking longer than expected.' }) }, 30000)
      probeTimer = setTimeout(() => probe(epoch), 500)
    }
    const failed = event => { if (event.isMainFrame === false || event.errorCode === -3) return; generation++; cancel(); onState({ phase: 'error', text: 'Globe could not load. ' + (event.errorDescription || '') }) }
    const gone = () => { generation++; cancel(); onState({ phase: 'error', text: 'Globe renderer stopped. Reload to recover.' }) }
    const external = async event => {
      if (event.channel !== 'preview-open-external') return
      const target = webURL(event.args?.[0])
      if (!target) return
      try { if (await ctx.os.openExternal(target) !== true && active) onMessage({ kind: 'error', text: 'Could not open the browser. This Desktop build may not support external links.' }) }
      catch (e) { if (active) onMessage({ kind: 'error', text: errorText(e) }) }
    }
    const listeners = { 'did-start-navigation': event => { if (event.isMainFrame !== false && !event.isInPlace) waiting() }, 'dom-ready': ready, 'did-fail-load': failed, 'render-process-gone': gone, 'ipc-message': external }
    Object.entries(listeners).forEach(([name, fn]) => guest.addEventListener(name, fn))
    waiting()
    return () => { active = false; generation++; cancel(); Object.entries(listeners).forEach(([name, fn]) => guest.removeEventListener(name, fn)) }
  }, [url, guestRef, onState, ctx, onMessage])
  return jsx('webview', { ref: guestRef, src: url, partition: 'persist:hermes-preview', webpreferences: 'contextIsolation=yes,nodeIntegration=no,sandbox=yes', title: 'God’s Eye View — native globe', style: { display: 'flex', flex: '1 1 auto', width: '100%', height: '100%', minWidth: 0, minHeight: 0, border: 'none' } })
}
function Button({ children, ...props }) { return jsx('button', { type: 'button', className: 'gev-button', ...props, children }) }
function Workspace({ ctx, query }) {
  const status = query.data
  const client = useQueryClient()
  const guestRef = useRef(null)
  const deckRef = useRef(null)
  const alive = useRef(true)
  const lock = useRef(false)
  const [view, setView] = useState({ phase: 'loading', text: 'Loading globe' })
  const [drawer, setDrawer] = useState(false)
  const [focus, setFocus] = useState(false)
  const [confirm, setConfirm] = useState(false)
  const [bridge, setBridge] = useState(false)
  const [busy, setBusy] = useState('')
  const [message, setMessage] = useState(null)
  useEffect(() => { alive.current = true; return () => { alive.current = false } }, [])
  const current = () => alive.current && JSON.stringify([host.state.profile.get(), host.state.connectionId.get()]) === query.scope
  const running = status?.running === true
  const setupRequired = status?.installed === false || status?.node24_ok === false
  const disabled = Boolean(busy || query.error || query.isPending)
  const close = () => { setDrawer(false); setConfirm(false); setBridge(false); deckRef.current?.focus() }
  const act = async name => {
    if (lock.current || !current()) return
    if (name === 'update' && !confirm || name === 'bridge' && !bridge) return
    const paths = { start: '/start', stop: '/stop', update: '/update', check: '/updates/check', bridge: '/keys/hermes' }
    if (!paths[name]) return
    lock.current = true; setBusy(name); setMessage(null); setConfirm(false)
    try {
      const result = await ctx.rest(paths[name], { method: 'POST', timeoutMs: name === 'update' ? 900000 : 120000 })
      if (!result || result.ok !== true || result.error || result.detail) throw new Error(errorText(result))
      if (!current()) return
      const text = name === 'check' ? (Number.isInteger(result.commits_behind) ? `Update check complete: ${result.commits_behind} upstream commit(s) behind.` : 'Update check complete. Review engine version below.') : name === 'update' ? 'Update completed. Check engine status before starting again.' : name === 'bridge' ? 'Compatibility bridge completed. Key configuration does not verify provider access.' : `${name === 'start' ? 'Start' : 'Stop'} request accepted. Refreshing engine status.`
      setMessage({ kind: 'info', text })
    } catch (e) { if (current()) setMessage({ kind: 'error', text: errorText(e) + (name === 'start' ? ' ' + SETUP_GUIDANCE : '') }) }
    finally { lock.current = false; if (current()) { setBusy(''); await client.invalidateQueries({ queryKey: query.queryKey }) } }
  }
  const external = async () => {
    const target = webURL(status?.url)
    if (!target) return
    try { if (await ctx.os.openExternal(target) !== true && current()) setMessage({ kind: 'error', text: 'Could not open the browser. Use a Desktop build with native external-link support.' }) }
    catch (e) { if (current()) setMessage({ kind: 'error', text: errorText(e) }) }
  }
  const providers = async () => {
    try {
      const guest = guestRef.current
      if (view.phase !== 'ready' || typeof guest?.executeJavaScript !== 'function' || typeof guest?.getURL !== 'function' || new URL(guest.getURL()).origin !== new URL(status.url).origin) throw new Error('unsupported')
      const opened = await guest.executeJavaScript(`(() => { const panel = document.querySelector('#key-setup[data-initialized="true"]'); const chip = document.querySelector('#key-setup-chip'); if (!panel || !chip) return false; if (panel.hidden) chip.click(); return panel.hidden === false; })()`)
      if (opened !== true) throw new Error('unsupported')
      if (current()) { setMessage(null); close() }
    } catch { if (current()) setMessage({ kind: 'error', text: 'Open Provider Settings inside the globe using its native settings chip. This build does not expose the supported shortcut.' }) }
  }
  const reload = () => { try { if (typeof guestRef.current?.reload !== 'function') throw new Error('Reload is unavailable in this Desktop build.'); guestRef.current.reload(); setView({ phase: 'loading', text: 'Loading globe' }) } catch (e) { setView({ phase: 'error', text: errorText(e) }) } }
  const engine = query.error ? 'Connection interrupted' : query.isPending ? 'Connecting to backend' : running ? 'Engine running' : setupRequired ? 'Setup required' : 'Engine offline'
  const notice = message && jsxs('div', { className: 'gev-notice', role: message.kind === 'error' ? 'alert' : 'status', children: [jsx('span', { children: message.text }), jsx(Button, { onClick: () => setMessage(null), 'aria-label': 'Dismiss message', children: 'Dismiss' })] })
  return jsxs('section', { className: 'gev-shell', 'aria-label': 'God’s Eye View workspace', children: [
    jsx('style', { children: CSS }),
    !focus && jsxs('header', { className: 'gev-header', style: { height: '40px' }, children: [jsx(Emblem, {}), jsx('h1', { className: 'gev-title', children: 'God’s Eye View' }), jsx('span', { className: 'gev-health', role: 'status', title: engine + (running ? ' · ' + view.text : ''), children: engine + (running ? ' · ' + view.text : '') }), jsx(Button, { onClick: () => { close(); setFocus(true) }, children: 'Focus' }), jsx(Button, { ref: deckRef, onClick: () => drawer ? close() : setDrawer(true), 'aria-expanded': drawer, children: 'Control room' })] }),
    focus && jsx(Button, { className: 'gev-button gev-restore', onClick: () => setFocus(false), children: 'Show flight deck' }),
    query.error && running && jsxs('div', { className: 'gev-notice', role: 'alert', children: [jsx('span', { children: 'Connection interrupted. Last globe retained; engine status is unverified. ' + errorText(query.error) }), jsx(Button, { onClick: () => query.refetch(), children: 'Retry connection' })] }),
    view.phase === 'error' && running && jsxs('div', { className: 'gev-notice', role: 'alert', children: [jsx('span', { children: view.text }), jsx(Button, { onClick: reload, children: 'Reload globe' })] }),
    notice,
    jsxs('div', { className: 'gev-body', children: [
      jsx('main', { className: 'gev-stage', children: running ? jsx(Guest, { url: status.url, guestRef, onState: setView, ctx, onMessage: setMessage }) : jsxs('div', { className: 'gev-empty', children: [jsx(Emblem, { blueprint: true }), jsx('p', { className: 'gev-kicker', children: 'Geospatial workspace' }), jsx('h2', { children: query.error ? 'Connection unavailable.' : query.isPending ? 'Establishing perspective.' : setupRequired ? 'Set up your perspective.' : 'A wider perspective.' }), jsx('p', { className: 'gev-copy', role: query.error ? 'alert' : 'status', children: query.error ? errorText(query.error) : query.isPending ? 'Checking the plugin backend. The engine state is not yet known.' : setupRequired ? SETUP_GUIDANCE : 'The engine is offline. Start it to explore the native God’s Eye View globe.' }), query.error ? jsx(Button, { onClick: () => query.refetch(), children: 'Retry connection' }) : !query.isPending && jsx(Button, { onClick: () => act('start'), disabled: disabled || setupRequired, children: busy === 'start' ? 'Starting engine…' : 'Start engine' }), jsx('p', { className: 'gev-caption', children: 'Decorative orbital blueprint · not live data' })] }) }),
      drawer && jsxs('aside', { className: 'gev-drawer', role: 'dialog', 'aria-label': 'Control room', 'aria-modal': false, onKeyDown: e => { if (e.key === 'Escape') { e.stopPropagation(); close() } }, children: [
        jsxs('div', { className: 'gev-drawer-title', children: [jsxs('div', { children: [jsx('p', { className: 'gev-kicker', children: 'Workspace systems' }), jsx('h2', { children: 'Control room' })] }), jsx(Button, { autoFocus: true, onClick: close, 'aria-label': 'Close Control room', children: 'Close' })] }),
        jsx('p', { className: 'gev-copy', children: 'The globe stays native. Manage the engine here; explore layers, places and scenes inside God’s Eye View.' }),
        jsxs('section', { className: 'gev-group', children: [jsx('h3', { children: 'Engine' }), jsx('p', { className: 'gev-copy', children: `${engine}${status?.version ? ' · ' + status.version : ''}` }), jsxs('div', { className: 'gev-actions', children: [jsx(Button, { disabled: disabled || (!running && setupRequired), onClick: () => act(running ? 'stop' : 'start'), children: running ? 'Stop engine' : 'Start engine' }), jsx(Button, { disabled: !running, onClick: reload, children: 'Reload globe' }), jsx(Button, { disabled: !running, onClick: external, children: 'Open in browser' })] })] }),
        jsxs('section', { className: 'gev-group', children: [jsx('h3', { children: 'Provider configuration' }), jsx('p', { className: 'gev-copy', children: 'Configure providers in GEV. A configured key is not proof of authentication, live feeds or coverage.' }), jsx(Button, { onClick: providers, disabled: !running, children: 'Provider Settings' }),
          Array.isArray(status?.keys?.keys) && jsx('ul', { className: 'gev-keys', children: status.keys.keys.map((k, index) => jsx('li', { children: `${k.title || k.id || 'Provider'} — ${k.set === true ? 'configured' : 'not configured'}` }, k.id || index)) }),
          jsxs('details', { className: 'gev-compat', children: [jsx('summary', { children: 'Compatibility bridge (optional)' }), jsx('p', { className: 'gev-copy', children: 'Explicitly copy compatible Hermes environment keys into GEV. This does not reuse OAuth subscriptions or verify provider access.' }), jsxs('label', { children: [jsx('input', { type: 'checkbox', checked: bridge, onChange: e => setBridge(e.target.checked) }), ' Allow compatible key copying' ] }), jsx(Button, { disabled: disabled || !running || !bridge, onClick: () => act('bridge'), children: 'Bridge compatible keys' })] })
        ] }),
        jsxs('section', { className: 'gev-group', children: [jsx('h3', { children: 'Maintenance' }), jsx('p', { className: 'gev-copy', children: 'Updates apply to the upstream GEV app, not this Hermes plugin. They are explicit, never part of health polling. Local modifications are protected by the backend.' }), jsxs('div', { className: 'gev-actions', children: [jsx(Button, { disabled: disabled || setupRequired, onClick: () => act('check'), children: 'Check updates' }), jsx(Button, { disabled: disabled || setupRequired || !status?.installed, onClick: () => setConfirm(true), children: 'Update engine' })] }), confirm && jsxs('div', { className: 'gev-confirm', children: [jsx('h4', { children: 'Update and stop the engine?' }), jsx('p', { className: 'gev-copy', children: 'This may stop the globe and install upstream dependencies. Local changes can block the update. Start again after completion.' }), jsx(Button, { disabled, onClick: () => act('update'), children: 'Confirm update' }), jsx(Button, { onClick: () => setConfirm(false), children: 'Cancel' })] })] }),
        busy && jsx('p', { role: 'status', className: 'gev-copy', children: busy === 'update' ? 'Updating engine… this can take several minutes.' : 'Request in progress…' }),
        jsx('p', { className: 'gev-caption', children: 'Native scenes and feed status remain inside GEV. No telemetry is inferred by this shell.' })
      ] })
    ] })
  ] })
}
function StatusChip({ ctx }) {
  const query = useStatus(ctx)
  const label = query.error ? 'Backend unavailable' : query.isPending ? 'Checking engine' : query.data?.running ? 'Engine running' : query.data?.installed === false || query.data?.node24_ok === false ? 'Setup required' : 'Engine offline'
  return jsx('button', { type: 'button', title: label + ' — open God’s Eye View', onClick: () => host.navigate(ROUTE), style: { border: '1px solid var(--ui-stroke-secondary)', borderRadius: 4, background: 'transparent', color: query.data?.running && !query.error ? 'var(--ui-accent)' : 'var(--ui-text-secondary)', padding: '1px 7px', fontSize: 10, cursor: 'pointer' }, children: 'GEV' })
}
function Page({ ctx }) { const query = useStatus(ctx); return jsx(Workspace, { ctx, query }, query.scope) }
export default {
  id: ID, name: 'God’s Eye View', description: 'An immersive native geospatial workspace.',
  register(ctx) {
    ctx.registerMany([
      { id: 'page', area: ROUTES_AREA, title: 'God’s Eye View', data: { path: ROUTE }, render: () => jsx(Page, { ctx }) },
      { id: 'nav', area: SIDEBAR_NAV_AREA, order: 47, data: { path: ROUTE, label: 'God’s Eye View', codicon: 'globe' } },
      { id: 'status-chip', area: STATUSBAR_AREAS.right, order: 80, render: () => jsx(StatusChip, { ctx }) },
      { id: 'open', area: PALETTE_AREA, data: { id: `${ID}.open`, label: 'God’s Eye View: Open workspace', run: () => host.navigate(ROUTE) } }
    ])
  }
}