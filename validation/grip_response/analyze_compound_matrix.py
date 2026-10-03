from pathlib import Path
import json,statistics as st,csv,sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import analyze_grip_ab as base

# Same calculations and qualification rules as the first study; only file paths differ.
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--results',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--manifest',type=Path)
args=parser.parse_args()
source=(Path(__file__).resolve().parent/'analyze_grip_ab.py').read_text()
source=source.replace("OUT=ROOT/'analysis'","OUT=Path("+repr(str(args.out.resolve()))+")")
source=source.replace("RESULTS=ROOT/'results'","RESULTS=Path("+repr(str(args.results.resolve()))+")")
source=source.replace("path=RESULTS/(condition+'.json')","path=RESULTS/('matrix_'+condition+'.json')")
namespace={'__name__':'matrix_analysis'};exec(compile(source,'matrix_analysis','exec'),namespace)
summary,rows,datasets=namespace['main']()
OUT=namespace['OUT'];ROOT=namespace['ROOT']
if args.manifest:
    manifest=json.loads(args.manifest.read_text())
else:
    manifest=[];seen=set()
    for run in datasets['stock']['runs']:
        if run['car'] not in seen:
            seen.add(run['car']);manifest.append({k:run[k] for k in ['car','family','compound','tyreParts']})
if summary['runs']!=168:print('Partial matrix:',summary['runs']);sys.exit(0)
checks={'runs':168,'tyre_failures':summary['safety']['failed_tyre_samples'],'matched_active_parts':True,'expected_tyres_loaded':True,'cold_setpoint_psi':28,
  'wheel_ray_counts':sorted({w['rays'] for d in datasets.values() for r in d['runs'] for s in r['samples'] for w in s['tyres']}),
  'factor_violations':sum(not .92<=w['factor']<=1 for d in datasets.values() for r in d['runs'] for s in r['samples'] for w in s['tyres']),
  'max_paired_entry_speed_difference_kmh':max(p['max_entry_speed_difference_kmh'] for p in summary['paired'])}
checks['vehicle_samples']=sum(len(r['samples']) for d in datasets.values() for r in d['runs'])
checks['wheel_samples']=sum(len(s['tyres']) for d in datasets.values() for r in d['runs'] for s in r['samples'])
for r in datasets['slipline']['runs']:
    ref=next(a for a in datasets['stock']['runs'] if (a['car'],a['maneuver'],a['repeat'])==(r['car'],r['maneuver'],r['repeat']))
    checks['matched_active_parts'] &= r['metadata']['parts']==ref['metadata']['parts']
for d in datasets.values():
    for r in d['runs']:checks['expected_tyres_loaded'] &= set(r['tyreParts'].values())<=set(r['metadata']['parts'].values())
(OUT/'audit.json').write_text(json.dumps(checks,indent=2))
order=[c['car'] for c in manifest]
fig,axes=plt.subplots(1,3,figsize=(14,5),layout='constrained')
for ax,maneuver,title,unit in zip(axes,['brake','corner','steering'],['Braking change','Steady corner response change','Sudden steering peak change'],['% longer stopping path','% lateral acceleration','% peak yaw rate']):
    items=[next(p for p in summary['paired'] if p['car']==car and p['maneuver']==maneuver) for car in order]
    ys=list(range(7));values=[p['delta_percent'] for p in items]
    ax.barh(ys,values,color='#177eaa',alpha=.8);ax.axvline(0,color='#666',lw=1);ax.set_yticks(ys,[c['family'].replace('_',' ')+' / '+c['compound'] for c in manifest]);ax.invert_yaxis();ax.set_title(title);ax.set_xlabel(unit);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    for y,p in zip(ys,items):
        scale=100/p['baseline_mean'];ax.plot([p['delta_min']*scale,p['delta_max']*scale],[y,y],color='#333',lw=2)
