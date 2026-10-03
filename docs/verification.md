# Plugin scope and checks

## v0.1.3-legacy.1 checks (October 2, 2026 Pacific)

Fresh Windows checks: npm lockfile install with scripts disabled; 16 matching legacy frontend regressions and 34 backend regressions PASS, including the real Node/HTTP lifecycle fixture and platform dependency-marker checks. JavaScript syntax passes. The renderer and its test file match the v0.1.0 Git blobs; backend sources remain unchanged from v0.1.2.

The installed local Hermes validator and doctor both returned exit 0, including a misleading green desktop-surface check for this raw-webview bundle. This automated result does NOT override the published SDK restriction or Tek's explicit review. This remains noncompliant and not catalog approved; no scanner was bypassed and no exception is claimed. Native legacy QA and a fresh URL installation were not performed; the active SDK installation was preserved, with no Desktop restart or provider operation. Regression mocks are not a current embedded-rendering pass.



The first release supports Windows and macOS around the separately installed official GEV application. It does not certify or modify every third-party app feature.

## Integration status — October 2, 2026 (Pacific time)

The catalog SDK line remains **v0.1.2**, pinned to `8eec0b3ede21b4971e840cb1cf35457087a1a6cb`. Catalog admission is not live rendering acceptance. Current Windows acceptance recovered the backend and controls, but the local GEV engine rejects the SDK frame with `Content-Security-Policy: frame-ancestors 'none'` and `X-Frame-Options: DENY`. The native console confirms the framing refusal. This is a regression after the SDK-required migration, not evidence that the original Electron guest never worked.

**Immediate supported fallback:** Start engine, then **Open in browser**. Browser globe rendering and camera interaction were observed in the October 2 acceptance run; they do not fulfill embedded rendering. After Desktop quits, an explicit Start may be needed. Provider-save recovery in the SDK frame remains untested because framing is rejected first.

### LEGACY COMPATIBILITY — separate, not SDK/catalog approved

- [v0.1.0 historical release](https://github.com/cygnostik/Hermes-Plugin-Gods-Eye-View/releases/tag/v0.1.0), source `c871d9b1e17a962acb3bd7d2a8d851fe313f8daf`, was already public. Historical embedded live verification dates are September 20 and September 25, 2026; the [September 25 exact-pin Windows results](https://github.com/cygnostik/Hermes-Plugin-Gods-Eye-View/issues/1) include visible camera interaction and scoped provider-save recovery. These are not fresh tests of today's Hermes/upstream combination.
- [v0.1.3-legacy.1 compatibility prerelease](https://github.com/cygnostik/Hermes-Plugin-Gods-Eye-View/releases/tag/v0.1.3-legacy.1) restores only that renderer and its matching frontend tests onto the v0.1.2 backend/dependency baseline. Unlike immutable v0.1.0, it retains `psutil>=5.9,<8; sys_platform != 'android'`, avoiding the known universal Android resolution conflict. It does not add Android support.
- The legacy renderer uses raw Electron webview, Hermes' shared `persist:hermes-preview` partition, private preload IPC and guest scripting. This coupling is outside the supported SDK and is **not catalog approved**. Host changes may break it. Current validation/installation can reject it; **stop on refusal**, do not bypass scanners, copy it into discovery, weaken sandbox/headers or treat historical validation as current approval.
- The compatibility release is a separate branch/prerelease, never a catalog re-pin or replacement for main. See its release notes for the exact immutable source/install reference, actual regression results and admission result. No current native rendering acceptance or maintainer exception is claimed.

## Historical v0.1.2 dependency admission checks

Hermes' universal resolver also evaluates its deferred Android environment. The old unconditional `psutil>=5.9,<8` declaration conflicts there with Hermes' Android-only source pin (which declares 8.0.0), even though Windows uses the compatible index pin 7.2.2. v0.1.2 excludes Android from this Desktop plugin requirement, without changing core, widening the desktop version bound, or changing the SDK sandbox.

On Windows, a minimal universal `uv lock` probe using the exact core psutil declarations fails before this marker change and resolves after it. 34 backend tests (including two marker regressions and the real Node/HTTP lifecycle fixture), 14 frontend tests, JavaScript syntax, diff checks and plugin admission validation pass. Marker tests are dependency-data checks, not Android execution. Subsequent live frame acceptance is blocked as described above; installation/enable readback is not evidence of a rendered globe.

## v0.1.1 SDK migration checks

Local checks on macOS: 14 frontend tests and 32 backend tests pass (including the native Node/HTTP lifecycle fixture); JavaScript syntax and diff checks pass. Plugin admission validation reports all checks green, scanner `safe`, and no warnings; Plugin Doctor reports no findings. The current upstream Desktop surface lint also passes. Five migration regressions fail against the original v0.1.0 bundle.

The public entrypoint now imports `SandboxedFrame` from `@hermes/plugin-sdk` and uses its default sandbox. Engine status comes solely from backend `/status`; the wrapper does not claim document or canvas readiness. Provider Settings shows directions to GEV’s own settings chip. Reload globe explicitly recreates the frame; polling and Focus retain it. The backend is unchanged.

The frontend suite executes the public entrypoint with a mocked SDK boundary. It covers the frame props, polling/reload/profile lifecycle, truthful status, no private IPC handoff, provider guidance without scripting, update confirmation, key-copy opt-in, and error handling. The mock does not establish browser sandbox enforcement or live GEV compatibility.

Backend regressions include offline fixtures and a small native Node/HTTP lifecycle test that starts, adopts, stops and restarts its own fixture. It does not download GEV or call providers. Platform CI is distinct from live Desktop acceptance.

**Historical pre-acceptance caution for v0.1.1 (superseded by the framing blocker above):** opaque-origin framing can affect GEV provider requests, storage and configuration behavior. No same-origin or popup privileges are added to compensate; use Open in browser when an upstream feature requires the standalone app.

## Historical v0.1.0 acceptance

Windows foreground acceptance completed September 25 on the exact v0.1.0 pin: automatic provider-save recovery, Reload globe, visible camera interaction, Start/Stop, Focus/restore and restart persistence passed. Results and sanitized screenshots are in [issue #1](https://github.com/cygnostik/Hermes-Plugin-Gods-Eye-View/issues/1). The original defect was not reproduced. Earlier macOS acceptance used the unmodified official GEV checkout `f01b6a5d8462c182e03c94493fa24098c1ac3771` with Node 26.

These historical results concern the previous Electron guest, not the v0.1.1 SDK frame.

## Third-party scope

GEV owns its globe controls, providers, imagery, feeds and voice features. Exhaustive testing of its buttons and provider accounts is outside this wrapper release. Report reproducible integration problems through this repository's issues.

- Voice/microphone permissions in the embedded view have not been verified.
- Guest popup/navigation restrictions follow the SDK default sandbox. Use the explicit Open in browser control for standalone GEV when needed.
- Remote Hermes backends and Linux lifecycle management are not supported by this wrapper release. GEV and Hermes Desktop must run on the same machine.
