#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-/home/pi/sg1_v4}"
if [[ "$TARGET" == "--target" ]]; then
  TARGET="${2:-/home/pi/sg1_v4}"
fi

fail() { echo "ERROR: $1" >&2; exit 1; }

[ -d "$TARGET" ] || fail "Target folder not found: $TARGET"

if ! sudo -n true 2>/dev/null; then
  echo "This restore needs sudo because stargate files may be owned by root."
  sudo true
fi

BACKUP="$(ls -dt "$TARGET"/backups/lamp-mode-* 2>/dev/null | head -n 1 || true)"
[ -n "$BACKUP" ] || fail "No Lamp Mode backup found in $TARGET/backups"
[ -d "$BACKUP" ] || fail "Backup folder does not exist: $BACKUP"

echo "Restoring Lamp Mode files from:"
echo "  $BACKUP"

sudo systemctl stop stargate.service || true

while IFS= read -r -d '' src; do
  rel="${src#"$BACKUP/"}"
  sudo mkdir -p "$TARGET/$(dirname "$rel")"
  sudo rm -rf "$TARGET/$rel"
  sudo cp -a "$src" "$TARGET/$rel"
  echo "Restored: $rel"
done < <(find "$BACKUP" -type f -print0)

sudo find "$TARGET/classes" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
sudo chown -R pi:pi "$TARGET"
sudo systemctl start stargate.service

echo "=== LAMP MODE RESTORE COMPLETE ==="
