# Plugin scope and checks

The first release supports Windows and macOS around the separately installed official GEV application. It does not certify or modify every third-party app feature.

## v0.1.1 SDK migration checks

Local checks on macOS: 14 frontend tests and 32 backend tests pass (including the native Node/HTTP lifecycle fixture); JavaScript syntax and diff checks pass. Plugin admission validation reports all checks green, scanner `safe`, and no warnings; Plugin Doctor reports no findings. The current upstream Desktop surface lint also passes. Five migration regressions fail against the original v0.1.0 bundle.

The public entrypoint now imports `SandboxedFrame` from `@hermes/plugin-sdk` and uses its default sandbox. Engine status comes solely from backend `/status`; the wrapper does not claim document or canvas readiness. Provider Settings shows directions to GEV’s own settings chip. Reload globe explicitly recreates the frame; polling and Focus retain it. The backend is unchanged.

The frontend suite executes the public entrypoint with a mocked SDK boundary. It covers the frame props, polling/reload/profile lifecycle, truthful status, no private IPC handoff, provider guidance without scripting, update confirmation, key-copy opt-in, and error handling. The mock does not establish browser sandbox enforcement or live GEV compatibility.

Backend regressions include offline fixtures and a small native Node/HTTP lifecycle test that starts, adopts, stops and restarts its own fixture. It does not download GEV or call providers. Platform CI is distinct from live Desktop acceptance.

**Live acceptance remains pending for v0.1.1:** opaque-origin framing can affect GEV provider requests, storage and configuration behavior. No same-origin or popup privileges are added to compensate; use Open in browser when an upstream feature requires the standalone app.

## Historical v0.1.0 acceptance

Windows foreground acceptance completed September 25 on the exact v0.1.0 pin: automatic provider-save recovery, Reload globe, visible camera interaction, Start/Stop, Focus/restore and restart persistence passed. Results and sanitized screenshots are in [issue #1](https://github.com/cygnostik/Hermes-Plugin-Gods-Eye-View/issues/1). The original defect was not reproduced. Earlier macOS acceptance used the unmodified official GEV checkout `f01b6a5d8462c182e03c94493fa24098c1ac3771` with Node 26.

These historical results concern the previous Electron guest, not the v0.1.1 SDK frame.

## Third-party scope

GEV owns its globe controls, providers, imagery, feeds and voice features. Exhaustive testing of its buttons and provider accounts is outside this wrapper release. Report reproducible integration problems through this repository's issues.

- Voice/microphone permissions in the embedded view have not been verified.
- Guest popup/navigation restrictions follow the SDK default sandbox. Use the explicit Open in browser control for standalone GEV when needed.
- Remote Hermes backends and Linux lifecycle management are not supported by this wrapper release. GEV and Hermes Desktop must run on the same machine.
