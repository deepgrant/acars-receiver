"""Capture lifecycle tests use fake executables, never the USB receiver."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CAPTURE = Path(__file__).resolve().parents[1] / 'Scripts/capture-acars.py'

class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='acars-capture-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.probe = self.root / 'probe'
        self.probe.write_text('#!' + sys.executable + '\nimport os\nprint(os.environ.get("ACARS_TEST_DEVICE_COUNT", "1"))\n')
        self.probe.chmod(0o755)
        self.decoder = self.root / 'decoder'
        self.decoder.write_text('#!' + sys.executable + '''
import json, os, signal, sys, time
from pathlib import Path
args = sys.argv[1:]
Path(os.environ['ACARS_TEST_ARGUMENTS']).write_text(json.dumps(args))
mode = os.environ.get('ACARS_TEST_MODE', 'normal')
if mode == 'failure':
    sys.exit(7)
out = next(a.split('json:file:path=', 1)[1] for a in args if a.startswith('json:file:path='))
def emit():
    with open(out, 'a') as file:
        file.write(json.dumps({'freq': 131.55, 'tail': 'TEST', 'error': 0}) + '\\n')
def stop(signum, frame):
    Path(os.environ['ACARS_TEST_STOPPED']).write_text('graceful')
    emit()
    sys.exit(0)
signal.signal(signal.SIGINT, stop)
if mode == 'wait':
    while True:
        time.sleep(0.1)
emit()
''')
        self.decoder.chmod(0o755)
        self.env = dict(os.environ,
            ACARS_TEST_ARGUMENTS=str(self.root / 'arguments.json'),
            ACARS_TEST_STOPPED=str(self.root / 'stopped'))

    def capture(self, *extra, mode='normal', count='1'):
        env = dict(self.env, ACARS_TEST_MODE=mode, ACARS_TEST_DEVICE_COUNT=count)
        command = [sys.executable, str(CAPTURE), '--decoder', str(self.decoder),
            '--probe', str(self.probe), '--data-dir', str(self.root / 'data'),
            '--name', 'fixture', '--seconds', '1', *extra, '131.550']
        return subprocess.run(command, env=env, capture_output=True, text=True, timeout=15)

    def test_normal_capture_preserves_existing_rows_and_forwards_settings(self):
        data = self.root / 'data'
        data.mkdir()
        old = json.dumps({'freq': 130.45, 'tail': 'OLD', 'error': 0}) + '\n'
        (data / 'fixture.jsonl').write_text(old)
        result = self.capture('--gain', '40.2', '--ppm', '50', '--station', 'TEST-STATION')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('1 new messages', result.stdout)
        self.assertTrue((data / 'fixture.jsonl').read_text().startswith(old))
        arguments = json.loads((self.root / 'arguments.json').read_text())
        self.assertEqual(arguments[arguments.index('-g') + 1], '40.2')
        self.assertEqual(arguments[arguments.index('-p') + 1], '50')
        self.assertEqual(arguments[arguments.index('-i') + 1], 'TEST-STATION')

    def test_timeout_stops_the_owned_decoder_gracefully(self):
        result = self.capture(mode='wait')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / 'stopped').read_text(), 'graceful')
        self.assertIn('1 new messages', result.stdout)

    def test_decoder_failure_is_not_reported_as_a_successful_capture(self):
        result = self.capture(mode='failure')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('exit code 7', result.stderr)
        self.assertNotIn('CAPTURE COMPLETE', result.stdout)

    def test_multiple_receivers_require_explicit_selection(self):
        result = self.capture(count='2')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Multiple receivers', result.stderr)
        self.assertFalse((self.root / 'arguments.json').exists())
        result = self.capture('--device', '1', count='2')
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments = json.loads((self.root / 'arguments.json').read_text())
        self.assertEqual(arguments[arguments.index('--rtlsdr') + 1], '1')

    def test_invalid_duration_is_rejected_before_opening_a_receiver(self):
        result = self.capture('--seconds', '0')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / 'arguments.json').exists())

if __name__ == '__main__':
    unittest.main()
