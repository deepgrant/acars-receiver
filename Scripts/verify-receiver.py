"""Verify a staged macOS bundle without enumerating or opening radio devices."""
import argparse
import os
from pathlib import Path
import subprocess
import tarfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('bundle', type=Path)
parser.add_argument('--developer-dir', required=True)
args = parser.parse_args()
env = dict(os.environ, DEVELOPER_DIR=args.developer_dir)
bundle = args.bundle
for path in list((bundle / 'bin').iterdir()) + list((bundle / 'lib').iterdir()):
    subprocess.run(['/usr/bin/codesign', '--verify', '--strict', str(path)], env=env, check=True)
    dependencies = subprocess.check_output(['/usr/bin/otool', '-L', str(path)], env=env, text=True)
    for line in dependencies.splitlines()[1:]:
        dependency = line.strip().split(' (')[0]
        if dependency.startswith('@loader_path/'):
            target = path.parent / dependency.removeprefix('@loader_path/')
            if not target.is_file():
                raise SystemExit('Missing bundled dependency: ' + str(target))
        elif not dependency.startswith(('/usr/lib/', '/System/Library/')):
            raise SystemExit('Nonportable dependency: ' + dependency)
subprocess.run(['/bin/bash', '-n', str(bundle / 'start-acars.command')], check=True)
result = subprocess.run([str(bundle / 'bin/acarsdec'), '--output', 'help'], capture_output=True, text=True)
if '"json"' not in result.stderr:
    raise SystemExit('Decoder JSON output is unavailable: ' + result.stderr)
with tarfile.open(bundle / 'sources.tar.gz') as archive:
    if any('.git' in Path(name).parts for name in archive.getnames()):
        raise SystemExit('Source archive includes Git metadata.')
if (bundle / 'data').exists():
    raise SystemExit('Staged distribution must not contain live reception data.')
print('Verified signatures, portable libraries, JSON support, launcher, and source archive.')
