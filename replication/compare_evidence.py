"""Compare completed A/B outputs and C drawing data after model generation.

This comparison stage never changes model parameters or runs an author script.
"""
from pathlib import Path
import csv
import json

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence'
OUT=E/'comparison'
OUT.mkdir(exist_ok=True)


def read(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def save(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def case(row):return (float(row['omega']),float(row['alpha']))


author=read(E/'trajectories.csv')
model=read(E/'independent/trajectories.csv')
assert len(author)==len(model)==6000
residuals=[]
for a,b in zip(author,model):
    assert case(a)==case(b) and abs(float(a['t'])-float(b['t']))<1e-12
    residuals.append(dict(omega=float(a['omega']),alpha=float(a['alpha']),t=float(a['t']),
        position_B_minus_A=float(b['x1'])-float(a['x1']),
        velocity_B_minus_A=float(b['x2'])-float(a['x2']),
        input_B_minus_A=float(b['u'])-float(a['u'])))
save('author_vs_independent.csv',residuals)
A={case(x):x for x in read(E/'metrics.csv')}
B={case(x):x for x in read(E/'independent/metrics.csv')}
C={case(x):x for x in read(E/'published_figure_comparison.csv') if int(x['state'])==0}
rows=[]
for key in sorted(A):
    a,b,c=A[key],B[key],C[key]
    rows.append(dict(omega=key[0],alpha=key[1],
        author_A_y5=float(a['y_5s']),independent_B_y5=float(b['y_5s']),
        pdf_C_y5=float(c['paper_endpoint']),analytical_equilibrium=float(b['y_infinity']),
        analytical_steady_error_percent=float(b['steady_error_percent'])))
save('endpoint_comparison.csv',rows)

A7=read(E/'figure7_sensitivity.csv')
B7=read(E/'independent/figure7_sensitivity.csv')
C7=read(E/'figure7_published_points.csv')
assert len(A7)==len(B7)==len(C7)==100
f7=[]
for a,b,c in zip(A7,B7,C7):
    assert float(a['omega_low'])==float(b['omega_low'])==float(c['omega_low'])
    assert abs(float(a['alpha'])-float(b['alpha']))<1e-12
    assert abs(float(c['alpha'])-float(b['alpha']))<1e-6
    f7.append(dict(omega_low=float(b['omega_low']),omega_high=float(b['omega_high']),alpha=float(b['alpha']),
        author_A_width5=float(a['author_width_5s']),independent_B_width5=float(b['width_5s']),
        pdf_C_width5=float(c['published_width']),equilibrium_width=float(b['equilibrium_width']),
        B_minus_A=float(b['width_5s'])-float(a['author_width_5s']),
        B_minus_C=float(b['width_5s'])-float(c['published_width'])))
save('figure7_comparison.csv',f7)
summary=dict(
    A='Author-code rerun; archived outputs from executing the original programs.',
    B='Standalone equation-based reconstruction; generated without A or C inputs.',
    C='Coordinates extracted from published PDF vector paths; artifact audit only.',
    dependency_note='A and C share the author computational lineage. B shares the published model/settings and was developed with source access; it is not blinded or physical validation.',
    comparison_performed_after_B_outputs=True,
    max_position_B_minus_A=max(abs(r['position_B_minus_A']) for r in residuals),
    max_velocity_B_minus_A=max(abs(r['velocity_B_minus_A']) for r in residuals),
    max_input_B_minus_A=max(abs(r['input_B_minus_A']) for r in residuals),
    figure7_max_B_minus_A=max(abs(r['B_minus_A']) for r in f7),
    figure7_max_B_minus_C=max(abs(r['B_minus_C']) for r in f7))
assert summary['max_position_B_minus_A']<1e-6 and summary['max_velocity_B_minus_A']<1e-6
(OUT/'provenance_and_comparison.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
