"""Check the default entry point in a fresh directory without A/C material."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--extra-deps',type=Path)
args=parser.parse_args()
with tempfile.TemporaryDirectory(prefix='edr-independent-') as temp:
    isolated=Path(temp).resolve()
    assert isolated.parent==Path(tempfile.gettempdir()).resolve()
    assert isolated.name.startswith('edr-independent-')
    (isolated/'replication').mkdir()
    shutil.copy2(ROOT/'reproduce.py',isolated/'reproduce.py')
    shutil.copy2(ROOT/'replication/independent_model.py',isolated/'replication/independent_model.py')
    initial_files=sorted(p.relative_to(isolated).as_posix() for p in isolated.rglob('*') if p.is_file())
    assert initial_files==['replication/independent_model.py','reproduce.py']
    command=[sys.executable,'reproduce.py','--output-dir','outputs']
    if args.extra_deps:command += ['--extra-deps',str(args.extra_deps.resolve())]
    start=time.perf_counter()
    result=subprocess.run(command,cwd=isolated,capture_output=True,text=True,
                          encoding='utf-8',errors='replace')
    elapsed=time.perf_counter()-start
    if result.returncode:
        print(result.stdout)
        print(result.stderr,file=sys.stderr)
        raise SystemExit(result.returncode)
    generated=isolated/'outputs'
    verification=json.loads((generated/'verification.json').read_text())
    assert verification['main_cases']==6 and verification['trajectory_rows']==6000
    assert verification['extension_cases']==12 and verification['figure7_endpoint_cases']==200
    # These references are read by the parent only after the child has finished.
    checked=[]
    for expected in sorted((ROOT/'evidence/independent').glob('*.csv')):
        assert expected.read_bytes()==(generated/expected.name).read_bytes(),expected.name
        checked.append(expected.name)
    record=dict(checked_utc=datetime.now(timezone.utc).isoformat(),passed=True,
        entry_point='python reproduce.py --output-dir outputs',
        initial_working_directory_files=initial_files,
        author_scripts_present=False,pdf_present=False,reference_results_present=False,
        child_exit_code=result.returncode,matching_csv_files=checked,
        elapsed_seconds=elapsed,python_version=platform.python_version(),
        platform=platform.platform(),architecture=platform.machine(),
        timing_scope='Child process including model, checks and plotting; excludes dependency installation.',
        comparison_timing='Parent compares results only after the isolated child exits.',
        environment='Existing installed numerical libraries; this is execution isolation, not a clean dependency installation.')
(ROOT/'evidence/independent/execution_check.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
