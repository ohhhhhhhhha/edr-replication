"""Reproduce EDR Figures 2-3, validate against published vectors, and vary alpha.

Run: python reproduce.py [--extra-deps PATH]
Source files are preserved; only the plotting backend/show function is adapted.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import runpy
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--extra-deps', type=Path)
args = parser.parse_args()
if args.extra_deps:
    sys.path.append(str(args.extra_deps.resolve()))
OUT = ROOT / 'evidence'
OUT.mkdir(exist_ok=True)
os.environ['MPLBACKEND'] = 'Agg'
os.environ['MPLCONFIGDIR'] = str(OUT / 'mplconfig')
import numpy as np
import scipy
from scipy.integrate import solve_ivp
import matplotlib
import matplotlib.pyplot as plt
import control as ct
import pdfplumber


def save_csv(name, rows):
    with (OUT / name).open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def theoretical(t, w, a):
    """Closed-form solution of y''+4y'+k*y=g; initial state zero."""
    t = np.asarray(t)
    k, g = w*w + 3 + a*a, 4 + a*a
    eq = g/k
    d = k-4
    if abs(d) < 1e-14:
        y = eq * (1 - np.exp(-2*t)*(1+2*t))
        v = eq * 4*t*np.exp(-2*t)
    elif d > 0:
        q = np.sqrt(d)
        y = eq * (1-np.exp(-2*t)*(np.cos(q*t)+2/q*np.sin(q*t)))
        v = g/q*np.exp(-2*t)*np.sin(q*t)
    else:
        q = np.sqrt(-d)
        y = eq * (1-np.exp(-2*t)*(np.cosh(q*t)+2/q*np.sinh(q*t)))
        v = g/q*np.exp(-2*t)*np.sinh(q*t)
    return np.array([y, v])


def rhs(w, a):
    return lambda t, z: [z[1], -(w*w+3+a*a)*z[0]-4*z[1]+4+a*a]


source = ROOT/'source'/'author_experiment1.py'
src = source.read_bytes()
git_blob = hashlib.sha1(b'blob '+str(len(src)).encode()+b'\0'+src).hexdigest()
assert git_blob == '8a8e4c5e5fc6c27efba99fae3094e3cf53d77233', git_blob
author_figs = OUT/'author_figures'
author_figs.mkdir(exist_ok=True)
old_dir = Path.cwd()
old_show = plt.show
os.chdir(author_figs)
plt.show = lambda *a, **kw: None
try:
    ns = runpy.run_path(str(source))
finally:
    plt.show = old_show
    os.chdir(old_dir)
    plt.close('all')
assert len(list(author_figs.glob('*.pdf'))) == 6

t = np.linspace(0, 5, 1000)
case_keys = [(0.5, 0., '参变x_min'), (0.5, 2., '参变x_min_n'),
             (1., 0., '参环x'), (1., 2., '参环x_n'),
             (1.5, 0., '参变x_max'), (1.5, 2., '参变x_max_n')]
states, metrics, trajectories, checks = {}, [], [], []
for w,a,key in case_keys:
    x = np.asarray(ns[key])
    assert x.shape == (2,1000) and np.isfinite(x).all()
    states[w,a] = x
    independent = solve_ivp(rhs(w,a), (0,5), [0.,0.], t_eval=t,
                            method='DOP853', rtol=1e-11, atol=1e-13)
    assert independent.success
    exact = theoretical(t,w,a)
    err_ode = float(np.max(np.abs(x-independent.y)))
    err_exact = float(np.max(np.abs(x-exact)))
    assert err_ode < 1e-6 and err_exact < 1e-6
    eq = (4+a*a)/(w*w+3+a*a)
    u = -(3+a*a)*x[0]-4*x[1]+4+a*a
    long = solve_ivp(rhs(w,a),(0,30),[0.,0.],t_eval=[30.],
                     method='DOP853',rtol=1e-11,atol=1e-13)
    assert long.success and abs(long.y[0,-1]-eq) < 1e-9
    poles = np.roots([1,4,w*w+3+a*a])
    assert np.max(poles.real)<0
    metrics.append(dict(omega=w,alpha=a,y_5s=float(x[0,-1]),v_5s=float(x[1,-1]),
        y_infinity=eq,steady_error_percent=100*abs(1-eq),
        endpoint_minus_equilibrium=float(x[0,-1]-eq),
        peak_abs_u=float(np.max(np.abs(u))),
        overshoot_own_equilibrium_percent=100*max(0,float(np.max(x[0])/eq-1)),
        max_state_difference_ode=err_ode,max_state_difference_exact=err_exact,
        y_30s=float(long.y[0,-1]),equilibrium_check_30s=float(abs(long.y[0,-1]-eq)),
        poles='; '.join(str(z) for z in poles)))
    trajectories.extend(dict(omega=w,alpha=a,t=float(tt),x1=float(yy),x2=float(vv),u=float(uu))
                        for tt,yy,vv,uu in zip(t,x[0],x[1],u))
