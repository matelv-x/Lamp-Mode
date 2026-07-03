# Lamp Mode

[![Downloads](https://img.shields.io/github/downloads/matelv-x/Lamp-Mode/total?label=downloads)](https://github.com/matelv-x/Lamp-Mode/releases)

Clean-install LED strip lamp mode add-on.

## Install

Clone or unzip this add-on into `/home/pi`, then run:

```bash
cd /home/pi
rm -rf Lamp-Mode
git clone https://github.com/matelv-x/Lamp-Mode.git
cd Lamp-Mode
chmod +x install.sh restore.sh
sudo ./install.sh --target /home/pi/sg1_v4
sudo systemctl restart stargate.service
```

## Restore / uninstall

```bash
cd /home/pi/Lamp-Mode
sudo ./restore.sh --target /home/pi/sg1_v4
sudo systemctl restart stargate.service
```

## What it changes

- Adds LED lamp animation controls.
- Applies a surgical overlay, preserving Alarm Clock and other installed add-ons.
- Updates static color and brightness live without an Apply button.
- Applies brightness live to Static Color, Wormhole Effect, Black Hole and Kawoosh Loop.

## Attribution and originality

Original base project: StargateProject SG1 software from the BuildAStargate/Jordan/Kristian/Jonnerd project lineage.

Additional source/idea credit: Feature idea by matelv-x/Codex over StargateProject LED/wormhole animation code.

How much is copied or changed: Clean-install overlay; use carefully on heavily patched live gates.
