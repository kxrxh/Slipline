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

Wheel construction stays stock. Slipline does not increase polygon or physics-node counts.

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
