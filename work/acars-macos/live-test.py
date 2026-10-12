from pathlib import Path
import argparse
import json
import signal
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--ppm', type=int, default=0)
parser.add_argument('--gain', type=float, default=49.6)
parser.add_argument('--seconds', type=int, default=120)
parser.add_argument('--name', default='acars-corrected-test')
parser.add_argument('frequencies', nargs='*', default=['131.550'])
opts = parser.parse_args()
bundle = Path(__file__).resolve().parents[2] / 'outputs/acars-macos-arm64'
(bundle / 'data').mkdir(exist_ok=True)
json_path = bundle / 'data' / (opts.name + '.jsonl')
before = len(json_path.read_text().splitlines()) if json_path.exists() else 0
args = [str(bundle / 'bin/acarsdec'), '-v', '-i', 'MA-ACARS', '--rtlsdr', '0',
        '-g', str(opts.gain), '-p', str(opts.ppm), '--output', 'full:file',
        '--output', 'json:file:path=' + str(json_path), *opts.frequencies]
print('Live ACARS capture:', json_path, flush=True)
proc = subprocess.Popen(args)
try:
    proc.wait(timeout=opts.seconds)
except subprocess.TimeoutExpired:
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.terminate()
        proc.wait(timeout=10)
rows = [json.loads(line) for line in json_path.read_text().splitlines()[before:]
        if line.strip()] if json_path.exists() else []
print('LIVE TEST COMPLETE:', len(rows), 'new messages; decoder exit:', proc.returncode, flush=True)
if rows:
    print('Frequencies:', sorted({row['freq'] for row in rows}), flush=True)
    print('Aircraft:', sorted({row.get('tail', '') for row in rows}), flush=True)
