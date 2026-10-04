# 0.3.0 audio validation

BeamNG.drive 0.39.4.0, build 20972; visible DX11 windows with isolated profiles on Small Grid. No headless runs. Compared native audio, the 0.2.6 shared-coefficient boost and the 0.3.0 candidate, both without Redux and with the supplied Redux 0.20 archive. Four stock configurations drove 33 seconds of simulation per run: stationary, straight acceleration, gentle cornering, hard cornering, powered sliding and braking. The cars were separated so other cars did not enter the recording. Game-only process audio and window captures were retained locally.

| Configuration | Compound / size | Hard-corner front event input → output, no Redux |
|---|---|---|
| BX track | Race 245/35R17 | 0.0128 → 0.0584 |
| BX GTz | Sport 195/60R15 | 0.0248 → 0.0843 |
| ETK I-Series drift | Drift 225/40R17 | 0.0416 → 0.1466 |
| Vivace trackday | Race 245/35R19 | 0.0172 → 0.0883 |

These are normalized sound-event control values captured inside the candidate, not sound pressure or perceived loudness. Native events already above the enhancement ceiling remain intact. Gentle-corner skid events remained silent on the BX and Vivace; the ETK drift car had a small native cue. All candidate frames retained a readable bridge and owned skid hooks. Stationary readings below 0.2 m/s after the initial second had identical native input/output. The shared tyre sound coefficient remained 1.0 throughout; rolling-event methods are not wrapped.

Completed **24 vehicle runs, 15,840 graphics samples and 63,360 wheel samples**, with zero tyre-deflation or broken-wheel readings. Redux loaded on all four cars, and its read-only grip bridge initialized after the first sample. Slipline's grip factors remained 1.0; audio did not replace Redux's thermal or wear model. Automatic loading was checked before manual A/B mode switching in the Redux session. All four owned skid methods restored on unload in both sessions.

LuaJIT fixtures separately passed progressive response, native pitch/colour/texture preservation, loud native events, locked-wheel scrub, airborne/flat/broken/muted/loose/submerged/stationary gating, reset, unload, method ownership, wheel replacement and unavailable-interface fallback. The native-grip fixture forbids physics writes and extension-order changes. All release Lua and loader files except the audio extension are byte-identical to 0.2.6.

The first trial had a harness reload-path error and is excluded: the candidate was unloaded and never reloaded. Corrected trials explicitly use the auto-extension file path. The final Redux trial uses the release audio source; the corrected no-Redux trial differs only by an unused diagnostic field removed afterward.

The recorder samples the preceding sound update, so phase edges can lag one graphics frame. Simulation time and recording wall time differ; do not compare raw clip durations as handling evidence. Short asphalt tests do not validate every surface, long sessions, multiplayer, subjective usefulness or physical grip realism. This release improves skid cues, not the tyre force curve. The sound bridge depends on the 0.39 internal interface and falls back to native audio when unavailable.

Aggregate results: [audio-validation-0.3.0.json](audio-validation-0.3.0.json). Original reproduction driver and visible runner are in `tests/`; no BeamNG or Redux source is bundled.
