"""Routes A/C: rerun the author Figure 7 script and audit PDF vector paths.

Run from the repository root: python replication/author_sensitivity_audit.py
The independent Figure 7 calculation is part of independent_model.py.
"""
from pathlib import Path
import argparse
import csv
import json
import os
import runpy
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--extra-deps', type=Path)
args = parser.parse_args()
if args.extra_deps:
    sys.path.append(str(args.extra_deps.resolve()))
OUT = ROOT / 'evidence'
os.environ['MPLBACKEND'] = 'Agg'
os.environ['MPLCONFIGDIR'] = str(OUT / 'mplconfig')
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import pdfplumber


def equilibrium(omega, alpha):
    return (4 + alpha**2) / (omega**2 + 3 + alpha**2)


def exact_position(t, omega, alpha):
    k = omega**2 + 3 + alpha**2
    d = k - 4
    if abs(d) < 1e-14:
        transient = 1 + 2*t
    elif d > 0:
        q = np.sqrt(d)
        transient = np.cos(q*t) + 2*np.sin(q*t)/q
    else:
        q = np.sqrt(-d)
        transient = np.cosh(q*t) + 2*np.sinh(q*t)/q
    return equilibrium(omega, alpha)*(1 - np.exp(-2*t)*transient)


def save_csv(name, rows):
    with (OUT / name).open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


print('[1/3] Running the original 50-gain sensitivity experiment.')
show = plt.show
plt.show = lambda *a, **kw: None
try:
    author = runpy.run_path(str(ROOT / 'author_source/author_sensitivity.py'))
finally:
    plt.show = show
    plt.close('all')
alphas = np.asarray(author['aa'])
assert len(alphas) == 50 and alphas[0] == 0 and alphas[-1] == 25
intervals = [(0.5, 1.5, 'y1'), (0.1, 1.9, 'y2')]
rows = []
ode_errors = []
author_errors = []
for lo, hi, key in intervals:
    values = np.asarray(author[key])
    for a, observed in zip(alphas, values):
        exact = exact_position(5, lo, a) - exact_position(5, hi, a)
        integrated = []
        for w in [lo, hi]:
            def rhs(t, x):
                return [x[1], -(w*w + 3 + a*a)*x[0] - 4*x[1] + 4 + a*a]
            sol = solve_ivp(rhs, (0, 5), [0., 0.], t_eval=[5.],
                            method='DOP853', rtol=1e-11, atol=1e-13)
            assert sol.success
            integrated.append(float(sol.y[0, -1]))
            ode_errors.append(abs(integrated[-1] - exact_position(5, w, a)))
        steady_width = equilibrium(lo, a) - equilibrium(hi, a)
        worst_error = max(abs(1-equilibrium(lo, a)), abs(1-equilibrium(hi, a)))
        author_errors.append(abs(observed-exact))
        rows.append(dict(omega_low=lo, omega_high=hi, alpha=float(a),
            author_width_5s=float(observed), exact_width_5s=float(exact),
            independent_width_5s=integrated[0]-integrated[1],
            equilibrium_width=float(steady_width), worst_steady_error=float(worst_error),
            endpoint_bias=float(observed-steady_width)))
assert max(author_errors) < 1e-6 and max(ode_errors) < 1e-6
save_csv('figure7_sensitivity.csv', rows)

