from pathlib import Path
import os
import shutil
import subprocess
import tarfile
import json

base = Path(__file__).resolve().parent
workspace = base.parent.parent
bundle = workspace / 'outputs' / 'acars-macos-arm64'
(bundle / 'bin').mkdir(parents=True, exist_ok=True)
(bundle / 'lib').mkdir(exist_ok=True)
(bundle / 'licenses').mkdir(exist_ok=True)
env = dict(os.environ, DEVELOPER_DIR='/Library/Developer/CommandLineTools')
live_binary = base/'build-macos/acars/acarsdec'
if not live_binary.exists():
    live_binary = base/'live-build/acarsdec'

def run(*args):
    return subprocess.check_output(args, env=env, text=True)

for source, dest in [
    (live_binary, bundle/'bin/acarsdec'),
    (base/'check-sdr', bundle/'bin/check-sdr'),
    (base/'runtime/lib/librtlsdr.0.dylib', bundle/'lib/librtlsdr.0.dylib'),
    (Path('/opt/homebrew/opt/cjson/lib/libcjson.1.dylib'), bundle/'lib/libcjson.1.dylib'),
    (Path('/opt/homebrew/opt/libusb/lib/libusb-1.0.0.dylib'), bundle/'lib/libusb-1.0.0.dylib'),
    (base/'start-acars.command', bundle/'start-acars.command'),
    (base/'acarsdec/LICENSE.md', bundle/'licenses/acarsdec.txt'),
    (base/'rtl-sdr/COPYING', bundle/'licenses/rtl-sdr.txt'),
    (Path('/opt/homebrew/opt/cjson/LICENSE'), bundle/'licenses/cjson.txt'),
    (Path('/opt/homebrew/opt/libusb/COPYING'), bundle/'licenses/libusb.txt'),
]:
    if dest.exists():
        dest.unlink()
    shutil.copy2(source, dest, follow_symlinks=True)

# Make all bundled dependencies resolve relative to this folder.
files = list((bundle/'bin').iterdir()) + list((bundle/'lib').iterdir())
for path in files:
    if path.parent.name == 'lib':
        run('/usr/bin/install_name_tool', '-id', '@loader_path/'+path.name, str(path))
    lines = run('/usr/bin/otool', '-L', str(path)).splitlines()[1:]
    for line in lines:
        dependency = line.strip().split(' (')[0]
        name = Path(dependency).name
        if name in {'librtlsdr.0.dylib','libcjson.1.dylib','libusb-1.0.0.dylib'}:
            prefix = '@loader_path/../lib/' if path.parent.name == 'bin' else '@loader_path/'
            run('/usr/bin/install_name_tool', '-change', dependency, prefix+name, str(path))
    run('/usr/bin/codesign', '--force', '--sign', '-', str(path))

(bundle/'start-acars.command').chmod(0o755)
replay_capture = base/'decoded-test.jsonl'
if replay_capture.exists():
    rows = [json.loads(line) for line in replay_capture.read_text().splitlines()]
    for row in rows:
        row['station_id'] = 'RECORDED-TEST'
    (bundle/'recorded-test-example.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))

(bundle/'README.txt').write_text('''ACARS receiver for Apple Silicon Macs (macOS 15 or newer)

Connect the RTL-SDR Blog V4 and its VHF antenna to the Mac that will run
the decoder. Close SDRangel, SDR++, Gqrx or another program
using that same dongle. Keep the Pi ADS-B receiver running.

In Terminal, cd to this extracted folder, then run:
  ./bin/check-sdr
  ./start-acars.command

The launcher monitors 130.025, 130.450, 130.825, 130.850, 131.125,
131.525, 131.550, 131.725, 131.825 and 131.850 MHz together,
prints decoded messages and records JSON lines under data/. The decoder
adds a date suffix when daily rotation is enabled. Stop with Control-C.
For a single-channel test:
  ./start-acars.command 131.550

If multiple dongles are connected, select the spare device explicitly:
  SDR_DEVICE=1 ./start-acars.command

Optional receiver adjustments:
  ACARS_GAIN=28 ACARS_PPM=0 ./start-acars.command
The defaults for your RTL-SDR Blog V4 are gain 49.6 dB and frequency
correction 0 ppm. A receive-only check on October 12, 2026 confirmed V4
driver detection and closely aligned local weather broadcasts at 0 ppm.
A five-minute live test with the longer dipole at these settings decoded
four messages from N584QS on 131.725 MHz with zero reported parity errors.
49.6 dB is a tested starting setting, not a measured optimum. Separate
quiet captures at 40.2 dB do not establish that lower gain cannot work.
The driver bundled here includes V4-specific support. The V4 has a TCXO;
do not apply the old NESDR Mini's +50 ppm correction to it.

If you reconnect the previously calibrated NESDR Mini, use:
  ACARS_PPM=50 ./start-acars.command
The +50 ppm correction is specific to that Mini, not a general RTL setting.

For the RTL-SDR telescopic dipole, use the long elements, approximately
55 cm per arm, arranged vertically with one element up and the other
down. Place it near a clear window and away from the computer. The bias
tee stays off for this passive antenna. A 1090 MHz ADS-B antenna is not
the appropriate tuned antenna for these VHF channels.

An empty screen means no message has decoded yet. ADS-B reception from
an aircraft does not guarantee it is transmitting traditional VHF ACARS.

When present, recorded-test-example.jsonl contains messages decoded from
the upstream test recording. It is sample data, NOT reception from Boston;
the timestamps were generated during replay and freq=0 is expected.
This optional replay capture is not required to build or run the receiver.
The compact live executable omits WAV input and optional libacars/MQTT.
It supports text and JSON file output and UDP output.

No Homebrew or Xcode installation is needed to run these bundled binaries.
They are locally built and ad-hoc signed, not Apple-notarized. If macOS
blocks the downloaded build, inspect the warning and use the standard
Privacy & Security "Open Anyway" option for this build if you trust it.

Sources and licenses:
  https://github.com/f00b4r0/acarsdec
  https://github.com/osmocom/rtl-sdr
  https://github.com/DaveGamble/cJSON/tree/v1.7.18
  https://github.com/libusb/libusb/tree/v1.0.28
License texts are in licenses/. The ACARS and RTL-SDR source snapshots,
including the small Mac build adjustments, are in sources.tar.gz.
''')

with tarfile.open(bundle/'sources.tar.gz', 'w:gz') as archive:
    def source_filter(info):
        return None if '/.git' in info.name else info
    archive.add(base/'acarsdec', arcname='acarsdec', filter=source_filter)
    archive.add(base/'rtl-sdr', arcname='rtl-sdr', filter=source_filter)
    archive.add(base/'check-sdr.c', arcname='check-sdr.c')

with tarfile.open(workspace/'outputs/acars-macos-arm64.tar.gz', 'w:gz') as archive:
    archive.add(bundle, arcname=bundle.name)
print('Packaged:', bundle)
