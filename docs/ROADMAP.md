# GEV: Windows baseline, Mac path, agent control

**Launch status:** the shared Windows/macOS wrapper passes CI, the Mac workspace and improved reload have been accepted live, and the first-launch repository presentation is approved. Catalog admission is pending. The Windows installation will be checked later. Agent control remains a separate future decision. Keep official GEV as the engine.

## 1. Windows “Basic Version”

Define Basic as **the full native GEV interface inside Hermes**, with reliable Start/Stop, Focus, provider setup and explicit updates—not a reduced globe. It needs Hermes Desktop ≥0.21.3, a separate official GEV checkout and compatible Node 24/26. GEV starts keyless; photorealistic imagery and voice are optional provider upgrades.[1][3]

**Next work:**
- The tested Mac GEV revision is recorded in [verification](verification.md). The original Windows CI failure[5] is fixed; the shared wrapper now has passing Windows and macOS CI.
- Recheck provider-key-save recovery on Windows. DOM-only false readiness is fixed and explicit reload recreates the guest, but the original rendering failure remains unresolved.
- Accept Basic on an actual Windows Desktop: clean setup, keyless globe, Start/Stop, provider-save recovery, Focus, links and dirty-checkout-safe updates. Check embedded microphone/voice separately before claiming it works.

## 2. Mac: port, don’t rebuild

**Official GEV already runs on macOS.** The Windows restriction belongs to this wrapper’s lifecycle management; the globe itself does not need a Mac rewrite.[1][4]

| Approach | Build effort / coding-token demand* | Benefit and verdict |
|---|---|---|
| **Port this Hermes wrapper** | **Medium** | Preserve native GEV and one shared plugin. **Recommended.** |
| New Mac shell, reusing GEV components | High | More custom UX; worthwhile only if we want a separate product rather than a Hermes plugin. |
| Rewrite the globe/application | Very high | Maximum control, but rebuilds feeds, camera behavior, scenes and voice. No present benefit justifies it. |

**Mac milestone:** lifecycle and Node/npm adaptation are implemented; the official globe has rendered in Hermes' Electron preview. Sidebar activation and improved explicit reload have now been accepted live. Microphone/provider checks remain separate. Upstream has reusable application components, but its standalone shell still assumes one application per page; reuse is not a drop-in native UI toolkit.[2]

## 3. What agent control actually adds

**Your understanding was right:** built-in voice already drives 28 actions, including fly-to, orbit, route flight, layers, tracking, annotations and scenes. It uses OpenAI Realtime. Those actions also have a deterministic JavaScript runner; upstream’s own browser tests call it without a model. That is an integration point, not an already-installed Hermes/MCP service.[1][12]

| Option | Build effort* | Runtime token demand* | Practical value |
|---|---|---|---|
| Keep native voice | Low; verify embedding | Metered voice; AI HUD summaries are separate | Hands-free exploration already exists. |
| **Hermes → structured actions** | **Low–medium** | **Low per request; no model needed while orbit runs** | Use chat context to navigate, stage layers and inspect results. Best first addition. |
| Agent-authored tours / briefings | Medium | Generation/editing turns; deterministic replay | Repeatable presentations and saved workflows using Director.[6] |
| Continuous screenshot-driven operator | High to make dependable | High, repeated image/reasoning turns | Reserve for unsupported controls; poor default. |

Do not route Hermes through a second conversational voice agent. Start with **read state, fly-to, orbit/stop and layer toggles**; use an allowlist, compact result readback, timeouts and manual cancellation. Screenshots should be occasional verification, not the control loop.

*Relative engineering estimates, not measured token budgets. Native voice has STD/MINI tiers and a session spend guard; these do not cap separate Hermes, HUD or map-provider usage.[1]*

## Closest concrete examples

| Example | What exists / lesson |
|---|---|
| Typed OpenAI/OpenRouter/Ollama agent, PR #51 | Implemented but **unmerged**. Reuses the action runner beside voice; closest precedent for our bridge.[9] |
| Electron + Taiwan CCTV, PR #670 | Implemented but **unmerged**; inspected packaging targets Linux, not proof of Mac readiness. Supports the thin-shell approach.[10] |
| Nepal flood scene, PR #590 | **Merged** multi-shot, source-linked evidence playback. Strong precedent for tours/data packs rather than a rewrite.[7] |
| Local-agent guide, PR #117 | **Documentation-only, unmerged**; uses browser actions, not a shipped HTTP/MCP connector.[11] |

## Agreed near-term order

**Windows CI repair + Mac port → live Mac sidebar acceptance → repository presentation/catalog → actual Windows install recheck.** Evaluate agent control separately after the basic integration is working.

## Sources

[1] https://github.com/bilawalsidhu/gods-eye-view/blob/f01b6a5d8462c182e03c94493fa24098c1ac3771/README.md — Official GEV: platforms, setup and native voice
[2] https://github.com/bilawalsidhu/gods-eye-view/blob/f01b6a5d8462c182e03c94493fa24098c1ac3771/docs/APPLICATION.md — Reusable application and voice components
[3] https://github.com/cygnostik/Hermes-Plugin-Gods-Eye-View/blob/d3879c390e52c930fa3c81f8b0fdbedc6986079c/README.md — Hermes GEV wrapper: requirements and known issues
[4] https://github.com/cygnostik/Hermes-Plugin-Gods-Eye-View/blob/d3879c390e52c930fa3c81f8b0fdbedc6986079c/dashboard/plugin_api.py — Wrapper lifecycle implementation
[5] https://github.com/cygnostik/Hermes-Plugin-Gods-Eye-View/actions/runs/35572094261 — Windows wrapper CI failure
[6] https://github.com/bilawalsidhu/gods-eye-view/blob/f01b6a5d8462c182e03c94493fa24098c1ac3771/docs/DIRECTOR.md — GEV scene playback and reusable Director
[7] https://github.com/bilawalsidhu/gods-eye-view/pull/590 — Merged Nepal flood scene and evidence playback
[9] https://github.com/bilawalsidhu/gods-eye-view/pull/51 — Open PR: typed agent with OpenAI, OpenRouter and Ollama
[10] https://github.com/bilawalsidhu/gods-eye-view/pull/670 — Open PR: Electron shell and Taiwan CCTV
[11] https://github.com/bilawalsidhu/gods-eye-view/pull/117 — Open proposal: local browser-agent automation
[12] https://github.com/bilawalsidhu/gods-eye-view/blob/f01b6a5d8462c182e03c94493fa24098c1ac3771/scripts/qa-voice-routing.mjs — Upstream QA: deterministic actions versus paid model routing
