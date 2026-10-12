# Project context

This project receives traditional VHF ACARS and stores raw JSON for a future UI.
The active receiver is an RTL-SDR Blog V4 on the Mac Studio M1 Max. The chat
may be viewed on a separate M4 Mac; verify the execution host before testing
USB hardware or changing its software.

Use the existing native decoder bundle under outputs/acars-macos-arm64.
The canonical project interface is the Gradle 9.8.1 wrapper: build,
buildReceiver, checkSdr, receive and capture. Native build tasks and simulated
tests do not open the SDR; hardware tasks are explicit. Preserve logs when
changing build/install/clean tasks. Native caches and staging live under build/.
V4 defaults are 0 ppm, gain 49.6 dB, bias tee off. The older NESDR Mini needs
the previously measured +50 ppm correction. Do not apply that to the V4.

The user confirmed the long dipole elements are installed on October 12.
V4 live reception is verified: a five-minute capture decoded four messages
from N584QS on 131.725 MHz with zero reported parity errors. The test is
stopped. See docs/setup-history.md for details before further testing.
Only one program can own a dongle. Keep the separate Pi ADS-B feed operating.
An existing continuous receiver was observed during the Gradle migration;
check current process ownership before running hardware tasks.

Keep raw reception logs in outputs/acars-macos-arm64/data and out of Git.
These are live received messages; recorded-test-example.jsonl is replay data.
Preserve the original frames when adding interpretation or reassembly.
Do not assign units to proprietary numeric payloads without a matching layout.
Decoder timestamps and daily rotation use UTC; user-facing time is Eastern.

The UI and Pi 4 deployment have not been specified. Read docs/setup-history.md
for the current verification state and next steps. Do not create a new chat,
publish a repository, or schedule a receiver job without a user request.
