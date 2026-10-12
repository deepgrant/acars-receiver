#!/bin/bash
set -euo pipefail
acars_project="$(cd -- "$(dirname -- "$0")" && pwd)"
if [ "$#" -gt 0 ]; then
    exec "$acars_project/gradlew" -p "$acars_project" receive "-Pfrequencies=$*"
fi
exec "$acars_project/gradlew" -p "$acars_project" receive
