"""Run the project implementation in replication/reproduce.py."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parent / 'replication' / 'reproduce.py'),
                   run_name='__main__')
