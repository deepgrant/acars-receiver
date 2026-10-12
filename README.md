# ACARS Receiver

Receive traditional VHF ACARS with an RTL-SDR on the Mac Studio M1 Max,
preserve the decoded JSON, and later build a UI around it. The Raspberry Pi
ADS-B feed continues as a separate receiver.

## Run

The local setup already has the native bundle. For a new GitHub checkout,
build it first using the dependencies listed below:

```bash
git clone https://github.com/deepgrant/acars-receiver.git
cd acars-receiver
./work/acars-macos/build-macos.sh
```

Then start reception:

```bash
./start-acars.command
```

The launcher monitors ten channels between 130.025 and 131.850 MHz. It displays
messages in Terminal and appends JSON to
`outputs/acars-macos-arm64/data/acars_YYYYMMDD.jsonl`. Rotation and decoder
timestamps use UTC. Stop with Control-C.

The current receiver is the RTL-SDR Blog V4 with its telescopic dipole.
Defaults: **0 ppm correction, 49.6 dB gain, bias tee off**. Use the long antenna
elements, about 55 cm per arm, arranged vertically near a window.

For the previously calibrated Nooelec NESDR Mini:

```bash
ACARS_PPM=50 ./start-acars.command
```

The +50 ppm setting belongs to that particular Mini. If multiple dongles are
attached, set `SDR_DEVICE` to the intended receiver's index. A single-channel
test can be run with `./start-acars.command 131.550`.

## Current status

- The NESDR Mini successfully decoded live ACARS on October 11, 2026.
- The V4 driver recognizes the Blog V4 and R828D tuner correctly.
- Weather-broadcast checks on October 12 showed close alignment at 0 ppm.
- A five-minute V4 test with the longer dipole decoded four live messages
  from N584QS on 131.725 MHz, all with zero reported parity errors. These
  include airport-status and position messages. The test stopped cleanly.
- The saved gain is a tested starting setting; it has not been optimized
  through a controlled comparison with lower gain.
- A UI, database, VDL2 receiver, and dedicated Pi 4 deployment are still TBD.

## Files

- `start-acars.command`: entry point for continuous reception.
- `work/acars-macos/start-acars.command`: portable bundle launcher source.
- `work/acars-macos/live-test.py`: bounded capture and JSON verification.
- `work/acars-macos/build-macos.sh`: rebuild and package on Apple Silicon.
- `work/acars-macos/package.py`: bundle executable, libraries, and licenses.
- `work/acars-macos/acarsdec-macos.patch`: small macOS source adjustments.
- `outputs/acars-macos-arm64/`: runnable bundle and captured data.
- `docs/setup-history.md`: hardware, verification results, and remaining work.

Compiled binaries, build caches, upstream clones, and reception logs are
preserved locally and ignored by Git. Builds do not depend on the optional
local replay JSON capture. The original chat workspace remains a
backup; its launcher delegates to this project after migration.

## Build

The bundled executable runs without Xcode or Homebrew. Rebuilding requires
Apple Silicon Command Line Tools and Homebrew's `cmake`, `pkg-config`,
`libusb`, `cjson`, and `libsndfile` (for the optional replay build).

```bash
./work/acars-macos/build-macos.sh
```

Upstream revisions are pinned in the script. Missing source checkouts are
downloaded; existing modified checkouts are preserved. The new build uses
fresh build directories because the copied original CMake caches contain
paths to the chat workspace. The runtime target is macOS 15 or newer.

Upstream projects:
[acarsdec](https://github.com/f00b4r0/acarsdec),
[rtl-sdr](https://github.com/osmocom/rtl-sdr).
Their licenses and source snapshots are included in the portable bundle.
