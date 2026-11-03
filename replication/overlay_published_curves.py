"""Post-hoc overlay of saved B solutions and C PDF vertices, with residuals.

No simulation is fitted or rerun here. Cubic Hermite interpolation evaluates the
already generated B solution at C's vertex times; position and velocity retain
their own units throughout the comparison.
"""
from pathlib import Path
import argparse
import csv
import json
import os
import sys

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--extra-deps',type=Path)
args=parser.parse_args()
if args.extra_deps:sys.path.append(str(args.extra_deps.resolve()))
OUT=ROOT/'evidence/comparison'
OUT.mkdir(exist_ok=True)
os.environ['MPLBACKEND']='Agg'
os.environ['MPLCONFIGDIR']=str(ROOT/'evidence/mplconfig')
import numpy as np
from scipy.interpolate import CubicHermiteSpline
import matplotlib.pyplot as plt


def rows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def write(name,data):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)


B=rows(ROOT/'evidence/independent/trajectories.csv')
C=rows(ROOT/'evidence/published_vector_points.csv')
AB=rows(OUT/'author_vs_independent.csv')
assert len(B)==6000 and len(C)==715 and len(AB)==6000
curves,details,summaries={},[],[]
for panel in ['2a','2b','3a','3b']:
    state=0 if panel.endswith('a') else 1
    cases=[(1.,0.),(1.,2.)] if panel.startswith('2') else [(.5,0.),(.5,2.),(1.5,0.),(1.5,2.)]
    for omega,alpha in cases:
        b=[r for r in B if float(r['omega'])==omega and float(r['alpha'])==alpha]
        c=[r for r in C if r['figure']==panel and float(r['omega'])==omega and float(r['alpha'])==alpha]
        ab=[r for r in AB if float(r['omega'])==omega and float(r['alpha'])==alpha]
        t=np.array([float(r['t']) for r in b])
        y=np.array([float(r['x1']) for r in b])
        v=np.array([float(r['x2']) for r in b])
        u=np.array([float(r['u']) for r in b])
        values=y if state==0 else v
        derivative=v if state==0 else -omega**2*y+u
        tc=np.array([float(r['t']) for r in c])
        paper=np.array([float(r['paper_value']) for r in c])
        sampled=CubicHermiteSpline(t,values,derivative)(tc)
        residual=sampled-paper
        component='position_B_minus_A' if state==0 else 'velocity_B_minus_A'
        max_ab=max(abs(float(r[component])) for r in ab)
        unit='rad' if state==0 else 'rad/s'
        summaries.append(dict(panel=panel,omega=omega,alpha=alpha,state='position' if state==0 else 'velocity',
            unit=unit,pdf_vertices=len(c),max_abs_B_minus_A=max_ab,
            max_abs_B_minus_C=float(max(abs(residual))),rmse_B_minus_C=float(np.sqrt(np.mean(residual**2)))))
        details.extend(dict(panel=panel,omega=omega,alpha=alpha,t=float(tt),unit=unit,
            B_interpolated=float(bb),C_pdf_value=float(cc),B_minus_C=float(dd))
            for tt,bb,cc,dd in zip(tc,sampled,paper,residual))
        curves[panel,omega,alpha]=(t,values,tc,paper)
assert len(summaries)==12 and len(details)==715
write('curve_residuals.csv',summaries)
write('overlay_vertices.csv',details)

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,
    'axes.labelsize':9,'legend.fontsize':8,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(2,2,figsize=(6.3,4.0),layout='constrained')
colors={0.:'#42677F',2.:'#C65F32'}
for panel,ax in zip(['2a','2b','3a','3b'],axes.ravel()):
    state=0 if panel.endswith('a') else 1
    cases=[(1.,0.),(1.,2.)] if panel.startswith('2') else [(.5,0.),(.5,2.),(1.5,0.),(1.5,2.)]
    for omega,alpha in cases:
        t,values,tc,paper=curves[panel,omega,alpha]
        label=('Baseline' if alpha==0 else 'EDR, α = 2') if panel.startswith('2') else f"{'Baseline' if alpha==0 else 'EDR'} ω = {omega}"
        style='--' if omega==1.5 else '-'
        ax.plot(t,values,color=colors[alpha],ls=style,label=label,lw=1.35)
        ax.plot(tc[::3],paper[::3],ls='none',marker='o',ms=3.0,mfc='none',mec=colors[alpha],mew=.7)
    ax.set_title(f"({panel}) {'Nominal' if panel.startswith('2') else 'Mismatch'} {'position' if state==0 else 'velocity'}")
    ax.set(xlim=(0,5),xlabel='Time (s)',ylabel='Position (rad)' if state==0 else 'Velocity (rad/s)')
    ax.grid(alpha=.2)
    ax.legend(loc='lower right' if state==0 else 'upper right',labelspacing=.2,borderpad=.25)
    if state==0:ax.set_ylim(0,1.4)
fig.savefig(OUT/'published_overlay.png',dpi=300)
plt.close(fig)
summary=dict(comparison='B solution versus C PDF vertices, after independent model generation',
    interpolation='Cubic Hermite from saved B values and derivatives; residual includes interpolation and PDF precision.',
    main_grid_count=1000,pdf_vertices=715,panel_count=4,curve_count=12,
    max_position_B_minus_A=max(r['max_abs_B_minus_A'] for r in summaries if r['state']=='position'),
    max_velocity_B_minus_A=max(r['max_abs_B_minus_A'] for r in summaries if r['state']=='velocity'),
    max_position_B_minus_C=max(r['max_abs_B_minus_C'] for r in summaries if r['state']=='position'),
    max_velocity_B_minus_C=max(r['max_abs_B_minus_C'] for r in summaries if r['state']=='velocity'),
    interpretation='Post-hoc artifact comparison, not an independent experimental dataset.')
assert summary['max_position_B_minus_C']<1e-6 and summary['max_velocity_B_minus_C']<1e-6
(OUT/'overlay_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
