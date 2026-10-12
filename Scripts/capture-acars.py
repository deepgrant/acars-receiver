"""Run a bounded ACARS capture and stop only the decoder started here."""
import argparse
import json
import math
from pathlib import Path
import re
import signal
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--decoder', type=Path, required=True)
parser.add_argument('--probe', type=Path, required=True)
parser.add_argument('--data-dir', type=Path, required=True)
parser.add_argument('--device')
parser.add_argument('--station', default='MA-ACARS')
parser.add_argument('--ppm', type=int, default=0)
parser.add_argument('--gain', type=float, default=49.6)
parser.add_argument('--seconds', type=int, default=120)
parser.add_argument('--name', default='acars-capture')
parser.add_argument('frequencies', nargs='+')

def stop_decoder(process):
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

def main():
    opts = parser.parse_args()
    if opts.seconds <= 0:
        parser.error('--seconds must be positive')
    if not math.isfinite(opts.gain):
        parser.error('--gain must be finite')
    if not re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_.-]*', opts.name):
        parser.error('--name must be a filename without directory separators')
    try:
        if any(not math.isfinite(float(f)) or float(f) <= 0 for f in opts.frequencies):
            raise ValueError()
    except ValueError:
        parser.error('frequencies must be positive decimal MHz values')
    count = int(subprocess.check_output([str(opts.probe), '--count'], text=True).strip())
    if count == 0:
        parser.error('No RTL-SDR detected.')
    if count > 1 and opts.device is None:
        parser.error('Multiple receivers detected. Select the spare receiver with -Pdevice or SDR_DEVICE.')
    opts.data_dir.mkdir(parents=True, exist_ok=True)
    json_path = opts.data_dir / (opts.name + '.jsonl')
    before = len(json_path.read_text().splitlines()) if json_path.exists() else 0
    command = [str(opts.decoder), '-v', '-i', opts.station, '--rtlsdr', opts.device or '0',
               '-g', str(opts.gain), '-p', str(opts.ppm), '--output', 'full:file',
               '--output', 'json:file:path=' + str(json_path), *opts.frequencies]
    print('Live ACARS capture:', json_path, flush=True)
    process = subprocess.Popen(command)
    interrupted = False
    def interrupted_by_signal(signum, frame):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, interrupted_by_signal)
    try:
        process.wait(timeout=opts.seconds)
    except subprocess.TimeoutExpired:
        stop_decoder(process)
    except KeyboardInterrupt:
        interrupted = True
    finally:
        stop_decoder(process)
    if process.returncode != 0 and not interrupted:
        raise SystemExit('Decoder failed with exit code ' + str(process.returncode))
    rows = [json.loads(line) for line in json_path.read_text().splitlines()[before:]
            if line.strip()] if json_path.exists() else []
    print('CAPTURE COMPLETE:', len(rows), 'new messages; decoder exit:', process.returncode, flush=True)
    if rows:
        print('Frequencies:', sorted({row['freq'] for row in rows}), flush=True)
        print('Aircraft:', sorted({row.get('tail', '') for row in rows}), flush=True)

if __name__ == '__main__':
    main()
