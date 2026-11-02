"""Standalone equation-based reconstruction of the EDR pendulum experiment.

Inputs are the equations and settings listed below. This module does not import
the author's scripts or read pre-existing reference results or PDF curves.
It was developed after inspecting the paper and source, so it is not blinded.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path,
                        default=Path(__file__).resolve().parents[1]/'evidence'/'independent')
    parser.add_argument('--extra-deps', type=Path)
    args = parser.parse_args()
    if args.extra_deps:
        sys.path.append(str(args.extra_deps.resolve()))
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    os.environ['MPLBACKEND'] = 'Agg'
    os.environ['MPLCONFIGDIR'] = str(out/'mplconfig')
    import numpy as np
    import scipy
    from scipy.integrate import solve_ivp
    import matplotlib.pyplot as plt

    def control(state, alpha, reference):
        position, velocity = state
        return -(3 + alpha**2)*position - 4*velocity + (4 + alpha**2)*reference

    def simulate(omega, alpha, times, reference=1., initial=(0., 0.),
                 method='DOP853', rtol=1e-11, atol=1e-13):
        # Keep the plant and controller separate, as in the published equations.
        def plant(t, state):
            u = control(state, alpha, reference)
            return [state[1], -omega**2*state[0] + u]
        solution = solve_ivp(plant, (0., float(times[-1])), initial,
                             t_eval=times, method=method, rtol=rtol, atol=atol)
        assert solution.success and np.isfinite(solution.y).all()
        return solution.y

    def equilibrium(omega, alpha, reference=1.):
        return (4 + alpha**2)*reference/(omega**2 + 3 + alpha**2)

    def analytical(times, omega, alpha, reference=1., initial=(0., 0.)):
        # Solve the homogeneous second-order equation about its equilibrium.
        times = np.asarray(times)
        k = omega**2 + 3 + alpha**2
        offset = initial[0] - equilibrium(omega, alpha, reference)
        velocity = initial[1]
        if abs(k-4) < 1e-14:
            f, g = np.ones_like(times), times
        elif k > 4:
            q = np.sqrt(k-4)
            f, g = np.cos(q*times), np.sin(q*times)/q
        else:
            q = np.sqrt(4-k)
            f, g = np.cosh(q*times), np.sinh(q*times)/q
        decay = np.exp(-2*times)
        y = equilibrium(omega, alpha, reference) + decay*(offset*f + (velocity+2*offset)*g)
        v = decay*(velocity*f - (k*offset+2*velocity)*g)
        return np.vstack([y, v])

    def save_csv(name, rows):
        with (out/name).open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    print('[1/3] Solving six cases directly from the plant and controller equations.')
    t = np.linspace(0, 5, 1000)
    states, metrics, trajectories = {}, [], []
    for omega in [.5, 1., 1.5]:
        for alpha in [0., 2.]:
            x = simulate(omega, alpha, t)
            states[omega, alpha] = x
            exact = analytical(t, omega, alpha)
            alternate = simulate(omega, alpha, t, method='RK45')
            refined = simulate(omega, alpha, t, rtol=1e-12, atol=1e-14)
            long = simulate(omega, alpha, np.array([30.]))
            u = control(x, alpha, 1.)
            eq = equilibrium(omega, alpha)
            errors = [float(np.max(abs(x-other))) for other in [exact, alternate, refined]]
            assert max(errors)<1e-6 and abs(long[0,-1]-eq)<1e-6
            metrics.append(dict(omega=omega, alpha=alpha, y_5s=float(x[0,-1]),
                v_5s=float(x[1,-1]), y_infinity=eq, steady_error_percent=100*abs(1-eq),
                peak_abs_u=float(np.max(abs(u))), max_error_closed_form=errors[0],
                max_difference_rk45=errors[1], max_difference_tighter_tolerance=errors[2],
                equilibrium_residual_30s=float(abs(long[0,-1]-eq))))
            trajectories.extend(dict(omega=omega, alpha=alpha, t=float(tt),
                x1=float(yy), x2=float(vv), u=float(uu))
                for tt,yy,vv,uu in zip(t,x[0],x[1],u))
    save_csv('metrics.csv', metrics)
    save_csv('trajectories.csv', trajectories)

    # Exercise the implementation away from the paper's unit-reference/zero-state case.
    additional = []
    for omega, alpha, reference, initial in [(1.2,1.5,.7,(.2,-.15)),(.8,0.,1.5,(-.1,.3))]:
        x = simulate(omega,alpha,t,reference,initial)
        error = float(np.max(abs(x-analytical(t,omega,alpha,reference,initial))))
        assert error<1e-6
        additional.append(dict(omega=omega,alpha=alpha,reference=reference,
            initial_position=initial[0],initial_velocity=initial[1],max_error_closed_form=error))
    save_csv('additional_checks.csv', additional)

    print('[2/3] Calculating the parameter variation and the broader sensitivity study.')
    fine = np.linspace(0,5,2001)
    sweep, sweep_trajectories, sweep_states = [], [], {}
    for alpha in [0.,1.,2.,3.]:
        peaks = []
        for omega in [.5,1.,1.5]:
            x = simulate(omega,alpha,fine)
            assert np.max(abs(x-analytical(fine,omega,alpha)))<1e-6
            sweep_states[omega,alpha]=x
            u=control(x,alpha,1.)
            peaks.append(float(max(abs(u))))
            sweep_trajectories.extend(dict(omega=omega,alpha=alpha,t=float(tt),
                x1=float(yy),x2=float(vv),u=float(uu))
                for tt,yy,vv,uu in zip(fine,x[0],x[1],u))
        overshoot=0. if alpha==0 else 100*np.exp(-2*np.pi/alpha)
        sampled=100*max(0,float(max(sweep_states[1.,alpha][0])-1))
        assert abs(sampled-overshoot)<1.1e-5
        sweep.append(dict(alpha=alpha,
            error_w05_percent=100*abs(1-equilibrium(.5,alpha)),
            error_w15_percent=100*abs(1-equilibrium(1.5,alpha)),
            worst_error_percent=max(100*abs(1-equilibrium(w,alpha)) for w in [.5,1.,1.5]),
            nominal_overshoot_percent=float(overshoot), nominal_sampled_overshoot_percent=sampled,
            peak_abs_u_all_cases=max(peaks), initial_u=4+alpha**2))
    save_csv('alpha_sweep.csv',sweep)
    save_csv('alpha_sweep_trajectories.csv',sweep_trajectories)

    alphas=np.linspace(0,25,50)
    sensitivity=[]
    for lo,hi in [(.5,1.5),(.1,1.9)]:
        for alpha in alphas:
            low=simulate(lo,alpha,np.array([5.]))[0,-1]
            high=simulate(hi,alpha,np.array([5.]))[0,-1]
            width=low-high
            exact=analytical(np.array([5.]),lo,alpha)[0,-1]-analytical(np.array([5.]),hi,alpha)[0,-1]
            eqwidth=equilibrium(lo,alpha)-equilibrium(hi,alpha)
            assert abs(width-exact)<1e-6
            sensitivity.append(dict(omega_low=lo,omega_high=hi,alpha=float(alpha),
                width_5s=float(width),closed_form_width_5s=float(exact),
                equilibrium_width=float(eqwidth),endpoint_bias=float(width-eqwidth)))
    save_csv('figure7_sensitivity.csv',sensitivity)

    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,
        'axes.labelsize':9,'legend.fontsize':8,'axes.spines.top':False,'axes.spines.right':False})
    colors={0.:'#42677F',2.:'#C65F32'}
    fig,axes=plt.subplots(2,2,figsize=(6.3,4.3),layout='constrained')
    for j in [0,1]:
        for alpha in [0.,2.]:
            axes[0,j].plot(t,states[1.,alpha][j],color=colors[alpha],lw=1.6,
                label='Baseline' if alpha==0 else 'EDR, α = 2')
        axes[0,j].set_title(f"({'a' if j==0 else 'b'}) Nominal {'position' if j==0 else 'velocity'}")
        for omega,style in [(.5,'-'),(1.5,'--')]:
            for alpha in [0.,2.]:
                axes[1,j].plot(t,states[omega,alpha][j],color=colors[alpha],ls=style,lw=1.4,
                    label=f"{'Base' if alpha==0 else 'EDR'} ω = {omega}")
        axes[1,j].set_title(f"({'c' if j==0 else 'd'}) Mismatch {'position' if j==0 else 'velocity'}")
    for i in [0,1]:
        for j in [0,1]:
            ax=axes[i,j]
            ax.set(xlim=(0,5),xlabel='Time (s)',ylabel='Position (rad)' if j==0 else 'Velocity (rad/s)')
            ax.grid(alpha=.2)
            ax.legend(loc='lower right' if j==0 else 'upper right')
            if j==0:ax.axhline(1,color='.5',ls=':',lw=.8);ax.set_ylim(0,1.4)
    fig.savefig(out/'main_responses.png',dpi=300)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(6.3,2.25),layout='constrained')
    for a,color in zip([0.,1.,2.,3.],['#667582','#47929A','#C65F32','#825A8C']):
        axes[0].plot(fine,sweep_states[1.,a][0],color=color,label=f'α = {a:g}',lw=1.4)
    axes[0].axhline(1,color='.4',ls=':',lw=.8)
    axes[0].set(xlabel='Time (s)',ylabel='Nominal position (rad)',xlim=(0,5))
    axes[0].legend(ncol=2,loc='lower right')
    axes[1].plot([s['initial_u'] for s in sweep],[s['worst_error_percent'] for s in sweep],'-o',color='#42677F')
    for s in sweep:axes[1].annotate(f"α = {s['alpha']:g}",(s['initial_u'],s['worst_error_percent']),xytext=(3,5),textcoords='offset points',fontsize=8)
    axes[1].set(xlabel='Initial control input (model units)',ylabel='Worst steady error (%)',ylim=(5,28),xlim=(3,14))
    for ax in axes:ax.grid(alpha=.2)
    fig.savefig(out/'alpha_tradeoff.png',dpi=300)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(6.5,2.6),layout='constrained')
    for lo,hi,color in [(.5,1.5,'#42677F'),(.1,1.9,'#C65F32')]:
        selected=[s for s in sensitivity if s['omega_low']==lo]
        label=f'ω ∈ [{lo:g}, {hi:g}]'
        axes[0].plot(alphas,[s['width_5s'] for s in selected],color=color,label=label,lw=1.6)
        axes[1].plot(alphas,[s['endpoint_bias'] for s in selected],color=color,label=label,lw=1.6)
    axes[0].set(xlabel='EDR parameter α',ylabel='Endpoint spread W₅ (rad)',xlim=(0,25),ylim=(0,.76),title='(a) Equation-based sensitivity')
    axes[1].set(xlabel='EDR parameter α',ylabel='W₅ − W∞ (rad)',xlim=(0,5),title='(b) Finite-horizon bias')
    axes[1].axhline(0,color='.5',lw=.8,ls=':')
    for ax in axes:ax.grid(alpha=.2);ax.legend()
    fig.savefig(out/'figure7_sensitivity.png',dpi=300)
    plt.close(fig)

    loaded=np.genfromtxt(out/'trajectories.csv',delimiter=',',names=True)
    assert len(loaded)==6000 and np.isfinite(np.column_stack([loaded[n] for n in loaded.dtype.names])).all()
    summary=dict(run_utc=datetime.now(timezone.utc).isoformat(),
        input_provenance='Published equations and explicit parameter settings; no author program, saved result or PDF input.',
        development_context='Developed after access to paper and source; not a blinded reconstruction.',
        solver='DOP853',rtol=1e-11,atol=1e-13,alternate_solver='RK45',
        tighter_rtol=1e-12,tighter_atol=1e-14,numerical_target=1e-6,
        numpy_version=np.__version__,scipy_version=scipy.__version__,
        main_cases=6,trajectory_rows=6000,extension_cases=12,figure7_endpoint_cases=200,
        max_error_closed_form=max(m['max_error_closed_form'] for m in metrics),
        max_difference_rk45=max(m['max_difference_rk45'] for m in metrics),
        max_difference_tighter_tolerance=max(m['max_difference_tighter_tolerance'] for m in metrics),
        max_equilibrium_residual_30s=max(m['equilibrium_residual_30s'] for m in metrics),
        additional_nonpaper_checks=additional,metrics=metrics,sweep=sweep)
    (out/'verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('[3/3] Independent outputs saved; analytical, solver and tolerance checks passed.')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['metrics','sweep']},indent=2))


if __name__=='__main__':
    main()
