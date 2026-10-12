ACARS receiver for Apple Silicon Macs (macOS 15 or newer)

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
  https://github.com/DaveGamble/cJSON
  https://github.com/libusb/libusb
License texts are in licenses/. The ACARS and RTL-SDR source snapshots,
including the small Mac build adjustments, are in sources.tar.gz.
