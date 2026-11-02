Ctrl_4 - EEEN3015J Control Theory - Final report Section A

EVIDENCE ROUTES
A: author-code re-execution. The wrappers author_rerun.py and
author_sensitivity_audit.py execute the preserved original programs.
B: independent_model.py implements the plant and feedback equations directly.
It imports no author code and reads no PDF or existing comparison results. The default
reproduce.py launcher runs B only.
C: PDF vector coordinates from the publication, used for artifact comparison.
A and C have a shared computational origin; their close agreement is not
independent replication. B was developed after access to the paper and source,
so independence concerns implementation/execution, not a blinded reconstruction.

RUN WITH PYTHON 3.12
    python -m pip install -r requirements.txt
    python reproduce.py
    python replication/compare_evidence.py
    python replication/design_analysis.py

B outputs are under evidence/independent/. The comparison stage reads these
completed results and the archived A/C outputs, then writes evidence/comparison/.
To use another output folder for B:
    python replication/independent_model.py --output-dir my_results

OPTIONAL ORIGINAL-AUTHOR RERUNS
    python replication/author_rerun.py
    python replication/author_sensitivity_audit.py
These regenerate A/C references. They are separate from B and are not needed
to generate the independent model outputs. The original author's plotting
escapes can cause SyntaxWarning messages without changing the dynamics.

RESULTS
The six main B cases generate 6000 trajectory rows. The alpha extension has
12 cases; Figure 7 uses 50 gains and two frequency intervals, giving 200 endpoint
calculations. verification.json records analytical, RK45 and tighter-tolerance
checks, plus changed-reference/nonzero-initial-state cases. A separate execution
test on 2 November 2026 ran B without author files, PDFs or saved reference data.

PROVENANCE
Main archived A outputs were recorded on 17 October 2026. The Figure 7 audit
and independent model were completed on 2 November 2026. Independent outputs
have their own run records. The report plots B and labels A/C comparisons.
PDF coordinates are drawing data, not an independent experimental dataset.

SOURCE MATERIAL
author_source/author_experiment1.py: original 实验一.py, unchanged.
author_source/author_sensitivity.py: original 实验二.py, unchanged.
author_source/EDR_published_paper.pdf: published paper, CC BY 4.0.
Author repository: https://github.com/fylimas/EDR
Paper DOI: https://doi.org/10.3390/mca31010011

FILE GUIDE
evidence/independent/trajectories.csv and metrics.csv: six main model cases.
evidence/independent/alpha_sweep*.csv: independent gain study.
evidence/independent/figure7_sensitivity.csv: independent endpoint spreads.
evidence/independent/verification.json and additional_checks.csv: solver checks.
evidence/comparison/endpoint_comparison.csv: A/B/C endpoints and analytical values.
evidence/comparison/author_vs_independent.csv: full-grid A/B differences.
evidence/comparison/figure7_comparison.csv: explicitly labelled Figure 7 audit.
evidence/design_constraints.json: illustrative analytical design constraints.

Archived A/C results and their original plots remain directly under evidence/.
Original source is unchanged. Rerunning a route replaces that route's generated
files; use a copy when retaining the supplied snapshot.
