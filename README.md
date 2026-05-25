# Lamp Mode

Adds LED-strip lamp mode animations and debug UI controls.

This repository is private while it is being checked and verified.

## Install

```bash
cd /home/pi/Stargate-Final_Patches
rm -rf Lamp-Mode
git clone https://github.com/matelv-x/Lamp-Mode.git
cd Lamp-Mode
chmod +x *.sh
sudo ./install.sh --target /home/pi/sg1_v4
sudo systemctl restart stargate.service
```

## Restore / uninstall

```bash
cd /home/pi/Stargate-Final_Patches/Lamp-Mode
chmod +x restore.sh
sudo ./restore.sh --target /home/pi/sg1_v4
sudo systemctl restart stargate.service
```

## What it changes

- Adds lamp animations: Static Color, Wormhole Effect, Black Hole and Kawoosh Loop.
- Adds debug UI controls for lamp color, brightness and animation.
- Extends wormhole LED animation code so effects can run outside dialing.

## Attribution and originality

Original base project: StargateProject SG1 software from the BuildAStargate/Jordan/Kristian/Jonnerd project lineage.

Additional source/idea credit: Feature idea by Marcin/Codex, implemented over StargateProject LED/wormhole animation code.

How much is copied or changed: Clean-install overlay. It currently replaces selected base files and should be installed early on a clean SG1 v4 system.

The included `*.patch` file, when present, shows the exact text-level changes against the base software used while packaging.
