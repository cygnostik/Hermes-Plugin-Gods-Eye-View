# v0.1.3-legacy.1 — LEGACY COMPATIBILITY

Separate prerelease, not SDK/catalog approved. Restore desktop/plugin.js and tests/frontend/plugin.test.cjs byte-for-byte from v0.1.0; preserve v0.1.2 backend and Android dependency marker. No upstream headers, SDK sandbox, core or provider values changed. Historical visual acceptance is not a fresh acceptance of this prerelease.

# Changelog

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
