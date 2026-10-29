#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-/home/pi/sg1_v4}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$TARGET" == "--target" ]]; then
  TARGET="${2:-/home/pi/sg1_v4}"
fi

fail() { echo "ERROR: $1" >&2; exit 1; }

[ -d "$TARGET" ] || fail "Target folder not found: $TARGET"

if ! sudo -n true 2>/dev/null; then
  echo "This restore needs sudo because stargate files may be owned by root."
  sudo true
fi

[ -f "$SCRIPT_DIR/uninstall_overlay.py" ] || fail "Overlay uninstaller not found: $SCRIPT_DIR/uninstall_overlay.py"

echo "Removing only Lamp Mode integration blocks."

if [ "${STARGATE_ADDON_NO_RESTART:-0}" != "1" ]; then
  sudo systemctl stop stargate.service || true
  trap 'sudo systemctl start stargate.service >/dev/null 2>&1 || true' EXIT
fi

PYBIN="python3"
[ -x /home/pi/venv_v4/bin/python ] && PYBIN="/home/pi/venv_v4/bin/python"
sudo "$PYBIN" "$SCRIPT_DIR/uninstall_overlay.py" "$TARGET"
"$PYBIN" -m py_compile \
  "$TARGET/classes/StargateMilkyWay/stargate.py" \
  "$TARGET/classes/StargateMilkyWay/wormhole_animation_manager.py" \
  "$TARGET/classes/web_server.py"

sudo find "$TARGET/classes" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
sudo chown -R pi:pi "$TARGET"
if [ "${STARGATE_ADDON_NO_RESTART:-0}" != "1" ]; then
  sudo systemctl start stargate.service
  trap - EXIT
else
  echo "Stargate restart deferred by add-on manager."
fi

echo "=== LAMP MODE RESTORE COMPLETE ==="
