"""Stage and relocate a standalone macOS receiver; Gradle owns the build/archive."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
for name in ('decoder', 'probe', 'rtl-prefix', 'homebrew-prefix', 'destination',
             'launcher', 'readme', 'sources-archive', 'acars-source', 'rtl-source'):
    parser.add_argument('--' + name, type=Path, required=True)
parser.add_argument('--developer-dir', required=True)
parser.add_argument('--replay-json', type=Path)
args = parser.parse_args()
bundle = args.destination
env = dict(os.environ, DEVELOPER_DIR=args.developer_dir)

def run(*command):
    return subprocess.check_output(command, env=env, text=True)

files = [
    (args.decoder, 'bin/acarsdec'),
    (args.probe, 'bin/check-sdr'),
    (args.rtl_prefix / 'lib/librtlsdr.0.dylib', 'lib/librtlsdr.0.dylib'),
    (args.homebrew_prefix / 'opt/cjson/lib/libcjson.1.dylib', 'lib/libcjson.1.dylib'),
    (args.homebrew_prefix / 'opt/libusb/lib/libusb-1.0.0.dylib', 'lib/libusb-1.0.0.dylib'),
    (args.launcher, 'start-acars.command'),
    (args.readme, 'README.txt'),
    (args.sources_archive, 'sources.tar.gz'),
    (args.acars_source / 'LICENSE.md', 'licenses/acarsdec.txt'),
    (args.rtl_source / 'COPYING', 'licenses/rtl-sdr.txt'),
    (args.homebrew_prefix / 'opt/cjson/LICENSE', 'licenses/cjson.txt'),
    (args.homebrew_prefix / 'opt/libusb/COPYING', 'licenses/libusb.txt'),
]
for source, relative in files:
    if not source.is_file():
        raise SystemExit('Missing package input: ' + str(source))
    target = bundle / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    shutil.copy2(source, target, follow_symlinks=True)
    target.chmod(0o755 if relative.startswith('bin/') or relative.endswith('.command') else 0o644)

libraries = {'librtlsdr.0.dylib', 'libcjson.1.dylib', 'libusb-1.0.0.dylib'}
for path in list((bundle / 'bin').iterdir()) + list((bundle / 'lib').iterdir()):
    if path.parent.name == 'lib':
        run('/usr/bin/install_name_tool', '-id', '@loader_path/' + path.name, str(path))
    for line in run('/usr/bin/otool', '-L', str(path)).splitlines()[1:]:
        dependency = line.strip().split(' (')[0]
        name = Path(dependency).name
        if name in libraries:
            prefix = '@loader_path/../lib/' if path.parent.name == 'bin' else '@loader_path/'
            run('/usr/bin/install_name_tool', '-change', dependency, prefix + name, str(path))
    run('/usr/bin/codesign', '--force', '--sign', '-', str(path))

if args.replay_json and args.replay_json.is_file():
    rows = [json.loads(line) for line in args.replay_json.read_text().splitlines() if line.strip()]
    if any(row.get('freq') != 0 for row in rows):
        raise SystemExit('Replay input contains radio frequencies; refusing to package live captures.')
    for row in rows:
        row['station_id'] = 'RECORDED-TEST'
    (bundle / 'recorded-test-example.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
print('Staged standalone receiver:', bundle)