save_csv('metrics.csv',metrics)
save_csv('trajectories.csv',trajectories)

# Read published vector paths. Axis locations are calibrated from horizontal grid
# lines and checked against the zero-initial-state vertex. All 12 plotted lines
# are extracted; filled envelopes and legend strokes are excluded by curve index.
pdf = pdfplumber.open(ROOT/'source'/'EDR_published_paper.pdf')
panels = [dict(page=8, label='2a', curves=[(0,1.,0.),(1,1.,2.)], state=0),
          dict(page=8, label='2b', curves=[(5,1.,0.),(6,1.,2.)], state=1),
          dict(page=8, label='3a', curves=[(12,.5,2.),(13,1.5,2.),(14,.5,0.),(15,1.5,0.)],state=0),
          dict(page=9, label='3b', curves=[(2,.5,2.),(3,1.5,2.),(4,.5,0.),(5,1.5,0.)],state=1)]
paper_points, paper_checks, endpoints = [], [], {}
for panel in panels:
    page = pdf.pages[panel['page']]
    first = page.curves[panel['curves'][0][0]]
    x0,x1 = first['x0'],first['x1']
    y0 = first['pts'][0][1]
    horizontal = sorted(set(round(l['top'],8) for l in page.lines
        if abs(l['x0']-x0)<1e-5 and abs(l['x1']-x1)<1e-5
        and abs(l['top']-l['bottom'])<1e-8 and y0-25<l['top']<y0-10))
    # Adjacent horizontal grid line above zero denotes +0.2 in each panel.
    assert len(horizontal)==1, (panel['label'],horizontal)
    scale = (y0-horizontal[0])/.2
    for idx,w,a in panel['curves']:
        pts=np.array(page.curves[idx]['pts'])
        pt=(pts[:,0]-x0)/(x1-x0)*5
        py=(y0-pts[:,1])/scale
        assert abs(pt[0])<1e-9 and abs(pt[-1]-5)<1e-9 and abs(py[0])<1e-9
        assert np.all(np.diff(pt)>=-1e-8)
        ref=theoretical(pt,w,a)[panel['state']]
        error=py-ref
        maxerr=float(np.max(np.abs(error)))
        assert maxerr < 1e-6, (panel['label'],w,a,maxerr)
        paper_checks.append(dict(figure=panel['label'],omega=w,alpha=a,state=panel['state'],
            n_vertices=len(pt),max_abs_difference=maxerr,rmse=float(np.sqrt(np.mean(error**2))),
            paper_endpoint=float(py[-1]),replicated_endpoint=float(states[w,a][panel['state'],-1]),
            scale_pdf_points_per_unit=scale))
        if panel['state']==0: endpoints[w,a]=float(py[-1])
        paper_points.extend(dict(figure=panel['label'],omega=w,alpha=a,t=float(tt),
            paper_value=float(yy),replicated_value=float(rr),difference=float(ee))
            for tt,yy,rr,ee in zip(pt,py,ref,error))
pdf.close()
save_csv('published_vector_points.csv',paper_points)
save_csv('published_figure_comparison.csv',paper_checks)

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,
                     'axes.titlesize':10,'axes.labelsize':9,'legend.fontsize':8,
                     'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(2,2,figsize=(6.3,4.3),layout='constrained')
cols={0.:'#42677F',2.:'#C65F32'}
for j in [0,1]:
    ax=axes[0,j]
    for a in [0.,2.]:
        ax.plot(t,states[1.,a][j],color=cols[a],label='Baseline' if a==0 else 'EDR, α = 2',lw=1.6)
    ax.set_title(f"({'a' if j==0 else 'b'}) Nominal {'position' if j==0 else 'velocity'}")
    ax=axes[1,j]
    for w,ls in [(.5,'-'),(1.5,'--')]:
        for a in [0.,2.]:
            ax.plot(t,states[w,a][j],color=cols[a],ls=ls,lw=1.4,
                label=f"{'Base' if a==0 else 'EDR'} ω = {w}")
    ax.set_title(f"({'c' if j==0 else 'd'}) Mismatch {'position' if j==0 else 'velocity'}")
for i in [0,1]:
    for j in [0,1]:
        ax=axes[i,j]
        ax.set(xlim=(0,5),xlabel='Time (s)',ylabel='Position (rad)' if j==0 else 'Velocity (rad/s)')
        ax.grid(alpha=.2)
        ax.legend(loc='lower right' if j==0 else 'upper right',ncol=1)
        if j==0: ax.axhline(1,color='.5',ls=':',lw=.8);ax.set_ylim(0,1.4)
