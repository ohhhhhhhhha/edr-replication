"""Audit initial input and finite-grid input peaks from the saved Route B sweep.

The result is a sampled statement on [0, 5] s, not an all-time analytic bound.
"""
from pathlib import Path
import csv
import json
import math

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/diagnostics'
OUT.mkdir(exist_ok=True)
with (ROOT/'evidence/independent/alpha_sweep_trajectories.csv').open(encoding='utf-8',newline='') as f:
    data=list(csv.DictReader(f))
assert len(data)==24012
records=[]
for alpha in [0.,1.,2.,3.]:
    for omega in [.5,1.,1.5]:
        case=[r for r in data if float(r['alpha'])==alpha and float(r['omega'])==omega]
        times=[float(r['t']) for r in case]
        inputs=[float(r['u']) for r in case]
        assert len(case)==2001 and times[0]==0 and times[-1]==5
        assert all(abs((b-a)-.0025)<1e-10 for a,b in zip(times,times[1:]))
        assert all(math.isfinite(u) for u in inputs)
        assert float(case[0]['x1'])==0 and float(case[0]['x2'])==0
        initial=4+alpha**2
        assert abs(inputs[0]-initial)<1e-12
        index=max(range(len(inputs)),key=lambda i:abs(inputs[i]))
        peak=abs(inputs[index])
        records.append(dict(alpha=alpha,omega=omega,sample_count=len(case),
            horizon_seconds=5.,grid_spacing_seconds=.0025,initial_input=initial,
            sampled_peak_abs_input=peak,time_of_sampled_peak=times[index],
            signed_input_at_peak=inputs[index],minimum_input=min(inputs),maximum_input=max(inputs)))
with (OUT/'control_effort_audit.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
gains=[]
for alpha in [0.,1.,2.,3.]:
    case=[r for r in records if r['alpha']==alpha]
    gains.append(dict(alpha=alpha,initial_input=4+alpha**2,
        sampled_peak_abs_input=max(r['sampled_peak_abs_input'] for r in case),
        peak_times=sorted({r['time_of_sampled_peak'] for r in case}),cases=len(case)))
summary=dict(cases=12,samples_per_case=2001,horizon_seconds=5.,grid_spacing_seconds=.0025,
    all_sampled_peaks_at_zero=all(r['time_of_sampled_peak']==0 for r in records),
    initial_equals_sampled_peak=all(r['initial_input']==r['sampled_peak_abs_input'] for r in records),
    interpretation='Finite-grid observation only. No assertion about the continuous-time maximum over all t >= 0.',
    actuator_bound='For any trajectory, sup_t |u(t)| >= |u(0)|; the design infeasibility needs only this necessary condition.',
    gain_summary=gains)
assert summary['all_sampled_peaks_at_zero'] and summary['initial_equals_sampled_peak']
(OUT/'control_effort_audit.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
