#!/usr/bin/env bash
set -euo pipefail

TARGET="/home/pi/sg1_v4"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR="$SCRIPT_DIR/files"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      TARGET="$2"
      shift 2
      ;;
    *)
      TARGET="$1"
      shift
      ;;
  esac
done

fail() { echo "ERROR: $1" >&2; exit 1; }

[ -d "$TARGET" ] || fail "Target folder not found: $TARGET"
[ -f "$TARGET/main.py" ] || fail "This does not look like an SG1 app folder: $TARGET"
[ -d "$FILES_DIR" ] || fail "Installer files folder not found: $FILES_DIR"

if ! sudo -n true 2>/dev/null; then
  echo "This installer needs sudo because stargate files may be owned by root."
  sudo true
fi

BACKUP_DIR="$TARGET/backups/lamp-mode-$STAMP"
sudo mkdir -p "$BACKUP_DIR"

backup_file() {
  local rel="$1"
  if [ -e "$TARGET/$rel" ]; then
    sudo mkdir -p "$BACKUP_DIR/$(dirname "$rel")"
    sudo cp -a "$TARGET/$rel" "$BACKUP_DIR/$rel"
  fi
}

sudo systemctl stop stargate.service || true

while IFS= read -r -d '' src; do
  rel="${src#"$FILES_DIR/"}"
  backup_file "$rel"
  sudo mkdir -p "$TARGET/$(dirname "$rel")"
  sudo cp -a "$src" "$TARGET/$rel"
  echo "Installed: $rel"
done < <(find "$FILES_DIR" -type f -print0)

PYBIN="python3"
[ -x /home/pi/venv_v4/bin/python ] && PYBIN="/home/pi/venv_v4/bin/python"
"$PYBIN" -m py_compile \
  "$TARGET/classes/StargateMilkyWay/stargate.py" \
  "$TARGET/classes/StargateMilkyWay/wormhole_animation_manager.py" \
  "$TARGET/classes/web_server.py"

sudo find "$TARGET/classes" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
sudo chown -R pi:pi "$TARGET"
sudo systemctl start stargate.service

echo
echo "=== LAMP MODE INSTALL COMPLETE ==="
echo "Backup folder: $BACKUP_DIR"