fig.suptitle('Matched tyre-size compound comparison вЂ” stock vs Slipline 0.2.3\nThree repeats; black segments show repeat-wise change ranges, not confidence intervals')
fig.savefig(OUT/'compound_comparison.png',dpi=160);plt.close(fig)
table=['| Car / compound | Tyres F / R | Stop m: stock в†’ Slipline | Change | Corner change | Peak yaw change |','| --- | --- | --- | --- | --- | --- |']
for c in manifest:
    pp={m:next(p for p in summary['paired'] if p['car']==c['car'] and p['maneuver']==m) for m in ['brake','corner','steering']}
    p=pp['brake'];sizes=[]
    for v in c['tyreParts'].values():
        width,aspect,diameter=v.removeprefix('tire_F_').removeprefix('tire_R_').removesuffix('_'+c['compound']).split('_')
        sizes.append(f'{width}/{aspect}R{diameter}')
    table.append(f"| {c['family']} / {c['compound']} | {' / '.join(sizes)} | {p['baseline_mean']:.2f} в†’ {p['modified_mean']:.2f} | {p['delta_percent']:+.2f}% | {pp['corner']['delta_percent']:+.2f}% | {pp['steering']['delta_percent']:+.2f}% |")
brakes=[p for p in summary['paired'] if p['maneuver']=='brake']
interpretation=f"Mean stopping paths change by {min(p['delta_percent'] for p in brakes):+.2f}вЂ“{max(p['delta_percent'] for p in brakes):+.2f}% across the seven matched-size cases. The repeat-wise distance range and entry-speed-normalized estimate are retained in `summary.json`; small differences should be read against that variation and the 50 ms sampling. No real tyre reference data was used, so a longer stop is a measured performance cost, not proof that either condition is more physically accurate."
qualifications=['| Setup | Qualified corner / 6 | Steering / 6 | Braking / 6 | Slide provocation / 6 |','| --- | --- | --- | --- | --- |']
for c in manifest:
    qualifications.append('| '+c['car']+' | '+' | '.join(str(sum(r['valid'] for r in rows if r['car']==c['car'] and r['maneuver']==m)) for m in ['corner','steering','brake','drift'])+' |')
text='''# Additional cars and compounds

168 visible runs: seven native tyre configurations Г— four manoeuvres Г— two conditions Г— three repeats. Stock is compared against Slipline 0.2.3; Redux is excluded from this additional matrix. All runs use the same driving rules, fixed 50 ms updates and per-run scenario resets as the first study.

Covet race (FWD) uses 195/60R15 standard and sport tyres. ETK 800 844 track (RWD) uses 245/35R17 sport, race and drift tyres. SBR4 S AWD uses 225/40R18 front and 295/30R18 rear sport and race tyres. Within each family, wheel parts, nominal tyre sizes, suspension, drivetrain and all other configuration choices match; front/rear cold setpoints are explicitly 28 PSI. These are controlled test setups based on factory configurations, not unchanged factory presets. Live gauge pressure still varies with load and tyre state.

Factory parts do not offer all compounds in every size. No tyre geometry was cloned or altered to manufacture missing compounds. Factory configuration names and selected tyres are retained in the data; runtime-generated configuration files are not redistributed.

The game window closed during the final Slipline batch. The preceding 161 completed runs were retained, and only the seven unrecorded final runs were repeated in a fresh visible process with the same reset/setup protocol. No partial interrupted trajectory is scored. The raw dataset records this resumption.

'''+ '\n'.join(table)+'\n\n'+interpretation+'\n\n'+ '\n'.join(qualifications)+f'''

![Measured compound comparison](compound_comparison.png)

Tyre failure observations: {checks['tyre_failures']}. Stock/Slipline active-part configurations match: {checks['matched_active_parts']}; selected tyre parts were verified on every recorded run: {checks['expected_tyres_loaded']}. Ray counts: {checks['wheel_ray_counts']}; multiplier-bound violations: {checks['factor_violations']}. Largest paired entry-speed difference: {checks['max_paired_entry_speed_difference_kmh']:.3f} km/h.

Black plot segments are the three repeat-wise difference ranges, not confidence intervals. Corner acceleration is the response to the prescribed steering, not peak available grip. Changes in peak yaw do not constitute a handling quality score. The fourth manoeuvre is the original aggressive slide provocation; it is retained in the CSV with qualification flags and must not be interpreted as sustained controlled drifting. The separate RWD feedback-driver follow-up addresses that limitation.

Per-run data and qualifications: `run_metrics.csv`. Paired means, standard deviations and secondary measurements: `summary.json`. Integrity checks: `audit.json`. All raw data belongs to this bounded dry, flat Smallgrid test; it does not cover every car, surface, speed, mod or human driver.
'''
(OUT/'Compound-validation.md').write_text(text,encoding='utf-8')
print(checks)
