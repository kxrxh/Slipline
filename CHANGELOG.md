# Changelog

## 0.2.6 — Minimal tyre map

- Replace the overview with four tyre blocks, front/rear pressure placement and no weather panel.
- Show temperature with three coloured tread bands and remaining life with bottom-up fill.
- Read Redux's estimated load bias for contact markers and camber for per-tyre details; hide unavailable or stale readings.
- Add small inner brake-temperature strips when fresh data exists.
- Keep unit controls and numerical readings in the detail view; preserve independent resizing down to 160 × 180.
- Preserve wheel positions when an individual standard wheel reading is missing.
- Keep all Lua, physics, thermals, audio and automatic loading identical to 0.2.5.

## 0.2.5 — Wear on the dashboard

- Show remaining tyre life as a percentage and a thin bar in the overview when wear telemetry is available.
- Hide unavailable or stale wear readings; keep zero life visible.
- Fit the extra reading in compact, medium and large layouts without changing saved app dimensions.
- Retain the 0.2.4 Lua, grip, telemetry and audio unchanged.

## 0.2.4 — Native grip correction

- Remove the experimental slip/history grip multiplier after the 0.2.3 tests found longer braking and harsher Vivace breakaway.
- Stop writing tyre friction on update, reset or unload. BeamNG and thermal mods retain complete control of grip.
- Keep the Redux base-grip bridge read-only, without changing Redux's execution order. An unknown interface only removes that reading.
- Keep automatic loading, tyre audio, the responsive dash and stock wheel construction.

## 0.2.3 — Responsive dashboard pre-release

- Lower the dash minimum from 240 × 280 to 160 × 180.
- Adapt to the app's own dimensions, with a compact layout for small/short apps and scaled medium/large views.
- Allow independent width/height resizing in the UI Apps editor.
- Keep temperature, three tread bands and pressure visible at small sizes; keep units in the header.
- Fix the back arrow returning from tyre details.
- Retain grip, audio, telemetry and wheel construction unchanged.

## 0.2.2 — Slipline initial public pre-release

- Publish the project as Slipline, retaining existing runtime identifiers.
- Minimal tyre-plan racing dash with tread temperature bands and live pressure.
- Per-tyre details, temperature/pressure unit switches and missing/stale/flat states.
- Keep the 0.2.1 grip and audio implementation unchanged.
- Add reproducible release packaging and public compatibility notes.

## 0.2.1 — Development build

- Automatic native tyre-audio gain driven by measured slip.
- Sideways-slip telemetry and clearer thermal/wear explanations.

## 0.2.0 — Development build

- Live pressure/grip telemetry and the original monitor UI.
- Restore stock wheel construction; remove unsafe wheel-density expansion.

## 0.1.1 — Development hotfix

- Disable density expansion following tyre/wheel failures.

## 0.1.0 — Withdrawn prototype

- Initial automatic grip/density experiment. **Do not install this build.**
