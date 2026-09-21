# Plugin scope and checks

Version 0.1.0 is a Windows Hermes Desktop wrapper around the separately installed official GEV application. It does not certify or modify every third-party app feature.

## Plugin checks

- Existing backend suite: 29 tests passed.
- Existing frontend suite: 15 tests passed.
- Frontend JavaScript syntax check passed.
- Publication files reviewed for credentials, private machine paths and runtime data; the included screenshot is cropped to the application.
- Earlier local Desktop acceptance confirmed embedded globe rendering, scene loading, Focus/restore and native Provider Settings.

The automated suites exercise the wrapper with temporary fixtures and mocked app/host boundaries. No second Hermes installation or clean-install rehearsal was performed for this release.

## Known bug: incomplete interface after provider-key save

Saving a provider key can restart the upstream server and leave the embedded interface partially loaded or apparently unstyled.

**Workaround:** switch to a chat session, then return to GEV.

Status: open; deferred to a later plugin investigation. A restart/loading race is suspected, not established. This does not block the first release, and no upstream app modifications are included.

## Third-party scope

GEV owns its globe controls, providers, imagery, feeds and voice features. Exhaustive testing of its buttons and provider accounts is outside this wrapper release. Report reproducible integration problems through this repository's issues.
