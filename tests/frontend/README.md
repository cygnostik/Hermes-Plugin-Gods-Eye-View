# Frontend regression tests

From the repository root on Windows, with a supported Node runtime on `PATH`:

```sh
npm ci --ignore-scripts
npm test
npm run check:frontend
```

The package uses the upstream GEV Node engine range: `>=24.14.0 <25 || >=26 <27`. The public plugin currently supports Windows only. The final suite was exercised on Windows with Node 24.21.0 and npm 11.19.0.

`npm test` first syntax-checks `desktop/plugin.js`, then executes that exact file directly through Node's `vm.SourceTextModule`. There is no copied plugin, transpilation, build output, or dependency on a local Hermes source checkout. `run-tests.cjs` uses the same Node executable as its parent, propagates syntax/test failures, and limits each subprocess to 90 seconds. Node's experimental VM-modules warning is expected.

## Dependencies

These are development-only packages, pinned exactly in `package.json` and resolved by `package-lock.json`:

- React and React DOM: `19.2.7`
- React Query: `5.101.2`
- JSDOM: `29.1.1`

The shipped desktop plugin still imports only the Hermes SDK, React, and React JSX runtime provided by Desktop. Installing these test dependencies does not install or configure the plugin in Hermes.

## Coverage

The suite has **15 passing tests**: all 13 original regressions are retained, plus unconfigured onboarding and failed-launch recovery tests. Existing backend-error, maintenance, and status-chip tests also assert the public setup/update guidance.

The tests exercise real React rendering, React DOM event handling, and the React Query cache. Hermes host/transport atoms and Electron guest APIs are controlled boundaries. Coverage includes:

- One native `webview`, profile/connection-scoped status, polling without remounting, and no iframe replacement.
- Invalid backend responses distinguished from an offline engine; setup guidance points to the README and `hermes gev configure`.
- Missing checkout/runtime disables start/update actions until configuration is available; failed launch preserves the backend's reason.
- Guest readiness, renderer-failure recovery, transient status errors, profile changes, and listener cleanup.
- Background fetch loading does not demote a ready globe; missed `dom-ready` is recovered by the guest readiness probe.
- Focus, Control room, confirmed upstream-app updates, failed actions, and fresh confirmation after drawer re-entry.
- Native Provider Settings shortcut/fallback, opt-in compatibility-bridge affordance, and validated external links.
- Truthful status-chip labels and neutral theme tokens.

Maintenance controls update the **upstream GEV application**, not the pinned Hermes plugin release. The tests never perform real engine updates or copy provider keys.

## Limits and open report

These are behavioral regressions, not Electron or visual end-to-end tests. They do not prove native compositing, rendered globe imagery, provider authentication, the real guest preload, or backend subprocess lifecycle. No live installation, Desktop restart, or credential changes are performed.

The report that saving a key in native Provider Settings and restarting can leave an unstyled/broken view remains **unconfirmed and unfixed**. This suite does not cover that real key-save/restart path and must not be presented as a fix or verification of it.
