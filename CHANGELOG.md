# Changelog

## Unreleased — Windows + macOS

- Support macOS engine start, exact-process adoption, stop and update; retain Windows process-tree shutdown.
- Discover npm in macOS/Homebrew layouts and detach the Mac engine from the launching terminal.
- Fix Windows CI's test-client import ordering without weakening its offline HTTP guard.
- Run CI on Windows and macOS, including a small real Node/HTTP start/adopt/stop/restart test.
- Require the guest readiness probe rather than declaring success on DOM readiness alone.
- Recreate the embedded view on explicit Reload globe; ordinary health polls preserve it.

## 0.1.0

First public packaging of the community GEV integration: native embedded interface, Focus mode, Control room, lifecycle controls, native provider setup, explicit separate-app updates, and consumer configuration outside the install tree. Includes loading-readiness recovery and neutral Hermes surface styling.

Known issue: saving a provider key may leave the guest partially initialized after upstream restart; switching away and back is the observed recovery. Not claimed fixed.
