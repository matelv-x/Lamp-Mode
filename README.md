# Lamp Mode

Clean-install LED strip lamp mode add-on.

This repository is private while it is being checked and verified.

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
- Overwrites selected base files.
- Best installed after first boot and before other add-ons.

## Attribution and originality

Original base project: StargateProject SG1 software from the BuildAStargate/Jordan/Kristian/Jonnerd project lineage.

Additional source/idea credit: Feature idea by Marcin/Codex over StargateProject LED/wormhole animation code.

How much is copied or changed: Clean-install overlay; use carefully on heavily patched live gates.
