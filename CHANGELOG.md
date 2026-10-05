# Changelog

## 0.1.3 — Upstream embed mode

- Adopt upstream GEV >= 0.2.1 embed mode: the SandboxedFrame now loads the globe-only `?embed=1` document instead of the full app. `/status` reports it as `embed_url`; `url` remains the full app for the external-browser handoff.
- The engine child environment sets `GEV_EMBED_FRAME_ANCESTORS=*` so upstream's opt-in framing allows the SDK frame's opaque origin. Only the `?embed=1` document becomes framable; every other document (including Provider Settings) keeps `X-Frame-Options: DENY` / `frame-ancestors 'none'`, and the rest of the upstream CSP is untouched.
- Update-path expectation: the engine update flow still refuses dirty checkouts and fast-forwards upstream; the local checkout must be at GEV >= 0.2.1 for embed mode (older engines keep full-app behavior with framing refused).

## 0.1.2 — Platform-scoped dependency admission

- Restrict the plugin's bounded index `psutil` requirement to non-Android targets, leaving Hermes' Android-only source pin untouched during universal resolution. Windows/macOS still require `psutil>=5.9,<8`; no core pin or SDK sandbox changes.
- Add marker regressions for the deferred Android target and supported desktop platforms. The original universal resolver conflict is reproduced independently and passes with this marker.
- Desktop frame acceptance is separate from package admission; see `docs/verification.md` for current evidence and limits.

## 0.1.1 — SDK frame migration

- Require Hermes >=0.21.5 and embed the separate GEV app through SDK `SandboxedFrame` using its default opaque-origin sandbox.
- Remove raw Electron guest, shared preview partition, private preload IPC, readiness scripting and scripted Provider Settings click. Report backend engine status; Provider Settings now directs users to GEV’s own settings chip.
- Preserve Start/Stop, explicit Reload, Focus/restore, update confirmation and opt-in key bridge. The backend and its trust controls are unchanged.
- Add focused regressions for frame lifecycle, truthful status, provider guidance and key-copy opt-in.

Live Desktop acceptance for the new frame remains pending. Windows foreground acceptance completed September 25 on v0.1.0; those results do not validate this replacement frame.

## 0.1.0 — First launch, Windows + macOS

First public release of the community GEV integration: native embedded interface, Focus mode, Control room, lifecycle controls, native provider setup, explicit separate-app updates, and consumer configuration outside the install tree.

- Support macOS engine start, exact-process adoption, stop and update; retain Windows process-tree shutdown.
- Discover npm in macOS/Homebrew layouts and detach the Mac engine from the launching terminal.
- Fix Windows CI's test-client import ordering without weakening its offline HTTP guard.
- Run CI on Windows and macOS, including a small real Node/HTTP start/adopt/stop/restart test.
- Require the guest readiness probe rather than declaring success on DOM readiness alone.
- Recreate the embedded view on explicit Reload globe; ordinary health polls preserve it.

- Publish the orbital-recon repository cover, real interface proof, and Windows/macOS setup including the separate Desktop capability switch.
- Confirm Mac sidebar acceptance and improved explicit reload live.

Known issue: saving a provider key may leave the guest partially initialized after upstream restart. Reload globe recreates the embedded view; the original Windows provider-save scenario still needs a live recheck. Not claimed fixed.