fig.savefig(OUT/'replicated_figures_2_3.png',dpi=300)
fig.savefig(OUT/'replicated_figures_2_3.pdf')
plt.close(fig)

sweep=[]
sweep_traj=[]
fine=np.linspace(0,5,2001)
for a in [0.,1.,2.,3.]:
    errors=[100*abs(1-(4+a*a)/(w*w+3+a*a)) for w in [.5,1.,1.5]]
    sample_peaks=[]
    for w in [.5,1.,1.5]:
        sol=solve_ivp(rhs(w,a),(0,5),[0.,0.],t_eval=fine,method='DOP853',rtol=1e-11,atol=1e-13)
        assert sol.success
        assert np.max(abs(sol.y-theoretical(fine,w,a)))<1e-6
        u=-(3+a*a)*sol.y[0]-4*sol.y[1]+4+a*a
        sample_peaks.append(float(np.max(abs(u))))
        sweep_traj.extend(dict(omega=w,alpha=a,t=float(tt),x1=float(yy),x2=float(vv),u=float(uu))
            for tt,yy,vv,uu in zip(fine,sol.y[0],sol.y[1],u))
    nominal=theoretical(fine,1.,a)[0]
    overshoot=0 if a==0 else 100*np.exp(-2*np.pi/a)
    sweep.append(dict(alpha=a,error_w05_percent=errors[0],error_w15_percent=errors[2],
        worst_error_percent=max(errors),nominal_overshoot_percent=float(overshoot),
        nominal_sampled_overshoot_percent=100*max(0,float(max(nominal)-1)),
        peak_abs_u_all_cases=max(sample_peaks),initial_u=4+a*a))
save_csv('alpha_sweep.csv',sweep)
save_csv('alpha_sweep_trajectories.csv',sweep_traj)

fig,axes=plt.subplots(1,2,figsize=(6.3,2.25),layout='constrained')
palette=['#667582','#47929A','#C65F32','#825A8C']
for a,color in zip([0,1,2,3],palette):
    axes[0].plot(fine,theoretical(fine,1.,a)[0],color=color,label=f'α = {a}',lw=1.4)
axes[0].axhline(1,color='.4',ls=':',lw=.8)
axes[0].set(xlabel='Time (s)',ylabel='Nominal position (rad)',xlim=(0,5))
axes[0].legend(ncol=2,loc='lower right')
axes[1].plot([r['initial_u'] for r in sweep],[r['worst_error_percent'] for r in sweep],'-o',color='#42677F')
for r in sweep: axes[1].annotate(f"α = {r['alpha']:g}",(r['initial_u'],r['worst_error_percent']),xytext=(3,5),textcoords='offset points',fontsize=8)
axes[1].set(xlabel='Initial control input (model units)',ylabel='Worst steady error (%)',ylim=(5,28),xlim=(3,14))
for ax in axes: ax.grid(alpha=.2)
fig.savefig(OUT/'alpha_tradeoff.png',dpi=300)
fig.savefig(OUT/'alpha_tradeoff.pdf')
plt.close(fig)

# Read the exported file, rather than counting in-memory rows only.
loaded=np.genfromtxt(OUT/'trajectories.csv',delimiter=',',names=True)
assert len(loaded)==6000 and len(loaded.dtype.names)==6
assert np.isfinite(np.column_stack([loaded[n] for n in loaded.dtype.names])).all()
summary=dict(run_utc=datetime.now(timezone.utc).isoformat(),python=sys.version,platform=platform.platform(),
    versions=dict(numpy=np.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__,control=ct.__version__,pdfplumber=pdfplumber.__version__),
    source_sha256=hashlib.sha256(src).hexdigest(),source_git_blob=git_blob,
    paper_sha256=hashlib.sha256((ROOT/'source'/'EDR_published_paper.pdf').read_bytes()).hexdigest(),
    author_plot_count=6,exported_trajectory_rows=len(loaded),main_cases=6,extension_cases=12,
    max_state_difference_ode=max(m['max_state_difference_ode'] for m in metrics),
    max_state_difference_exact=max(m['max_state_difference_exact'] for m in metrics),
    max_equilibrium_check_30s=max(m['equilibrium_check_30s'] for m in metrics),
    paper_vector_vertices=len(paper_points),
    max_published_position_difference=max(c['max_abs_difference'] for c in paper_checks if c['state']==0),
    max_published_velocity_difference=max(c['max_abs_difference'] for c in paper_checks if c['state']==1),
    numerical_tolerance=1e-6,
    paper_comparison_note='Differences at PDF polyline vertices include plot simplification/coordinate quantization; they are not raw-data errors.',
    metrics=metrics,sweep=sweep,paper_comparison=paper_checks)
(OUT/'verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ['metrics','sweep','paper_comparison']},indent=2))
print('All six baseline cases, 12 sweep cases, export/reload and independent numerical checks passed.')
