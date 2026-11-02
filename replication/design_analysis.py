"""Analytical design-constraint extension; no new physical assumptions in the plant."""
from pathlib import Path
import csv,json,math
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence'
def steady(w,a):return (4+a*a)/(w*w+3+a*a)
def worst_error(a):return 1.25/(5.25+a*a)
def nominal_overshoot(a):return 0 if a==0 else math.exp(-2*math.pi/a)
rows=[]
for a in [0,1,2,3]:
    derivative=-2/(4+a*a)
    h=1e-5
    fd=(steady(1+h,a)-steady(1-h,a))/(2*h)
    assert abs(derivative-fd)<1e-9
    errors=[abs(1-steady(.5+i/1000,a)) for i in range(1001)]
    assert abs(max(errors)-worst_error(a))<1e-12
    rows.append(dict(alpha=a,nominal_dyinf_domega=derivative,
        worst_steady_error_percent=100*worst_error(a),
        nominal_overshoot_percent=100*nominal_overshoot(a),initial_input=4+a*a))
low=math.sqrt(1.25/.1-5.25)
high_os=2*math.pi/math.log(20)
high_u=math.sqrt(10-4)
assert low>high_os and low>high_u
assert abs(worst_error(low)-.1)<1e-14
assert abs(nominal_overshoot(high_os)-.05)<1e-14
relaxed_low=math.sqrt(1.25/.15-5.25)
assert relaxed_low<2<high_os and worst_error(2)<.15 and nominal_overshoot(2)<.05
data=dict(illustrative_specs_not_paper_requirements=True,
    scope='Constant unit step, zero state, fixed velocity-feedback coefficient 4, nonnegative alpha, linear unsaturated plant.',
    target_worst_error_percent=10,target_nominal_overshoot_percent=5,target_initial_input_limit=10,
    min_alpha_for_10pct_error=low,max_alpha_for_5pct_overshoot=high_os,
    max_alpha_from_initial_input_limit=high_u,min_initial_input_for_10pct_error=4+low*low,
    nominal_overshoot_at_min_error_gain_percent=100*nominal_overshoot(low),
    min_alpha_for_15pct_error=relaxed_low,
    joint_specs_feasible=False,relaxed_15pct_error_and_5pct_overshoot_alpha2_feasible=True,
    explanation='The input constraint is necessary: peak absolute input cannot be below its initial value. No saturation experiment was run.',
    sweep=rows)
(OUT/'design_constraints.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
with (OUT/'analytical_sensitivity.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps(data,indent=2))
