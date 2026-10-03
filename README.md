# Slipline

Automatic tyre grip response, clearer tyre audio and a compact racing dash for **BeamNG.drive 0.39.x**.

**Version 0.2.2 is experimental.** Tested with BeamNG.drive 0.39.4.0 (build 20972). It is a bounded handling modifier, not a validated replacement for the native tyre physics model.

![Tyre Dash with sample readings](docs/images/tyre-dash.png)

*Preview uses sample telemetry; this is not an in-game screenshot.*

## Features

- Automatic per-wheel grip response driven by slip and short relaxation history. No tuning part or activation required.
- Native tyre audio grows with measured slip, helping make sliding more audible.
- **Tyre Dash:** four tyre silhouettes, three temperature bands per tyre and live pressure. Tap a tyre for more readings; switch between °C/°F and PSI/kPa.
- Optional integration with [Tyre Wear and Thermals Redux](https://www.beamng.com/resources/tyre-wear-and-thermals-redux.29934/). Redux supplies temperature, wear and base grip; Slipline applies its response afterwards.

Wheel construction stays stock. Slipline does not increase polygon or physics-node counts. The early Automatic Tyres prototype's density increase was withdrawn after tyre failures.

## Install

1. Download `slipline_beamng_039_v0.2.2.zip` from [Releases](https://github.com/kxrxh/Slipline/releases).
2. Open BeamNG's current user folder through its launcher. Place the ZIP in `mods` and keep it zipped.
3. Remove or disable previous Slipline / Automatic Tyres ZIPs, and disable GGT before using Slipline. Keep only one copy enabled.
4. Fully restart BeamNG and spawn a fresh vehicle. The grip and audio extensions load automatically.
5. To display readings, add **Tyre Dash** through the game's UI Apps editor. The dash is optional; its placement is a one-time UI choice.

GitHub's **Source code** archives are for development. Install the release ZIP listed above.

Without Redux, the dash still shows live pressure and Slipline runs its grip response. Temperature and remaining tyre life require Redux; unavailable readings appear as dashes.

To uninstall, remove the ZIP, restart BeamNG and respawn the vehicle. Remove Tyre Dash from your UI layout if desired. No base-game files are changed.

## Readings and behaviour

The main temperature is the average tread temperature. The detail view adds the three tread zones, core temperature, pressure, cold setpoint, remaining life, brake temperature and measured sideways slip. Pressure is live gauge pressure, not the configured cold pressure.

Temperature colours use Redux's **wear temperature target** as their reference; that target is not necessarily the temperature of maximum grip. Redux owns heat, wear, brake heat transfer and its wear-related punctures. Slipline does not run a second thermal or wear simulation, although changed handling can indirectly change slip and heating.

The transient grip multiplier stays between **0.92 and 1.00**, with a stationary baseline of **0.98**. Native contact, pressure and load sensitivity remain in use. Tyre sound gain is capped at **1.8×** its existing coefficient and returns to baseline at rest, when unloaded or deflated. The shared native coefficient can also raise rolling and scrub sounds; intentionally muted tyres remain muted.

## Compatibility and troubleshooting

- Known Redux bridge tested with **Redux 0.20**. It reads an internal computed-grip table, so future Redux changes may require an update. If that interface cannot be read, Slipline pauses its grip refinement to retain Redux behaviour.
- Other mods that write tyre friction or tyre audio coefficients can conflict. GGT should be disabled; a detected active GGT updater pauses Slipline's grip refinement.
- Multiplayer, every vehicle/mod combination and long high-speed sessions have not been validated.
- If readings are missing, check that Redux is enabled for temperature/life, then restart the game and respawn. Stale data dims and displays `NO DATA`.
- If updating from the withdrawn density prototype, a **full game restart** is necessary; existing cars can retain previously generated wheels.
- For bug reports, include game/mod versions, vehicle/configuration, tyre compound/size, reproduction steps and relevant lines from `beamng.log` in the current user folder. Review logs for personal information before sharing.

## Validation

In isolated BeamNG 0.39.4 sessions, native ETK I-Series drift 225/40R17 and sport 225/45R16 tyres passed spawn, acceleration, wheelspin/cornering and braking without deflated, punctured or broken wheels. Stock construction was retained. Additional BX and ETK checks verified intact tyres, live pressure/slip telemetry, bounded native sound parameters and restoration on unload. A neutral stationary check confirmed actual vehicle velocity before assessing idle behaviour.

Grip checks covered 10,000 varied inputs; feedback checks covered stationary, unloaded, deflated and intentionally muted tyres. Browser UI checks covered missing/stale data, flats, extra wheels, detail views, units and resizing. The preview is sample data; final in-game UI placement and subjective sound/handling remain user validation work. These checks do not establish a real-world calibrated tyre model.

## Build from source

Requires Python 3.9+; packaging uses only its standard library.

```sh
python tools/build.py --output dist
```

This creates the installable ZIP and `SHA256SUMS.txt`. Only the allowlisted game-facing directories and documentation are packaged. Internal `automaticTyres` module/app identifiers are retained for compatibility with existing installations and layouts.

Optional source tests use LuaJIT through Lupa:

```sh
python -m pip install -r requirements-dev.txt
python tests/test_runtime.py
```

## Credits and license

Original Lua, JavaScript, CSS, HTML and dash icon were developed with **OpenAI Codex (GPT-6)** at the project owner's direction. The preview renders that UI with sample data. No generated audio is included.

Reference concepts: GGT by LiXennn, High Poly Wheels by fillman86, Tyre Wear and Thermals Redux by Zesty_Maple98, and BeamNG pressure-wheel documentation. No game files, third-party mod source, textures or audio are distributed. This project is independent and is not endorsed by BeamNG or those authors.

Original code and icon: [MIT license](LICENSE.txt).
