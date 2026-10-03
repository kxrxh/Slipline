from pathlib import Path
import json,csv,math,statistics as st,sys,argparse,datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
parser=argparse.ArgumentParser()
parser.add_argument('--pilot',action='store_true')
parser.add_argument('--results',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
RESULTS=args.results.resolve();OUT=args.out.resolve();OUT.mkdir(parents=True,exist_ok=True)
datasets={}
for c in ['stock','slipline']:
    path=RESULTS/('handling_'+c+('_pilot' if args.pilot else '')+'.json')
    if path.exists():datasets[c]=json.loads(path.read_text())

def mean(a):
    a=list(a);return st.mean(a) if a else None
def axle(s,front=True):
    vals=[w['alpha'] for w in s['tyres'] if w['name'] in (['FL','FR'] if front else ['RL','RR']) and w.get('alpha') is not None]
    return mean(vals)
def deltaangle(a,b):return (a-b+180)%360-180
def angle_trace(samples,getter):
    out=[];previous=None
    for s in samples:
        value=getter(s)
        out.append(value if s['speed']>5 and (previous is None or abs(value-previous)<180) else math.nan)
        previous=value
    return out
def smoothrate(samples,key,angle=False):
    out=[]
    for i,s in enumerate(samples):
        if i<5:continue
        old=samples[i-5];dt=s['t']-old['t']
        if dt>0:out.append(abs(deltaangle(s[key],old[key]) if angle else s[key]-old[key])/dt)
    return out
def summarize(c,r):
    assert r['protocol']=='handling_v3', 'Unexpected scored driver protocol'
    assert abs(r['clock']['dtMin']-.02)<1e-6 and abs(r['clock']['dtMax']-.02)<1e-6
    ss=r['samples'];man=r['maneuver']
    entry=min(ss,key=lambda s:abs(s['t']-18)) if man!='sweep' else min(ss,key=lambda s:abs(s['t']-12))
    event=[s for s in ss if (12<=s['t']<=30 if man=='sweep' else 18<=s['t']<=21) and s['speed']>5]
    post_event=[s for s in ss if s['t']>=(12 if man=='sweep' else 18) and s['speed']>5]
    rear=[abs(axle(s,False)) for s in event if axle(s,False) is not None]
    front=[abs(axle(s)) for s in event if axle(s) is not None]
    recovery=[s for s in ss if s['t']>=24 and s['speed']>5]
    onset10=next((s['t'] for s in post_event if abs(s['beta'])>=10),None)
    onset30=next((s['t'] for s in post_event if abs(s['beta'])>=30),None)
    row={'condition':c,'car':r['car'],'repeat':r['repeat'],'maneuver':man,'entry_kmh':entry['speed']*3.6,
      'entry_beta_deg':entry['beta'],'entry_yaw_deg_s':entry['yawRate']*180/math.pi,
      'peak_beta_deg':max(abs(s['beta']) for s in event),'peak_beta_rate_deg_s':max(smoothrate(event,'beta',True),default=0),
      'peak_yaw_accel_deg_s2':max(smoothrate(event,'yawRate'),default=0)*180/math.pi,
      'peak_front_alpha_deg':max(front,default=0),'peak_rear_alpha_deg':max(rear,default=0),
      'time_over_10_deg_s':sum(s['dt'] for s in event if abs(s['beta'])>10),
      'time_over_30_deg_s':sum(s['dt'] for s in event if abs(s['beta'])>30),
      'time_over_60_deg_s':sum(s['dt'] for s in event if abs(s['beta'])>60),
      'post_event_peak_beta_deg':max(abs(s['beta']) for s in post_event),
      'post_event_spin_time_s':sum(s['dt'] for s in post_event if abs(s['beta'])>60),
      'time_to_10_deg_s':onset10-(12 if man=='sweep' else 18) if onset10 is not None else None,
      'time_to_30_deg_s':onset30-(12 if man=='sweep' else 18) if onset30 is not None else None,
      'transition_10_to_30_s':onset30-onset10 if onset30 is not None and onset10 is not None else None,
      'recovery_beta_rms_deg':math.sqrt(mean(s['beta']**2 for s in recovery)) if recovery else None,
      'recovery_speed_kmh':mean(s['speed']*3.6 for s in recovery),'minimum_event_kmh':min(s['speed']*3.6 for s in event),
      'mean_event_kmh':mean(s['speed']*3.6 for s in event),
      'peak_event_g':max(abs(s['ay'])/9.81 for s in event),
      'front_rear_slip_gap_deg':max(abs(axle(s,False))-abs(axle(s)) for s in event if axle(s,False) is not None and axle(s) is not None),
      'tyre_failure_samples':sum(w['flat'] or w['broken'] or w['punctured'] for s in ss for w in s['tyres']),
      'sample_dt_min':r['clock']['dtMin'],'sample_dt_max':r['clock']['dtMax']}
    row['qualified_entry']=abs(row['entry_kmh']-72)<3 and (man=='sweep' or abs(row['entry_beta_deg'])<10)
    row['wheel_geometry_available']=all(w.get('alpha') is not None for s in event for w in s['tyres'])
    return row
rows=[summarize(c,r) for c,d in datasets.items() for r in d['runs']]
fields=list(rows[0])
with (OUT/('pilot_metrics.csv' if args.pilot else 'run_metrics.csv')).open('w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
paired=[]
for car in sorted(set(r['car'] for r in rows)):
    for man in ['sweep','hold','trail_mild','trail_hard','lift','lift_reversal']:
        a=sorted([r for r in rows if r['condition']=='stock' and r['car']==car and r['maneuver']==man],key=lambda r:r['repeat'])
        b=sorted([r for r in rows if r['condition']=='slipline' and r['car']==car and r['maneuver']==man],key=lambda r:r['repeat'])
        if len(a)!=3 or len(b)!=3:continue
        p={'car':car,'maneuver':man,'all_entries_qualified':all(r['qualified_entry'] for r in a+b),
          'max_paired_entry_kmh_difference':max(abs(y['entry_kmh']-x['entry_kmh']) for x,y in zip(a,b)),
          'max_paired_entry_beta_difference':max(abs(y['entry_beta_deg']-x['entry_beta_deg']) for x,y in zip(a,b)),
          'runs_over_10_deg':{'stock':sum(r['time_to_10_deg_s'] is not None for r in a),'slipline':sum(r['time_to_10_deg_s'] is not None for r in b)},
          'runs_over_30_deg':{'stock':sum(r['time_to_30_deg_s'] is not None for r in a),'slipline':sum(r['time_to_30_deg_s'] is not None for r in b)},
          'spin_runs':{'stock':sum(r['post_event_spin_time_s']>0 for r in a),'slipline':sum(r['post_event_spin_time_s']>0 for r in b)},
          'metrics':{}}
        for key in ['peak_beta_deg','peak_beta_rate_deg_s','peak_yaw_accel_deg_s2','peak_front_alpha_deg','peak_rear_alpha_deg','front_rear_slip_gap_deg','time_over_10_deg_s','time_over_30_deg_s','time_over_60_deg_s','post_event_peak_beta_deg','post_event_spin_time_s','time_to_10_deg_s','time_to_30_deg_s','transition_10_to_30_s','mean_event_kmh','recovery_beta_rms_deg','recovery_speed_kmh','peak_event_g']:
            av=[r[key] for r in a];bv=[r[key] for r in b]
            if any(x is None for x in av+bv):continue
            ds=[y-x for x,y in zip(av,bv)]
            p['metrics'][key]={'stock':mean(av),'slipline':mean(bv),'stock_sd':st.stdev(av),'slipline_sd':st.stdev(bv),'delta':mean(ds),'delta_min':min(ds),'delta_max':max(ds)}
        paired.append(p)
summary={'runs':len(rows),'tyre_failure_samples':sum(r['tyre_failure_samples'] for r in rows),'spin_runs':sum(r['post_event_spin_time_s']>0 for r in rows),'unqualified_entries':[r for r in rows if not r['qualified_entry']],
         'all_wheel_geometry_available':all(r['wheel_geometry_available'] for r in rows),'paired':paired}
(OUT/('pilot_summary.json' if args.pilot else 'summary.json')).write_text(json.dumps(summary,indent=2))
print('Runs',len(rows),'failures',summary['tyre_failure_samples'],'geometry',summary['all_wheel_geometry_available'])
for r in rows:print(r['condition'],r['car'],r['maneuver'],r['repeat'],'entry',round(r['entry_kmh'],2),'beta',round(r['peak_beta_deg'],2),'betaRate',round(r['peak_beta_rate_deg_s'],2),'front/rear',round(r['peak_front_alpha_deg'],2),round(r['peak_rear_alpha_deg'],2),'qualified',r['qualified_entry'])
if args.pilot or len(rows)!=144:sys.exit(0)
assert len({(r['condition'],r['car'],r['repeat'],r['maneuver']) for r in rows})==144
wheel_samples=[w for d in datasets.values() for r in d['runs'] for s in r['samples'] for w in s['tyres']]
audit={'runs':144,'vehicle_samples':sum(len(r['samples']) for d in datasets.values() for r in d['runs']),
       'wheel_samples':len(wheel_samples),'tyre_failure_samples':summary['tyre_failure_samples'],
       'sample_dt_min':min(r['sample_dt_min'] for r in rows),'sample_dt_max':max(r['sample_dt_max'] for r in rows),
       'ray_counts':sorted(set(w['rays'] for w in wheel_samples)),'factor_violations':sum(not .92<=w['factor']<=1 for w in wheel_samples),
       'all_wheel_geometry_available':summary['all_wheel_geometry_available'],
       'matched_active_parts':all(r['metadata']['parts']==next(x for x in datasets['stock']['runs'] if (x['car'],x['maneuver'],x['repeat'])==(r['car'],r['maneuver'],r['repeat']))['metadata']['parts'] for r in datasets['slipline']['runs']),
       'max_paired_entry_speed_difference_kmh':max(p['max_paired_entry_kmh_difference'] for p in paired),
       'max_paired_entry_beta_difference_deg':max(p['max_paired_entry_beta_difference'] for p in paired),
       'esc_active_samples':sum(bool(s.get('escActive')) for d in datasets.values() for r in d['runs'] for s in r['samples']),
       'tc_active_samples':sum(bool(s.get('tcActive')) for d in datasets.values() for r in d['runs'] for s in r['samples'])}
(OUT/'audit.json').write_text(json.dumps(audit,indent=2))

cars=['BX_track','ETK_drift','Vivace_track','Sunburst_RS']
for maneuver in ['sweep','trail_hard','lift','lift_reversal']:
    fig,axes=plt.subplots(3,4,figsize=(16,9),layout='constrained')
    for col,car in enumerate(cars):
        for c,color in [('stock','#515965'),('slipline','#177eaa')]:
            for r in datasets[c]['runs']:
                if r['car']!=car or r['maneuver']!=maneuver:continue
                ss=[s for s in r['samples'] if s['t']>=12]
                offset=12 if maneuver=='sweep' else 18
                axes[0,col].plot([s['t']-offset for s in ss],angle_trace(ss,lambda s:s['beta']),color=color,alpha=.6,label=c if r['repeat']==0 else None)
                axes[1,col].plot([s['t']-offset for s in ss],angle_trace(ss,lambda s:axle(s,False)),color=color,alpha=.6)
                axes[2,col].plot([s['t']-offset for s in ss],[s['speed']*3.6 for s in ss],color=color,alpha=.6)
        axes[0,col].set_title(car.replace('_',' '))
        for idx,label in enumerate(['Body sideslip (В°)','Rear hub slip-angle estimate (В°)','Speed (km/h)']):
            axes[idx,col].set_ylabel(label);axes[idx,col].grid(alpha=.2);axes[idx,col].set_xlabel('Seconds from '+('sweep start' if maneuver=='sweep' else 'event'))
            if maneuver!='sweep':axes[idx,col].axvline(0,color='#aa6750',ls=':')
    axes[0,0].legend(frameon=False);fig.suptitle(maneuver.replace('_',' ').title()+' вЂ” all three repeats, 20 ms samples')
    fig.savefig(OUT/(maneuver+'_traces.png'),dpi=140);plt.close(fig)
fig,axes=plt.subplots(1,4,figsize=(16,4),layout='constrained')
for ax,car in zip(axes,cars):
    for c,color in [('stock','#515965'),('slipline','#177eaa')]:
        for r in datasets[c]['runs']:
            if r['car']!=car or r['maneuver']!='sweep':continue
            for a,b,style in [(12,20,'-'),(22,30,'--')]:
                ss=[s for s in r['samples'] if a<=s['t']<=b and s['speed']>8]
                ax.plot([abs(axle(s)) for s in ss],[abs(s['ay'])/9.81 for s in ss],style,color=color,alpha=.55,label=c if r['repeat']==0 and style=='-' else None)
    ax.set_title(car.replace('_',' '));ax.set_xlabel('Front hub slip-angle estimate |О±| (В°)');ax.set_ylabel('Lateral acceleration (g)');ax.grid(alpha=.2)
axes[0].legend(frameon=False);fig.suptitle('Vehicle response during steering sweep вЂ” solid increasing, dashed decreasing steering\nSpeed and throttle vary: these are response trajectories, not isolated tyre-force curves')
fig.savefig(OUT/'slip_angle_response.png',dpi=150);plt.close(fig)
table=['| Car / input | Peak sideslip В° stock в†’ Slipline | Max 100 ms sideslip rate В°/s | Recovery RMS В° | Entries qualify / 6 |','| --- | --- | --- | --- | --- |']
for p in paired:
    table.append('| '+p['car']+' / '+p['maneuver']+' | '+' | '.join(f"{p['metrics'][k]['stock']:.2f} в†’ {p['metrics'][k]['slipline']:.2f}" if k in p['metrics'] else 'вЂ” (insufficient moving samples)' for k in ['peak_beta_deg','peak_beta_rate_deg_s','recovery_beta_rms_deg'])+' | '+str(sum(r['qualified_entry'] for r in rows if r['car']==p['car'] and r['maneuver']==p['maneuver']))+' |')
stress=next(p for p in paired if p['car']=='Vivace_track' and p['maneuver']=='lift_reversal')
metrics=stress['metrics']
finding=f"In the Vivace lift/reversal case, mean moving event sideslip rises from {metrics['peak_beta_deg']['stock']:.2f}В° to {metrics['peak_beta_deg']['slipline']:.2f}В°, and its maximum 100 ms growth rate rises from {metrics['peak_beta_rate_deg_s']['stock']:.2f}В°/s to {metrics['peak_beta_rate_deg_s']['slipline']:.2f}В°/s. The mean 10В°в†’30В° transition interval falls from {metrics['transition_10_to_30_s']['stock']:.2f} s to {metrics['transition_10_to_30_s']['slipline']:.2f} s. Largest paired entry-speed difference in this case: {stress['max_paired_entry_kmh_difference']:.3f} km/h. This is a repeatable harsher breakaway under this prescribed stress input. It does not establish a universal spin threshold or real-world tyre accuracy. Other cars and inputs show smaller, mixed changes; they are retained below."
text='''# Slip angle, trail braking and lift-off response

144 visible stock/Slipline 0.2.3 runs: BX track and ETK I-Series drift (RWD), Vivace track (FWD), Sunburst RS (AWD), six manoeuvres, three repeats and two conditions. Redux is excluded. Released coefficients remain unchanged. Fixed update interval is 20 ms (50 Hz); tyre physics still runs at the game's native internal rate. Each run resets vehicle state; ESC is off where supported and factory ABS remains enabled. Arcade transmission can downshift under deceleration.

A stock-only pilot checked these inputs before the scored comparison. Steering sweep: at a 72 km/h entry target, increase normalized steering from zero to 0.45 over eight seconds, hold two seconds, then decrease over eight seconds. Speed feedback uses the same rule in both conditions, so actual throttle and achieved speed can differ. A sweep that saturates or spins is retained; the plot is a vehicle response trajectory, not a calibrated tyre force/slip-angle curve.

For the other inputs, ramp steering to 0.22 over two seconds, settle four seconds, then apply the event at t=18 s. Hold is a speed-feedback throttle control. Lift removes throttle for three seconds. Mild/heavy trail braking removes throttle and ramps the brake pedal to 0.25/0.50 in 0.25 s, holds until t=20 s, then releases over one second. At t=21 s all four inputs remove throttle and unwind steering over two seconds, with recovery observed through t=26 s. Brake pedal fractions are not fixed deceleration targets.

The additional lift/reversal stress case first settles at +0.50 steering, then removes throttle and reverses steering to в€’0.50 over 0.30 s. It holds that input until t=21 s, then unwinds to zero over two seconds. A stock-only pilot at В±0.35 gave limited sideslip, so В±0.50 was selected before scoring either condition. This deliberately tests a stronger weight-transfer/steering transition; it is separate from a pure throttle-lift test. All inputs are prescribed driver actions, with no edits to tyre or chassis state.

To obtain 20 ms updates, deterministic mode uses speed factor в€’1 with a 50 FPS limit. A timing pilot using positive speed factor 1 retained 50 ms controller updates and is excluded. The scored runs assert their actual minimum and maximum time steps. [BeamNG timing documentation](https://documentation.beamng.com/beamng_tech/deterministic_mode/)

Per-wheel alpha is a **kinematic hub estimate**: project average wheel-axis-node velocity onto the rolling/lateral directions derived from the wheel axis and vehicle up vector. It includes steered-wheel geometry; body sideslip is recorded separately. It is not a direct contact-patch force or aligning-torque measurement. Rear/front alpha difference is a response indicator, not a standalone understeer classification.

Sideslip rate and yaw acceleration use a 100 ms finite difference to limit single-frame noise. Angle differences are wrapped across В±180В°. Primary settled-turn event metrics use t=18вЂ“21 s; subsequent steering unwind and recovery are reported separately. Post-event spin duration covers the complete remainder of the run. Event metrics exclude speed below 5 m/s. Entries qualify if within 3 km/h of 72 and, for settled-turn events, body sideslip below 10В°. All failed entries and all repeats remain in the metrics, plots and aggregates. Three repeats describe this setup's variation; differences are not statistical confidence or a human feel score.

'''+ finding+'\n\n'+ '\n'.join(table)+f'''

Failed tyre observations: {summary['tyre_failure_samples']}. Geometric wheel-angle telemetry available throughout: {summary['all_wheel_geometry_available']}. Runs with body sideslip above 60В° while moving faster than 5 m/s: {summary['spin_runs']}.

Raw metrics also retain first crossing of 10В° and 30В° body sideslip and the interval between them, as descriptive transition thresholds. Missing crossings remain missing; they are not averaged as zero. The paired summary retains crossing and spin counts for each condition. Plots mask angles below 5 m/s and break lines at the В±180В° wrap to avoid drawing a mathematical discontinuity as a physical snap. Missing recovery measurements mean insufficient moving samples, not zero recovery error.

![Wheel slip-angle response trajectories](slip_angle_response.png)

![Heavy trail braking](trail_hard_traces.png)

![Sudden lift](lift_traces.png)

![Lift and rapid steering reversal](lift_reversal_traces.png)

All steering-sweep time traces: `sweep_traces.png`. Per-run input/response metrics: `run_metrics.csv`; paired means, standard deviations and repeat-wise delta ranges: `summary.json`. Interpreting a smaller sideslip rate as smoother requires checking achieved speed, initial state, recovery and whether a car spins. These tests can expose abruptness and loss of control, but cannot establish real-world tyre fidelity without external reference measurements.
'''
zone=datetime.timezone(datetime.timedelta(hours=3))
start=min(d['started'] for d in datasets.values());end=max(d['started']+d['wallSeconds'] for d in datasets.values())
interval=datetime.datetime.fromtimestamp(start,zone).isoformat(timespec='seconds')+' в†’ '+datetime.datetime.fromtimestamp(end,zone).isoformat(timespec='seconds')
text=text.replace('# Slip angle, trail braking and lift-off response', '# Slip angle, trail braking and lift-off response\n\nRecorded interval (Europe/Moscow): '+interval)
(OUT/'Handling-response-validation.md').write_text(text,encoding='utf-8')
