"""Summarize original telemetry without assuming that more sliding is better."""
from pathlib import Path
import json, math, statistics as st, csv

ROOT=Path.cwd()
RESULTS=ROOT/'results'
OUT=ROOT/'analysis'
def mean(items):
    items=list(items);return st.mean(items) if items else None
def sd(items):
    items=list(items);return st.stdev(items) if len(items)>1 else 0
def window(samples,a,b):return [s for s in samples if a<=s['t']<=b]
def summarize(condition,r):
    samples=r['samples'];measure=[s for s in samples if s['phase']=='measure']
    assert samples and measure
    tyres=[w for s in samples for w in s['tyres']]
    factors=[w['factor'] for w in tyres]
    row={'condition':condition,'car':r['car'],'maneuver':r['maneuver'],'repeat':r['repeat'],
      'family':r.get('family',r['car']),'compound':r.get('compound'),
      'entry_kmh':measure[0]['speed']*3.6,'sample_count':len(samples),'dt_min':r['clock']['dtMin'],'dt_max':r['clock']['dtMax'],
      'flat_samples':sum(w['flat'] or w['punctured'] or w['broken'] for w in tyres),
      'factor_min':min(factors),'factor_mean':mean(factors),'factor_max':max(factors),
      'min_pressure_psi':min(w['pressure'] for w in tyres if w.get('pressure') is not None),
      'drive_mode':r['metadata']['driveMode'],'peak_beta_deg':max((abs(s['beta']) for s in measure if s['speed']>5),default=0),
      'peak_yaw_deg_s':max(abs(s['yawRate'])*180/math.pi for s in measure),'reversing_samples':sum(s['longSpeed']< -1 for s in measure),
      'warmup_speed_sd':sd(s['speed'] for s in window(samples,10,12)),
      'esc_samples':sum((s.get('escActive') or 0)>0 for s in measure),'tc_samples':sum((s.get('tcActive') or 0)>0 for s in measure)}
    initial_sample=next((s for s in samples if all(w.get('temps') for w in s['tyres'])),samples[0])
    initial=initial_sample['tyres'];entry=measure[0]['tyres']
    row['initial_temperature_sample_s']=initial_sample['t'] if all(w.get('temps') for w in initial) else None
    row['initial_tread_c']=mean(mean(w['temps'][:3]) for w in initial if w.get('temps'))
    row['entry_tread_c']=mean(mean(w['temps'][:3]) for w in entry if w.get('temps'))
    row['final_tread_c']=mean(mean(w['temps'][:3]) for w in samples[-1]['tyres'] if w.get('temps'))
    row['peak_tread_zone_c']=max((max(w['temps'][:3]) for w in tyres if w.get('temps')),default=None)
    row['peak_core_c']=max((w['temps'][3] for w in tyres if w.get('temps')),default=None)
    row['initial_condition']=mean(w['condition'] for w in initial if w.get('condition') is not None)
    row['entry_pressure_psi']=mean(w['pressure'] for w in entry)
    if r['maneuver']=='corner':
        low=window(samples,14,17);high=window(samples,22,28)
        for label,data in [('low',low),('high',high)]:
            row[label+'_lat_g']=mean(abs(s['ay'])/9.81 for s in data)
            row[label+'_yaw_deg_s']=mean(abs(s['yawRate'])*180/math.pi for s in data)
            row[label+'_beta_deg']=mean(abs(s['beta']) for s in data)
            row[label+'_radius_m']=mean(s['speed']/abs(s['yawRate']) for s in data if abs(s['yawRate'])>.01)
            row[label+'_speed_kmh']=mean(s['speed']*3.6 for s in data)
            row[label+'_speed_sd']=sd(s['speed'] for s in data)
            row[label+'_yaw_cv']=sd(s['yawRate'] for s in data)/max(abs(mean(s['yawRate'] for s in data)),.001)
        row['metric']='high_lat_g';row['value']=row['high_lat_g']
        row['valid']=row['high_speed_sd']<1 and row['high_yaw_cv']<.15 and row['peak_beta_deg']<60
    elif r['maneuver']=='steering':
        turn=window(samples,12,14)
        row['step_peak_yaw_deg_s']=max(abs(s['yawRate'])*180/math.pi for s in turn)
        row['recovery_yaw_rms_deg_s']=math.sqrt(mean((s['yawRate']*180/math.pi)**2 for s in window(samples,16,19)))
        first=window(samples,12,13)
        peak=max(abs(s['yawRate']) for s in first)
        t10=next((s['t'] for s in first if abs(s['yawRate'])>=.1*peak),None)
        t90=next((s['t'] for s in first if abs(s['yawRate'])>=.9*peak),None)
        row['rise_time_s']=t90-t10 if t10 is not None and t90 is not None else None
        row['metric']='step_peak_yaw_deg_s';row['value']=row['step_peak_yaw_deg_s'];row['valid']=row['entry_kmh']>65 and row['peak_beta_deg']<60
    elif r['maneuver']=='brake':
        a=measure[0];end=measure[-1]
        path=sum(math.hypot(b['x']-a1['x'],b['y']-a1['y']) for a1,b in zip(measure,measure[1:]))
        row['brake_distance_m']=path;row['stop_time_s']=end['t']-a['t'];row['stop_speed_kmh']=end['speed']*3.6
        row['brake_max_decel_g']=max(-s['ax']/9.81 for s in measure)
        # Mildly mismatched entry speeds can be inspected through a v^2-normalized distance too.
        row['distance_at_100_kmh_m']=path*(100/row['entry_kmh'])**2
        row['metric']='brake_distance_m';row['value']=path;row['valid']=abs(row['entry_kmh']-100)<2 and row['stop_speed_kmh']<1.8
    else:
        sliding=[s for s in measure if s['speed']>5 and 10<=abs(s['beta'])<=60]
        row['slide_duration_s']=sum(s['dt'] for s in sliding)
        row['spin_duration_s']=sum(s['dt'] for s in measure if s['speed']>5 and abs(s['beta'])>60)
        row['slide_speed_kmh']=mean(s['speed']*3.6 for s in sliding)
        row['slide_beta_deg']=mean(abs(s['beta']) for s in sliding)
        row['qualifies_as_controlled_drift']=row['slide_duration_s']>=2 and row['spin_duration_s']<.25
        row['metric']='slide_duration_s';row['value']=row['slide_duration_s'];row['valid']=row['entry_kmh']>60 and row['slide_duration_s']>=.5
    return row

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[];datasets={}
    for condition in ['stock','slipline','redux','redux_slipline']:
        path=RESULTS/(condition+'.json')
        if not path.exists():continue
        d=json.loads(path.read_text());datasets[condition]=d
        rows.extend(summarize(condition,r) for r in d['runs'])
    fields=sorted(set(k for r in rows for k in r))
    with (OUT/'run_metrics.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    paired=[]
    for baseline,modified in [('stock','slipline'),('redux','redux_slipline')]:
        for car in sorted(set(r['car'] for r in rows)):
            for maneuver in ['corner','steering','brake','drift']:
                a=sorted([r for r in rows if r['condition']==baseline and r['car']==car and r['maneuver']==maneuver],key=lambda r:r['repeat'])
                b=sorted([r for r in rows if r['condition']==modified and r['car']==car and r['maneuver']==maneuver],key=lambda r:r['repeat'])
                if len(a)!=3 or len(b)!=3:continue
                values_a=[r['value'] for r in a];values_b=[r['value'] for r in b]
                deltas=[y-x for x,y in zip(values_a,values_b)]
                entry_deltas=[y['entry_kmh']-x['entry_kmh'] for x,y in zip(a,b)]
                entry_temps=[y['entry_tread_c']-x['entry_tread_c'] for x,y in zip(a,b) if x['entry_tread_c'] is not None and y['entry_tread_c'] is not None]
                item={'baseline':baseline,'modified':modified,'car':car,'maneuver':maneuver,'metric':a[0]['metric'],
                  'baseline_mean':mean(values_a),'modified_mean':mean(values_b),'baseline_sd':sd(values_a),'modified_sd':sd(values_b),
                  'delta_mean':mean(deltas),'delta_min':min(deltas),'delta_max':max(deltas),
                  'delta_percent':100*mean(deltas)/mean(values_a) if mean(values_a) else None,
                  'max_entry_speed_difference_kmh':max(abs(x) for x in entry_deltas),
                  'max_entry_temp_difference_c':max([abs(x) for x in entry_temps],default=0),
                  'all_runs_qualified':all(r['valid'] for r in a+b)}
                secondary={'corner':['low_lat_g','high_radius_m','high_speed_kmh','high_beta_deg'],
                  'steering':['rise_time_s','recovery_yaw_rms_deg_s','peak_beta_deg'],
                  'brake':['distance_at_100_kmh_m','stop_time_s','stop_speed_kmh'],
                  'drift':['spin_duration_s','slide_beta_deg','slide_speed_kmh','peak_beta_deg']}[maneuver]
                item['secondary']={}
                for key in secondary:
                    av=[r[key] for r in a if r.get(key) is not None];bv=[r[key] for r in b if r.get(key) is not None]
                    item['secondary'][key]={'baseline':mean(av),'modified':mean(bv),'delta':mean(bv)-mean(av) if av and bv else None}
                paired.append(item)
    summary={'runs':len(rows),'completed_conditions':list(datasets),'safety':{'failed_tyre_samples':sum(r['flat_samples'] for r in rows),'minimum_pressure_psi':min([r['min_pressure_psi'] for r in rows],default=None)},'paired':paired,'unqualified_runs':[{'condition':r['condition'],'car':r['car'],'maneuver':r['maneuver'],'repeat':r['repeat']} for r in rows if not r['valid']]}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('Summarized',len(rows),'runs;',len(paired),'complete comparisons')
    for item in paired:print(item['baseline'],item['car'],item['maneuver'],round(item['baseline_mean'],3),round(item['modified_mean'],3),'delta%',round(item['delta_percent'] or 0,2),'qualified',item['all_runs_qualified'])
    return summary,rows,datasets

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--results',type=Path,default=RESULTS)
    parser.add_argument('--out',type=Path,default=OUT)
    args=parser.parse_args();RESULTS=args.results.resolve();OUT=args.out.resolve()
    main()
