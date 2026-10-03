# Grip-response comparison

Original test-only driver and telemetry recorder for the Slipline 0.2.3 study. They are not included in the mod ZIP and do not write tyre friction, pressure or thermal state. The comparison report is in `docs/validation/0.2.3/Grip-response-validation.md`.

Requires Windows, BeamNG.drive 0.39.4, Python 3.12 and `beamngpy==1.35.1`. Supply Slipline and Redux ZIPs separately; no game files or Redux code are redistributed here. The known Redux interface is version 0.20.

Use a separate test workspace. The runner creates four isolated user profiles and opens a **visible Direct3D11 game window** for each condition. It does not offer a headless option. Optional online features and telemetry are declined in these test profiles to keep the first-run consent screen out of the driving view. Avoid manually driving the test cars during measurement. It quits only the game process it started.

```powershell
python -m pip install -r requirements.txt
python run_grip_ab.py --condition stock --suite --game-home "D:/Games/BeamNG.drive" --workspace "D:/SliplineTests" --slipline-zip "D:/Mods/slipline_beamng_039_v0.2.3.zip" --redux-zip "D:/Mods/tyre-thermals-and-wear.zip"
```

Four factory configurations, four manoeuvres, three repeats per condition; fixed 50 ms recorded updates. Full raw JSON is written after each batch in the workspace `results` directory. Inspect `owned_process.json` for the owned PID if interrupted; do not terminate unrelated game instances.

To summarize the JSON, run the analyzer with the test workspace as the current directory:

```powershell
cd D:/SliplineTests
python D:/Source/Slipline/validation/grip_response/analyze_grip_ab.py
```

The analyzer writes CSV and paired summaries to `analysis`. Qualifying an input run is not a realism score. In particular, `drift` is an aggressive slide provocation: the reported RWD runs spin, and sustained controlled drifting is not validated by that manoeuvre. Fixed timing is repeatable within a setup, not guaranteed complete determinism. The report retains all repeats and discloses these limits.


## Follow-up protocols

The [controlled RWD follow-up](../../docs/validation/0.2.3/Controlled-drift-followup.md) uses a stock-pilot-selected, frozen feedback driver on BX and ETK I-Series. Run `run_controlled_drift.py --condition stock --pair` with the same `--game-home`, `--workspace` and `--slipline-zip` options. Use a fresh dedicated workspace for each protocol. Analyze using `analyze_controlled_drift.py --results PATH/results --out PATH/analysis`.

The [compound matrix](../../docs/validation/0.2.3/compound_matrix/Compound-validation.md) adds Covet, ETK 800 and SBR4. First run `prepare_compound_matrix.py --game-home INSTALLATION --workspace TEST_DIRECTORY`; it reads native configs locally and generates seven matched-size tyre setups in the test workspace. Then run `run_compound_matrix.py --condition stock --pair` with the same installation/workspace and Slipline ZIP options. Analyze using `analyze_compound_matrix.py --results PATH/results --out PATH/analysis --manifest PATH/compound_matrix_manifest.json`. Native configuration files and the generated manifest are not distributed. Each recorded run verifies the selected tyres actually loaded. Pressure setpoints are 28 PSI front/rear.

The raw bundle contains eight scored JSON files: four original conditions, two controlled-drift conditions, and two compound-matrix conditions. Pilots are excluded. All failures and failed qualifications are retained. The matrix's `drift` manoeuvre remains an aggressive provocation; only the separate feedback-driver protocol tests sustained sliding.


## Handling transitions

[Slip angle, trail braking and lift/reversal](../../docs/validation/0.2.3/handling/Handling-response-validation.md) use four factory cars, six manoeuvres, three repeats and stock/Slipline conditions (144 scored runs). Run `run_handling_tests.py --condition stock --pair` with the same installation/workspace/release ZIP options. This uses 50 Hz fixed controller updates, explicitly verifies 20 ms recorded steps, and records geometric hub slip angles. `--pilot --condition stock --repeats 1` checks the steering sweep, hard trail braking, lift and rapid reversal separately; pilot data is not scored. Analyze with `analyze_handling_tests.py --results PATH/results --out PATH/analysis`. The raw bundle adds `handling_stock.json` and `handling_slipline.json`, giving ten scored JSON files overall. No pilot files are included.
