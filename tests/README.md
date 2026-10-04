# Lua lifecycle checks

Install `lupa==2.6`, then run `python tests/test_native_grip.py` and `python tests/test_tyre_feedback.py` from the source checkout. This uses LuaJIT and original mock fixtures; it does not require BeamNG files.

Physics-object access or an extension-order change fails the fixture. It checks native and Redux readings, a replaced Redux grip table, an unknown Redux interface, removal, reset, unload and diagnostic snapshot isolation. These checks establish read-only behaviour; visible driving tests provide separate handling evidence.

The audio fixture checks progressive sideways-slip cues, unchanged native parameters and rolling audio, muted/flat/broken/airborne/stationary/loose-surface/submerged tyres, locked-wheel scrub, reset, unload, replacement, ownership and missing-interface fallback. It verifies event volumes, not perceived loudness or the real tyre force curve.

## Visible audio comparison

Install `beamngpy==1.35.1`. Run `python tests/run_visible_audio.py --game <BeamNG-install> --output <new-test-folder>`; optionally add `--redux <Redux-zip>`. It launches a visible DX11 window with an isolated profile, drives four stock configurations on Small Grid and compares native audio, the previous Slipline coefficient boost from commit `d0d430e`, and the candidate. It quits only the process it launched. Keep the full Git history for the legacy comparison. Do not point the output at your normal user folder. Optional `--um <Universal-Modder-package>` records only the game process/window with that plugin's recorder.

Samples include native skid/rolling event levels, wheel state, parts and candidate diagnostics. Audio readings come from the preceding native sound update, so changes at phase boundaries can lag one graphics frame. Simulation time is not necessarily recording wall time. Results are cue-volume evidence, not calibrated loudness, subjective feedback or a tyre-force validation. See `docs/audio-validation-0.3.0.md`.
