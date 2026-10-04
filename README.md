# Slipline

Clearer tyre audio and a compact racing dash for **BeamNG.drive 0.39.x**, with native tyre grip preserved.

**Version 0.3.0 adds progressive skid audio and preserves native grip.** The grip modifier was removed in 0.2.4 after the 0.2.3 comparison found longer braking and sharper breakaway in one stress test. Tested with BeamNG.drive 0.39.4.0 (build 20972). Slipline does not replace the native tyre physics model.

![Tyre Dash with sample readings](docs/images/tyre-dash.png)

*Preview uses sample telemetry; this is not an in-game screenshot.*

## Features

- Loads automatically, with no tuning part or activation required. Tyre grip remains under BeamNG or your thermal mod's control.
- Existing spatial tyre skid sounds build smoothly with measured sideways slip. Native rolling and loose-surface audio stay unchanged.
- **Tyre Dash:** four tyre blocks with temperature colours, live pressure, wear fill, small brake-temperature strips and estimated contact markers when available. Tap a tyre for detailed readings and °C/°F or PSI/kPa controls.
- Optional integration with [Tyre Wear and Thermals Redux](https://www.beamng.com/resources/tyre-wear-and-thermals-redux.29934/). Redux supplies temperature, wear and grip; Slipline reads telemetry without applying another grip multiplier.

Wheel construction stays stock. Slipline does not increase polygon or physics-node counts.

## Resizing the dash

Drag the app resize handle in BeamNG's UI Apps editor. Suggested sizes: **small 160 × 180**, **medium 300 × 360**, **large 440 × 500**. Four tyres keep a two-column layout at every size. Width and height are independent; the graphics scale to fit both. Extra axles and small detail views scroll vertically.

## Readings and behaviour

Pressure sits above the front tyres and below the rear tyres. It is live gauge pressure, not the configured cold pressure. The overview uses colour for the three tread temperatures and small inner strips for brake temperature. Tap a tyre for numerical tread/core temperatures, pressure, cold setpoint, life, camber, estimated contact side, brake temperature and measured sideways slip. Unit controls are in that detail view.

Tyre blocks fill from the bottom with remaining life: **100% means new; 0% means exhausted.** The three bands share one life reading; this is not separate shoulder wear. Missing or stale wear uses a hatched temperature graphic, without assuming the tyre is new. The exact percentage is in the detail view. Redux supplies wear readings.

The white triangle shows Redux's **estimated load bias** across the displayed tread. Positive bias moves right; negative bias moves left, following Redux's left/centre/right temperature-ring weighting. On the left wheels, right is inner; on the right wheels, left is inner. The marker is an estimate based on camber and lateral acceleration, not a measured contact patch. Missing or stale bias hides the marker; unavailable camber and wear details are also hidden.

Tread colours run from cool teal through green and yellow to hot orange/red, using Redux's **wear temperature target** as their reference; that target is not necessarily the temperature of maximum grip. Brake strips use Redux's brake reference temperature, or 800°C if that field is absent; they are a heat cue, not a calibrated brake-performance meter. Redux owns heat, wear, brake heat transfer and its wear-related punctures. Slipline does not run a second thermal or wear simulation.

Slipline's grip factor is **1.00**. It does not write friction coefficients, alter Redux's update order or change wheel construction. The optional base-grip reading uses Redux's latest available computed value and can lag its update by one frame. Skid audio adds a sideways-slip cue to the game's existing rigid skid events on asphalt, rumble strips and cobblestone, with a smaller cue on wet asphalt. The multiplicative gain is capped at 1.5×, while the added event-volume floor is capped at 0.18; already louder native sounds remain intact. The cue ramps in and fades out, with no enhancement at rest, when unloaded, deflated, submerged or intentionally muted. Native rolling, loose-surface and kick-up sounds, pitch and tyre parameters stay unchanged. This is an audio cue derived from sideways slip and road speed, not a measured limit of grip or a separate understeer detector.

## Compatibility and troubleshooting

- Known Redux bridge tested with **Redux 0.20**. It reads an internal computed-grip table, so future Redux changes may remove that reading. Redux continues to control tyre physics if the interface cannot be read.
- The audio bridge reads the internal 0.39 skid-sound objects. An unknown interface retains native audio. Other mods that replace skid sound methods can conflict; Slipline restores only methods it still owns. GGT and other grip mods can still change handling independently of Slipline; disable them when comparing with stock.
- Multiplayer, every vehicle/mod combination and long high-speed sessions have not been validated.
- If readings are missing, check that Redux is enabled for temperature/life, then restart the game and respawn. Stale data dims and displays `NO DATA`.
- If updating from the withdrawn density prototype, a **full game restart** is necessary; existing cars can retain previously generated wheels.
- When updating from 0.2.3 or earlier, fully restart the game to discard the old runtime grip modifier.
- For bug reports, include game/mod versions, vehicle/configuration, tyre compound/size, reproduction steps and relevant lines from `beamng.log` in the current user folder. Review logs for personal information before sharing.
