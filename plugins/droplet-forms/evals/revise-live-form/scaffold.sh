#!/usr/bin/env bash
# Builds the fictional Harbor Point "Field Trip Request" from _fixtures/ into inbox/ as an exported .drplt.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p inbox
python3 "$here/../../skills/droplet-form-creator/scripts/build_drplt.py" build \
  "$here/../_fixtures/harbor-point-field-trip" -o "inbox/Field Trip Request.drplt" > /dev/null