print('[2/3] Comparing both curves with the published PDF drawing.')
point_rows = []
with pdfplumber.open(ROOT / 'author_source/EDR_published_paper.pdf') as pdf:
    page = pdf.pages[12]
    curves = [c for c in page.curves if len(c['pts']) == 50 and not c['fill']]
    assert len(curves) == 2
    x0, x1 = curves[0]['x0'], curves[0]['x1']
    grid_y = sorted({l['top'] for l in page.lines
        if abs(l['x0']-x0)<1e-6 and abs(l['x1']-x1)<1e-6
        and abs(l['bottom']-l['top'])<1e-6
        and isinstance(l.get('stroking_color'), (int, float))
        and abs(l['stroking_color']-0.6901960784)<1e-7})
    assert len(grid_y) == 8
    y_zero = grid_y[-1]
    scale = (grid_y[-1]-grid_y[-2])/0.1
    # Labels 0.0 ... 0.7 and evenly spaced grid lines calibrate the drawing.
    assert np.max(abs(np.diff(grid_y)-np.median(np.diff(grid_y)))) < 1e-5
    ticks = [w for w in page.extract_words() if x0-20<w['x0']<x0
             and grid_y[0]-5<w['top']<grid_y[-1]+5]
    assert {f'{i/10:.1f}' for i in range(8)} <= {w['text'] for w in ticks}
    for curve, (lo, hi, key) in zip(curves, intervals):
        pts = np.asarray(curve['pts'])
        drawing_alpha = (pts[:, 0]-x0)/(x1-x0)*25
        drawing_width = (y_zero-pts[:, 1])/scale
        # PDF coordinates round the original 50-point alpha grid.
        assert np.max(abs(drawing_alpha-alphas))<1e-6
        for a, value in zip(drawing_alpha, drawing_width):
            exact = exact_position(5, lo, a)-exact_position(5, hi, a)
            point_rows.append(dict(omega_low=lo, omega_high=hi, alpha=float(a),
                published_width=float(value), exact_width_5s=float(exact),
                difference=float(value-exact)))
assert len(point_rows) == 100
assert max(abs(r['difference']) for r in point_rows) < 1e-6
save_csv('figure7_published_points.csv', point_rows)

selected = []
for lo, hi, key in intervals:
    for a in [0., 2., 3., 25.]:
        width5 = exact_position(5, lo, a)-exact_position(5, hi, a)
        width_inf = equilibrium(lo, a)-equilibrium(hi, a)
        selected.append(dict(omega_low=lo, omega_high=hi, alpha=a,
            width_5s=width5, equilibrium_width=width_inf,
            worst_steady_error_percent=100*max(abs(1-equilibrium(lo, a)),abs(1-equilibrium(hi, a))),
            endpoint_bias=width5-width_inf,
            endpoint_relative_bias_percent=100*(width5-width_inf)/width_inf))
save_csv('figure7_selected_metrics.csv', selected)

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,
    'axes.titlesize':10,'axes.labelsize':9,'legend.fontsize':8,
    'axes.spines.top':False,'axes.spines.right':False})
fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.6), layout='constrained')
for lo, hi, color in [(0.5,1.5,'#42677F'),(0.1,1.9,'#C65F32')]:
    data=[r for r in rows if r['omega_low']==lo]
    points=[r for r in point_rows if r['omega_low']==lo]
    label=f'ω ∈ [{lo:g}, {hi:g}]'
    axes[0].plot(alphas,[r['author_width_5s'] for r in data],color=color,label=label,lw=1.6)
    axes[0].scatter([r['alpha'] for r in points[::3]],[r['published_width'] for r in points[::3]],
        marker='o',facecolors='none',edgecolors=color,s=15,zorder=3)
    axes[1].plot(alphas,[r['endpoint_bias'] for r in data],color=color,label=label,lw=1.6)
axes[0].set(xlabel='EDR parameter α',ylabel='Endpoint spread W₅ (rad)',xlim=(0,25),ylim=(0,.76),
    title='(a) Rerun and published vertices')
axes[0].legend()
axes[1].set(xlabel='EDR parameter α',ylabel='W₅ − W∞ (rad)',xlim=(0,5),
    title='(b) Finite-horizon bias')
axes[1].axhline(0,color='.5',lw=.8,ls=':')
axes[1].legend()
for ax in axes:ax.grid(alpha=.2)
fig.savefig(OUT/'figure7_replication.png',dpi=300)
fig.savefig(OUT/'figure7_replication.pdf')
plt.close(fig)
summary=dict(run_utc=datetime.now(timezone.utc).isoformat(),
    gain_count=50,alpha_range=[0,25],intervals=[[.5,1.5],[.1,1.9]],
    state_simulation_cases=200,published_vertices=100,
    max_author_vs_closed_form=float(max(author_errors)),
    max_dop853_position_difference=float(max(ode_errors)),
    max_published_width_difference=float(max(abs(r['difference']) for r in point_rows)),
    metric='W5 = y(5, omega_low) - y(5, omega_high), not worst reference error.',
    equilibrium_metric='Winfinity = y_infinity(omega_low) - y_infinity(omega_high).',
    selected_metrics=selected)
(OUT/'figure7_verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('[3/3] Figure 7 reproduced; finite endpoints and equilibria recorded separately.')
print(json.dumps(summary,indent=2))
