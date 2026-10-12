#!/bin/bash
set -euo pipefail
acars_base="$(cd -- "$(dirname -- "$0")" && pwd)"
acars_project="$(cd -- "$acars_base/../.." && pwd)"
exec "$acars_project/gradlew" -p "$acars_project" buildReceiver "$@"
