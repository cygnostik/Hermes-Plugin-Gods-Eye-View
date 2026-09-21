# Security and data boundaries

This is a local desktop integration, not a sandbox. Install reviewed commits only.

- The plugin serves companion routes through Hermes' authenticated backend. The GEV app itself listens on loopback and enforces its own key-setup checks.
- Configuration selects an existing local GEV checkout and Node executable. Treat both as executable code you trust. Do not point it at an untrusted checkout.
- Status reports credential names/configured flags, never credential values. Credentials belong to GEV's own store or an explicitly invoked supported key bridge. No ambient key copying occurs at install, registration, status polling, or engine startup.
- The embedded view disables Node integration and uses the isolated Hermes preview partition. This is still a browser with network access to the application's providers.
- Start/Stop and upstream-app updates are explicit actions. Process adoption requires a matching Node executable, checkout, Vite script, and loopback listening socket. Health polling does not run Git or enumerate processes.
- Runtime configuration/logs live outside the replaceable plugin directory. The source repository must never contain real keys, local settings, runtime logs, or session exports.
- External links are admitted only for HTTP(S) and handed to the OS browser through Hermes' SDK.
- The plugin never self-updates. The separate application's explicit update action is not a catalog plugin update and is not pinned by the catalog entry.

Report security concerns privately to praxis@prodyn.ai. Do not include credentials or private session data in public issues. Redact console/network captures before sharing. Ordinary reproducible bugs can be filed through GitHub Issues.
