#!/bin/bash
set -euo pipefail
acars_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
"$acars_dir/bin/check-sdr"
acars_count="$("$acars_dir/bin/check-sdr" --count)"
if [ "$acars_count" -eq 0 ]; then
    printf '%s\n' 'No RTL-SDR detected. Connect the RTL-SDR Blog V4 to this Mac and try again.'
    exit 1
fi
if [ "$acars_count" -gt 1 ] && [ -z "${SDR_DEVICE:-}" ]; then
    printf '%s\n' 'More than one receiver is attached. Set SDR_DEVICE to the index of your spare receiver.'
    printf '%s\n' 'Example: SDR_DEVICE=1 ./start-acars.command'
    exit 1
fi
mkdir -p "$acars_dir/data"
if [ "$#" -eq 0 ]; then
    set -- 130.025 130.450 130.825 130.850 131.125 131.525 131.550 131.725 131.825 131.850
fi
printf '%s\n' 'Listening for ACARS. Messages will appear below; stop with Control-C.'
printf 'Receiver settings: gain %s dB, correction %s ppm\n' "${ACARS_GAIN:-49.6}" "${ACARS_PPM:-0}"
printf 'JSON data: %s\n' "$acars_dir/data/acars.jsonl (daily rotation enabled)"
exec "$acars_dir/bin/acarsdec" \
    -i "${ACARS_STATION:-MA-ACARS}" \
    --rtlsdr "${SDR_DEVICE:-0}" \
    -g "${ACARS_GAIN:-49.6}" -p "${ACARS_PPM:-0}" \
    --output full:file \
    --output "json:file:path=$acars_dir/data/acars.jsonl,rotate=daily" \
    "$@"
