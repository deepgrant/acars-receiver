#!/bin/bash
set -euo pipefail
acars_project="$(cd -- "$(dirname -- "$0")" && pwd)"
exec "$acars_project/outputs/acars-macos-arm64/start-acars.command" "$@"
