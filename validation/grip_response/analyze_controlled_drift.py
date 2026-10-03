from pathlib import Path
import json,csv,statistics as st,math,sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--results',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args();RESULTS=args.results.resolve();OUT=args.out.resolve()
OUT.mkdir(parents=True,exist_ok=True)
datasets={c:json.loads((RESULTS/('controlled_'+c+'.json')).read_text()) for c in ['stock','slipline']}
assert all(len(d['runs'])==6 for d in datasets.values())
rows=[]
def longest(samples,predicate):
    maximum,current=0,0
    for s in samples:
        current=current+s['dt'] if predicate(s) else 0;maximum=max(maximum,current)
    return maximum
for condition,d in datasets.items():
    for r in d['runs']:
        assert r['driverParameters']=={'feedforward':.12,'rimRatio':1.25}
        samples=[s for s in r['samples'] if s['t']>=14]
        sliding=lambda s:s['speed']>10 and 10<=abs(s['beta'])<=40
        wheel_samples=[w for s in r['samples'] for w in s['tyres']]
        row={'condition':condition,'car':r['car'],'repeat':r['repeat'],
          'slide_time_s':sum(s['dt'] for s in samples if sliding(s)),
          'longest_slide_s':longest(samples,sliding),
          'spin_time_s':sum(s['dt'] for s in samples if s['speed']>5 and abs(s['beta'])>60),
          'mean_speed_kmh':st.mean(s['speed']*3.6 for s in samples),
          'mean_beta_deg':st.mean(s['beta'] for s in samples),
          'tracking_error_rms_deg':math.sqrt(st.mean((s['beta']+20)**2 for s in samples)),
          'steer_rms':math.sqrt(st.mean(s['steer']**2 for s in samples)),
          'mean_throttle':st.mean(s['throttle'] for s in samples),
          'rear_rim_overdrive_mean':st.mean(st.mean(abs(w['rimSpeed']) for w in s['tyres'] if w['name'] in ['RL','RR'])/max(abs(s['longSpeed']),1) for s in samples),
          'tyre_failure_samples':sum(w['flat'] or w['broken'] or w['punctured'] for w in wheel_samples)}
        row['qualified']=row['longest_slide_s']>=2 and row['spin_time_s']<.25 and row['rear_rim_overdrive_mean']>1.1
        rows.append(row)
with (OUT/'controlled_drift_metrics.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
paired=[]
for car in ['BX_track','ETK_drift']:
    a=[r for r in rows if r['condition']=='stock' and r['car']==car];b=[r for r in rows if r['condition']=='slipline' and r['car']==car]
    p={'car':car,'all_qualified':all(r['qualified'] for r in a+b)}
    for k in ['slide_time_s','longest_slide_s','tracking_error_rms_deg','mean_speed_kmh','steer_rms','mean_throttle']:
        p[k]={'stock':st.mean(r[k] for r in a),'slipline':st.mean(r[k] for r in b)}
    paired.append(p)
summary={'runs':len(rows),'qualified':sum(r['qualified'] for r in rows),'tyre_failure_samples':sum(r['tyre_failure_samples'] for r in rows),'paired':paired}
(OUT/'controlled_drift_summary.json').write_text(json.dumps(summary,indent=2))
fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
for col,car in enumerate(['BX_track','ETK_drift']):
    for condition,color in [('stock','#515965'),('slipline','#177eaa')]:
        for r in datasets[condition]['runs']:
            if r['car']!=car:continue
            s=[x for x in r['samples'] if x['phase']=='measure']
            axes[0,col].plot([x['t']-12 for x in s],[x['beta'] for x in s],color=color,alpha=.6,label=condition if r['repeat']==0 else None)
            axes[1,col].plot([x['t']-12 for x in s],[x['speed']*3.6 for x in s],color=color,alpha=.6)
    axes[0,col].axhline(-20,color='#aa6750',ls=':',lw=1);axes[0,col].set_title(car.replace('_',' '));axes[0,col].set_ylabel('Body sideslip (degrees)')
    axes[1,col].set_ylabel('Speed (km/h)')
    for ax in axes[:,col]:ax.grid(alpha=.2);ax.set_xlabel('Seconds after slide entry')
axes[0,0].legend(frameon=False)
fig.suptitle('Feedback-driven RWD slide follow-up вЂ” three fresh repeats\nFrozen driver settings; dotted line is the в€’20В° angle target')
fig.savefig(OUT/'controlled_drift_traces.png',dpi=160);plt.close(fig)
table=['| Car | Slide time s: stock в†’ Slipline | Longest continuous slide s | Angle error RMS В° | Qualified / 6 |','| --- | --- | --- | --- | --- |']
for p in paired:
    table.append('| '+p['car']+' | '+' | '.join(f"{p[k]['stock']:.2f} в†’ {p[k]['slipline']:.2f}" for k in ['slide_time_s','longest_slide_s','tracking_error_rms_deg'])+' | '+str(sum(r['qualified'] for r in rows if r['car']==p['car']))+' |')
text='''# Feedback-driven drift follow-up

Twelve additional visible runs: BX track and ETK I-Series drift, stock versus Slipline 0.2.3, three fresh repeats each. Redux was not included in this follow-up. Mod coefficients remained unchanged.

The original aggressive input spins these cars. A separate stock-only pilot qualified a feedback driver; its settings were frozen before these fresh stock and Slipline runs. The driver targets в€’20В° body sideslip and uses the same steering feedback and rear-rim-speed throttle rule for both cars and both conditions. Feedforward = 0.12; rim ratio = 1.25; other gains are in `slipline_drift_driver.lua`. Closed-loop inputs can differ in response to the changed car state. This compares the resulting state and required control, not identical pedal histories.

After the two-second slide-entry period, qualification requires a continuous 2 s with speed above 10 m/s and body sideslip between 10В° and 40В°, less than 0.25 s above 60В°, and mean rear-rim overdrive above 1.10. It is a limited sustained-slide criterion, not proof of skilled human drifting or realistic forces.

'''+ '\n'.join(table)+f'''

{summary['qualified']} of 12 runs qualify; {summary['tyre_failure_samples']} failed tyre observations. Mean speed differs between conditions and must be considered alongside the angle/control measurements. Longer sliding duration alone is not an improvement score. These runs provide a repeatable sustained-slide comparison, while human feel, sound and real-world tyre-force accuracy remain unvalidated.

BX qualifies in all six runs, but its mean angle-tracking RMS error increases from 4.88В° to 6.44В° with Slipline and it requires more steering correction. ETK stock qualifies in all three repeats; Slipline qualifies in one of three. The two failed Slipline repeats remain in every aggregate and plot. Neither car spins under this driver. This follow-up provides no drift-control benefit for the current modifier under the tested control rule.

![All repeats of the RWD slide follow-up](controlled_drift_traces.png)

Per-run measurements: `controlled_drift_metrics.csv`; paired means: `controlled_drift_summary.json`. All raw samples and the frozen driver are included in the validation bundle. Pilot runs are excluded from the scored results.
'''
(OUT/'Controlled-drift-followup.md').write_text(text,encoding='utf-8')
print(json.dumps(summary,indent=2))
