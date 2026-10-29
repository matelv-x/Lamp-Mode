#!/usr/bin/env python3
from pathlib import Path
import re
import sys


def replace_all(text, old, new):
    return text.replace(old, new)


def remove_pattern(text, pattern, label):
    updated, count = re.subn(pattern, "", text, count=1, flags=re.DOTALL)
    if count:
        print(f"Removed: {label}")
    return updated


def remote_close_signature(text):
    pattern = re.compile(
        r"(?ms)^    def notify_remote_wormhole_close\(.*?"
        r"(?=^    (?:@|def )|^class |\Z)"
    )
    match = pattern.search(text)
    return (
        text.count("self.outgoing_remote_ip"),
        text.count("self.remote_disconnect_sent"),
        match.group(0) if match else None,
    )


def update(path, transform, forbidden=()):
    text = path.read_text()
    protected = (
        remote_close_signature(text)
        if path.name == "stargate.py"
        else None
    )
    updated = transform(text)
    if protected is not None and remote_close_signature(updated) != protected:
        raise RuntimeError(
            f"Refusing to alter authoritative remote-close integration in {path}"
        )
    leftovers = [marker for marker in forbidden if marker in updated]
    if leftovers:
        raise RuntimeError(f"Lamp Mode markers remain in {path}: {leftovers}")
    if updated != text:
        path.write_text(updated)
        print(f"Updated: {path}")
    else:
        print(f"Already clean: {path}")


target = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/pi/sg1_v4")


def unpatch_stargate(text):
    text = remove_pattern(
        text,
        r"\n        # Lamp mode state:[^\n]*\n"
        r"        self\.lamp_mode = False\n"
        r"        self\.lamp_color = \(255, 255, 255\)\n"
        r"        self\.lamp_brightness = 255\n"
        r"        self\.lamp_animation = \"static\"\n"
        r"        self\.lamp_animation_active = False\n"
        r"        self\._lamp_animation_thread = None\n",
        "Stargate lamp state",
    )
    text = remove_pattern(
        text,
        r"\n\n    LAMP_ANIMATIONS = \[.*?"
        r"        self\.log\.log\(f\"Lamp animation thread stopped: \{animation\}\"\)\n",
        "Stargate lamp methods",
    )
    return text


def unpatch_animation(text):
    text = replace_all(
        text,
        'if not self.stargate.wormhole_active and not getattr(self.stargate, "lamp_animation_active", False):  # if the animation is cancelled',
        "if not self.stargate.wormhole_active:  # if the wormhole is cancelled",
    )
    text = replace_all(
        text,
        'while current_pattern != new_pattern and (self.stargate.wormhole_active or getattr(self.stargate, "lamp_animation_active", False)):',
        "while current_pattern != new_pattern and self.stargate.wormhole_active:",
    )
    text = re.sub(
        r'if not self\.stargate\.wormhole_active and not self\.stargate\.lamp_animation_active:'
        r'  # if the wormhole/lamp animation is cancelled',
        'if not self.stargate.wormhole_active:  # if the wormhole is cancelled',
        text,
    )
    text = replace_all(
        text,
        'while current_pattern != new_pattern and (self.stargate.wormhole_active or self.stargate.lamp_animation_active):',
        "while current_pattern != new_pattern and self.stargate.wormhole_active:",
    )
    text = replace_all(
        text,
        '                if not self.stargate.wormhole_active and not getattr(self.stargate, "lamp_animation_active", False):\n'
        "                    return\n",
        "",
    )
    return text


def unpatch_server(text):
    status_pattern = (
        r"                    \"speed_dial_full_address\":\s+self\.stargate\.cfg\.get\('dialing_address_book_dials_full_address'\),\n"
        r"                    \"lamp_mode\":\s+self\.stargate\.lamp_mode,\n"
        r"                    \"lamp_color\":\s+list\(self\.stargate\.lamp_color\),\n"
        r"                    \"lamp_brightness\":\s+self\.stargate\.lamp_brightness,\n"
        r"                    \"lamp_animation\":\s+self\.stargate\.lamp_animation\n"
    )
    text, status_count = re.subn(
        status_pattern,
        '                    "speed_dial_full_address":  self.stargate.cfg.get(\'dialing_address_book_dials_full_address\')\n',
        text,
        count=1,
    )
    if status_count:
        print("Removed: dialing status lamp fields")
    text = remove_pattern(
        text,
        r"            elif request_path == '/get/lamp_status':\n.*?"
        r"            elif request_path == '/get/lamp_animations':\n"
        r"                data = \{\"animations\": self\.stargate\.LAMP_ANIMATIONS\}\n\n",
        "Lamp GET routes",
    )
    text = remove_pattern(
        text,
        r"            elif self\.path == '/do/lamp_on':\n.*?"
        r"(?=            elif self\.path == \"/do/dhd_test_enable\":\n)",
        "Lamp POST routes",
    )
    text = re.sub(
        r'(            elif self\.path == "/do/(?:dynamic_wormhole_on|blackhole_on|wormhole_on|wormhole_off|simulate_incoming|dhd_press|clear_outgoing_buffer)":\n)'
        r'                if self\.stargate\.lamp_mode:\n'
        r'                    self\.stargate\.set_lamp_mode\(False\)\n',
        r"\1",
        text,
    )
    return text


def unpatch_html(text):
    return remove_pattern(
        text,
        r"        <hr />\n(?:[ \t]*\n)*        <h4>LED Strip &mdash; Lamp Mode</h4>.*?"
        r"        <div id=\"lamp_animation_buttons\"[^\n]*></div>\n(?:[ \t]*\n)*",
        "Lamp Mode debug controls",
    )


def unpatch_js(text):
    text = text.replace("  updateLampStatus(data);\n", "")
    return remove_pattern(
        text,
        r"\n\n// Lamp Mode controls[^\n]*\n.*?"
        r"\$\((?:initLampControls|function\(\) \{ initLampControls\(\); \})\);\n",
        "Lamp Mode JavaScript",
    )


update(
    target / "classes/StargateMilkyWay/stargate.py",
    unpatch_stargate,
    ("Lamp mode state:", "LAMP_ANIMATIONS", "def set_lamp_mode"),
)
update(
    target / "classes/StargateMilkyWay/wormhole_animation_manager.py",
    unpatch_animation,
    ("lamp_animation_active",),
)
update(
    target / "classes/web_server.py",
    unpatch_server,
    ("/get/lamp_status", "/do/lamp_on", "self.stargate.lamp_mode"),
)
update(target / "web/debug.htm", unpatch_html, ("lamp_status_bar", "Lamp Mode</h4>"))

# Stellar Archive keeps two copies of the original navigation pages. Clean the
# Lamp Mode block from both when they exist, otherwise a later Archive update or
# uninstall can restore the already removed controls into the active page.
for archive_debug in (
    target / "web/.stellar-archive-addon/managed/original-nav-pages/debug.htm",
    target / "web/.stellar-archive-addon/originals/original-nav-pages/debug.htm",
):
    if archive_debug.is_file():
        update(archive_debug, unpatch_html, ("lamp_status_bar", "Lamp Mode</h4>"))

update(target / "web/js/debug.js", unpatch_js, ("Lamp Mode controls", "updateLampStatus"))
