# Setup history and continuation

## Objective

Receive ACARS using a spare SDR, preserve useful JSON, and eventually build
a separate UI. A spare Raspberry Pi 4 may become the permanent receiver.
The existing Pi 5 / NESDR / Flightradar24 ADS-B feed is a separate setup.
The receiving area is Massachusetts, near KBED, KBOS, and KFIT.

## Host

Commands in the original chat executed on the user's Mac Studio M1 Max,
although the user was viewing the chat from an M4 Mac. The Mac Studio's
selected full Xcode reported an unaccepted license. Its standalone tools
under /Library/Developer/CommandLineTools compiled successfully using a
per-command DEVELOPER_DIR override. No license was accepted on the user's
behalf, and the global developer-directory selection was not changed.

## Decoder and driver

- acarsdec: cbaa28c4173fc1529a01ab50708e29d12d09a644 from f00b4r0/acarsdec.
- rtl-sdr: 797f8143266d983c56d8f35d2d442527529dd8a5 from osmocom/rtl-sdr.
- The driver includes Blog V4 detection, R828D clock handling and input switching.
- JSON and RTL input are enabled. libacars, MQTT and other SDR inputs are omitted
  from the compact live build. A separate WAV-enabled build validated the
  upstream recording: seven messages, all with zero reported parity errors.
- The Mac patch supplies HOST_NAME_MAX, replaces deprecated -Ofast with
  -O3 -ffast-math, and obtains the version from the source checkout.
- Bundled libraries resolve relative to the executable. Relocation to a
  folder containing spaces was checked, and ad-hoc signatures were verified.

## NESDR Mini verification, October 11

The Mini was initially absent from the USB inventory. It became visible
during troubleshooting after the user was asked to bypass a hub.
The first ACARS test at 0 ppm yielded no messages. Spectrum measurements
showed a frequency offset; +50 ppm aligned the local weather broadcasts.
At gain 40.2 dB and +50 ppm, a bounded ACARS test received N558NN / OH5441
on 131.550 MHz with zero reported parity errors. Later continuous reception
produced more messages on several channels; those logs are preserved.

## RTL-SDR Blog V4 verification, October 12

The user replaced the NESDR Mini with a Blog V4 and attached the RTL-SDR
telescopic dipole. No competing SDR program was found before testing.
The driver reported RTLSDRBlog / Blog V4, serial 00000001, Rafael R828D,
and "RTL-SDR Blog V4 Detected".

At 0 ppm, weather-spectrum peaks were near their expected channels:
162.475 MHz (-122 Hz), 162.525 MHz (-74 Hz), 162.550 MHz (-171 Hz).
These are approximate FFT measurements, not precision oscillator calibration.
Keep the V4 correction at 0 ppm as the starting setting.

The initial V4 ACARS test monitored ten channels at gain 40.2 dB and 0 ppm.
It was interrupted for installation of the longer antenna elements and had
decoded no messages. The test exited cleanly; the receiver is not running.
The user confirmed the longer elements are installed, approximately 55 cm
per arm and arranged vertically. A fresh bounded V4 capture was then started
from the dedicated project folder.

The long dipole was confirmed to be near a window. A three-minute capture at
40.2 dB decoded no messages. A subsequent five-minute capture at 49.6 dB and
0 ppm decoded four live messages from N584QS on 131.725 MHz: labels QR, 10,
QS and 5V, all with zero reported parity errors. The decoder extracted
airport-status fields, and the label 10 body contained a position report.
The original JSON is in data/acars-v4-highgain-20261012.jsonl inside the bundle.
The receiver test exited cleanly and is stopped.

The saved V4 gain is now 49.6 dB because that setting was demonstrated to
work. These separate captures do not establish that gain caused the earlier
quiet results or that 49.6 dB is optimal. Historical logs show long gaps in
ACARS traffic. Keep 0 ppm as the starting frequency correction.

## Next work

1. V4 live ACARS verification is complete; use the launcher for continuous
   reception when requested.
2. If reception becomes quiet, inspect antenna placement, gain, and actual
   channel activity before changing the previously verified frequency offset.
3. Keep the ten currently configured channels unless local evidence justifies
   another choice: 130.025, 130.450, 130.825, 130.850, 131.125, 131.525,
   131.550, 131.725, 131.825, 131.850 MHz.
4. Plan the UI with the user. Raw headers are available now; proprietary
   reports need full block reassembly and matching report layouts.

## Dedicated project

The user added /Users/gmills/Development/GIT/acars-receiver as a project and
moved this chat into it on October 12, 2026. The current working directory
and Mac Studio M1 Max execution host were verified after the move.
The source, settings, and 195 received JSON messages were preserved. A fresh
build from this folder passed, and the packaged library paths and signatures
were verified. The old chat-workspace launcher delegates to this project.

## Gradle migration

The project now follows the pidex Groovy Gradle task structure. Gradle and
the generated wrapper are pinned to 9.8.1, with official distribution and
wrapper JAR checksums. Native configuration, compilation, driver installation,
staging, signature verification, bundle installation and archives are distinct
tasks. Pinned source revisions remain unchanged.

Use ./gradlew build for the full software workflow, ./gradlew receive for
continuous reception, ./gradlew capture for a bounded test, and ./gradlew
checkSdr for enumeration. Hardware tasks are not dependencies of build/check.
Small platform helpers handle Mach-O relocation/signing, verification and
graceful bounded process shutdown. Legacy shell entry points delegate to Gradle.

Native sources and caches are now Gradle-owned under build/. Source and receiver
archives exclude Git metadata and live logs. Bundle installation replaces only
the declared program files atomically; existing data and active file handles
are preserved. The portable bundle retains a Java-independent launcher.

Verification passed for a fresh native build, a clean/rebuild cycle, and an
offline incremental build. Unchanged native compilation, staging, verification
and installation tasks were skipped. All five simulated capture lifecycle
tests passed. The official Gradle 9.8.1 wrapper checksum matched, and the wrapper
also launched successfully on the Mac's installed Java 26 runtime.

All seven existing capture files retained their original bytes, allowing new
messages to append. A held executable file descriptor retained its bytes across
atomic installation. The running user receiver process remained alive; no live
hardware capture was started by the software verification tasks. The receiver
archive was checked to contain no JSON reception logs.
