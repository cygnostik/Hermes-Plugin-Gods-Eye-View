# Plugin scope and checks

The current development version supports Windows and macOS around the separately installed official GEV application. It does not certify or modify every third-party app feature.

## Plugin checks

- Backend suite: offline regressions plus a small native Node/HTTP lifecycle smoke on Windows and macOS CI.
- Frontend suite: 16 tests passed, including DOM-only false readiness and explicit guest recreation.
- Frontend JavaScript syntax check passed.
- Publication files reviewed for credentials, private machine paths and runtime data; the included screenshot is cropped to the application.
- Earlier local Desktop acceptance confirmed embedded globe rendering, scene loading, Focus/restore and native Provider Settings.

The frontend suite uses mocked host/guest boundaries. Most backend tests use temporary offline fixtures; `test_lifecycle_live.py` starts a real Node fixture, checks its HTTP status, adopts its exact listening process, stops it and repeats. It does not download GEV or call providers. The GitHub Actions matrix runs both supported operating systems; an automated green result is not a live Windows Desktop UI check.

On macOS, the official GEV checkout has also been launched through the real plugin backend and opened in Hermes' Electron preview. Full sidebar activation is a separate check after the first-install backend restart.

Upstream revision used for that Mac check: `f01b6a5d8462c182e03c94493fa24098c1ac3771` (unmodified official checkout, Node 26). Automated lifecycle checks use a local fixture rather than that network-connected application.

## Known bug: incomplete interface after provider-key save

Saving a provider key can restart the upstream server and leave the embedded interface partially loaded or apparently unstyled.

**Recovery:** Control room → Reload globe now recreates the embedded view. Switching to a chat session and back is the previously observed workaround. Either can reset transient scene state.

Status: the wrapper's separate false-readiness defect was reproduced and fixed; DOM readiness no longer cancels the application-load watchdog. The original provider-save rendering failure remains un-reproduced in this investigation and awaits the live Windows recheck. No upstream app modifications are included.

## Third-party scope

GEV owns its globe controls, providers, imagery, feeds and voice features. Exhaustive testing of its buttons and provider accounts is outside this wrapper release. Report reproducible integration problems through this repository's issues.
