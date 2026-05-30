#!/usr/bin/env python3
from pathlib import Path
import sys


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Could not find insertion point: {label}")
    return text.replace(old, new, 1)


def update(path, transform):
    text = path.read_text()
    updated = transform(text)
    if updated != text:
        path.write_text(updated)
        print(f"Updated: {path}")
    else:
        print(f"Already current: {path}")


target = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/pi/sg1_v4")

lamp_state = """        # Lamp mode state: use the wormhole strip as a live-adjustable light.
        self.lamp_mode = False
        self.lamp_color = (255, 255, 255)
        self.lamp_brightness = 255
        self.lamp_animation = "static"
        self.lamp_animation_active = False
        self._lamp_animation_thread = None
"""

lamp_methods = """

    LAMP_ANIMATIONS = [
        {"id": "static", "name": "Static Color"},
        {"id": "wormhole", "name": "Wormhole Effect"},
        {"id": "black_hole", "name": "Black Hole"},
        {"id": "kawoosh", "name": "Kawoosh Loop"},
    ]
    LAMP_ANIMATION_IDS = {animation["id"] for animation in LAMP_ANIMATIONS}

    def set_lamp_mode(self, state: bool, color=None, brightness=None, animation=None):
        if state:
            if self.wormhole_active:
                self.wormhole_active = False
                sleep(0.3)
            self._stop_lamp_animation()
            self.shutdown(cancel_sound=False, wormhole_fail_sound=False)
            self.lamp_mode = False
            self.lamp_set(color=color, brightness=brightness, animation=animation)
            self.lamp_mode = True
            if self.lamp_animation == "static":
                self._apply_lamp()
            else:
                self._start_lamp_animation()
        else:
            self._stop_lamp_animation()
            self.lamp_mode = False
            self._apply_lamp_brightness(255)
            self.wh_manager.animation_manager.clear_wormhole()
            self.log.log("Lamp mode: OFF")

    def lamp_set(self, color=None, brightness=None, animation=None):
        if color is not None:
            self.lamp_color = tuple(max(0, min(255, int(c))) for c in color)
        if brightness is not None:
            self.lamp_brightness = max(0, min(255, int(brightness)))
        self._apply_lamp_brightness(self.lamp_brightness)

        animation_changed = animation is not None and animation in self.LAMP_ANIMATION_IDS and animation != self.lamp_animation
        if animation_changed:
            self.lamp_animation = animation
            if self.lamp_mode:
                self._stop_lamp_animation()
                if self.lamp_animation == "static":
                    self._apply_lamp()
                else:
                    self._start_lamp_animation()
        elif self.lamp_mode and self.lamp_animation == "static":
            self._apply_lamp()

    def _apply_lamp_brightness(self, brightness):
        pixels = self.wh_manager.animation_manager.pixels
        if hasattr(pixels, "brightness"):
            pixels.brightness = max(0, min(255, int(brightness))) / 255.0
            pixels.show()

    def _apply_lamp(self):
        total_leds = self.wh_manager.animation_manager.tot_leds
        self.wh_manager.animation_manager.set_wormhole_pattern([self.lamp_color] * total_leds)
        self.log.log(f"Lamp mode: ON - color={self.lamp_color}, brightness={self.lamp_brightness}, animation={self.lamp_animation}")

    def _start_lamp_animation(self):
        self.lamp_animation_active = True
        thread = Thread(target=self._run_lamp_animation, daemon=True)
        self._lamp_animation_thread = thread
        thread.start()

    def _stop_lamp_animation(self):
        self.lamp_animation_active = False
        thread = self._lamp_animation_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=0.75)
        self._lamp_animation_thread = None

    def _run_lamp_animation(self):
        manager = self.wh_manager.animation_manager
        animation = self.lamp_animation
        self.log.log(f"Lamp animation thread started: {animation}")
        while self.lamp_animation_active and self.lamp_mode:
            if animation == "wormhole":
                manager.do_random_transitions(is_black_hole=False)
            elif animation == "black_hole":
                manager.do_random_transitions(is_black_hole=True)
            elif animation == "kawoosh":
                manager.animate_kawoosh()
                sleep(0.3)
            else:
                break
        self.log.log(f"Lamp animation thread stopped: {animation}")
"""


def patch_stargate(text):
    text = replace_once(
        text,
        "        self.dhd_test = False\n",
        "        self.dhd_test = False\n\n" + lamp_state,
        "Stargate lamp state",
    )
    if "    LAMP_ANIMATIONS = [" not in text:
        text = text.rstrip() + lamp_methods + "\n"
    text = text.replace(
        "            self.lamp_mode = True\n            self.lamp_set(color=color, brightness=brightness, animation=animation)\n            if self.lamp_animation == \"static\":\n",
        "            self.lamp_mode = False\n            self.lamp_set(color=color, brightness=brightness, animation=animation)\n            self.lamp_mode = True\n            if self.lamp_animation == \"static\":\n",
    )
    return text


def patch_animation(text):
    text = text.replace(
        "if not self.stargate.wormhole_active:  # if the wormhole is cancelled",
        "if not self.stargate.wormhole_active and not getattr(self.stargate, \"lamp_animation_active\", False):  # if the animation is cancelled",
    )
    text = text.replace(
        "while current_pattern != new_pattern and self.stargate.wormhole_active:",
        "while current_pattern != new_pattern and (self.stargate.wormhole_active or getattr(self.stargate, \"lamp_animation_active\", False)):",
    )
    stop_check = """                if not self.stargate.wormhole_active and not getattr(self.stargate, "lamp_animation_active", False):
                    return
"""
    text = replace_once(
        text,
        "            for led in reversed(range(self.tot_leds)):\n                current_pattern[led] = new_pattern[led]\n",
        "            for led in reversed(range(self.tot_leds)):\n" + stop_check + "                current_pattern[led] = new_pattern[led]\n",
        "backwards sweep cancellation",
    )
    text = replace_once(
        text,
        "            for led in range(self.tot_leds):\n                current_pattern[led] = new_pattern[led]\n",
        "            for led in range(self.tot_leds):\n" + stop_check + "                current_pattern[led] = new_pattern[led]\n",
        "forward sweep cancellation",
    )
    return text


status_fields = """                    "speed_dial_full_address":  self.stargate.cfg.get('dialing_address_book_dials_full_address'),
                    "lamp_mode":                self.stargate.lamp_mode,
                    "lamp_color":               list(self.stargate.lamp_color),
                    "lamp_brightness":          self.stargate.lamp_brightness,
                    "lamp_animation":           self.stargate.lamp_animation
"""

get_routes = """            elif request_path == '/get/lamp_status':
                data = {
                    "lamp_mode":       self.stargate.lamp_mode,
                    "color":           list(self.stargate.lamp_color),
                    "brightness":      self.stargate.lamp_brightness,
                    "lamp_animation":  self.stargate.lamp_animation,
                }

            elif request_path == '/get/lamp_animations':
                data = {"animations": self.stargate.LAMP_ANIMATIONS}

"""

post_routes = """            elif self.path == '/do/lamp_on':
                self.stargate.set_lamp_mode(True, color=data.get('color'), brightness=data.get('brightness'), animation=data.get('animation'))
                data = {"success": True, "lamp_mode": True, "color": list(self.stargate.lamp_color), "brightness": self.stargate.lamp_brightness, "lamp_animation": self.stargate.lamp_animation}

            elif self.path == '/do/lamp_off':
                self.stargate.set_lamp_mode(False)
                data = {"success": True, "lamp_mode": False}

            elif self.path == '/do/lamp_set':
                if not self.stargate.lamp_mode:
                    data = {"success": False, "message": "Lamp mode is not active."}
                else:
                    self.stargate.lamp_set(color=data.get('color'), brightness=data.get('brightness'), animation=data.get('animation'))
                    data = {"success": True, "color": list(self.stargate.lamp_color), "brightness": self.stargate.lamp_brightness, "lamp_animation": self.stargate.lamp_animation}

"""


def patch_server(text):
    text = replace_once(
        text,
        "                    \"speed_dial_full_address\":  self.stargate.cfg.get('dialing_address_book_dials_full_address')\n",
        status_fields,
        "dialing status fields",
    )
    text = replace_once(text, '            elif request_path == "/get/config":\n', get_routes + '            elif request_path == "/get/config":\n', "lamp GET routes")
    text = replace_once(text, '            elif self.path == "/do/dhd_test_enable":\n', post_routes + '            elif self.path == "/do/dhd_test_enable":\n', "lamp POST routes")
    for action in ("dynamic_wormhole_on", "blackhole_on", "wormhole_on", "wormhole_off", "simulate_incoming", "dhd_press", "clear_outgoing_buffer"):
        anchor = f'            elif self.path == "/do/{action}":\n'
        guard = anchor + "                if self.stargate.lamp_mode:\n                    self.stargate.set_lamp_mode(False)\n"
        text = replace_once(text, anchor, guard, f"{action} lamp shutdown")
    return text


lamp_html = """        <hr />
        <h4>LED Strip &mdash; Lamp Mode</h4>
        <div id="lamp_status_bar" style="display:flex;align-items:center;gap:14px;margin-bottom:12px;padding:10px 14px;background:#d0d8de;border-radius:6px;flex-wrap:wrap;">
          <span>State:</span><strong id="lamp_state_label">-</strong>
          <span id="lamp_color_swatch" style="display:inline-block;width:28px;height:28px;border:2px solid #555;border-radius:4px;background:#ffffff;"></span>
          <span id="lamp_color_label" style="font-family:monospace;">-</span>
          <span>Brightness:&nbsp;<strong id="lamp_brightness_label">-</strong></span>
          <span>Animation:&nbsp;<strong id="lamp_animation_label">-</strong></span>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:14px;">
          <button type="button" id="lamp_on_btn" class="btn-secondary" style="background-color:#2ecc71;color:#fff;width:180px;">Lamp ON</button>
          <button type="button" id="lamp_off_btn" class="btn-secondary" style="background-color:#c0392b;color:#fff;width:180px;">Lamp OFF</button>
        </div>
        <div style="display:flex;flex-wrap:wrap;align-items:center;gap:20px;margin-bottom:14px;padding:12px 14px;background:#d0d8de;border-radius:6px;">
          <label style="margin:0;font-weight:bold;display:flex;align-items:center;gap:8px;">Color:<input type="color" id="lamp_color_picker" value="#ffffff" style="cursor:pointer;width:48px;height:36px;border:none;padding:0;background:none;"></label>
          <label style="margin:0;font-weight:bold;display:flex;align-items:center;gap:8px;">Brightness:<input type="range" id="lamp_brightness_slider" min="0" max="255" value="255" style="width:160px;"><span id="lamp_brightness_value" style="font-family:monospace;min-width:36px;text-align:right;">255</span></label>
        </div>
        <div style="margin-bottom:8px;font-weight:bold;">Animation:</div>
        <div id="lamp_animation_buttons" style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:6px;"></div>

"""


def patch_html(text):
    return replace_once(text, "        <hr />\n        <h4>Wormhole Manual Control</h4>\n", lamp_html + "        <hr />\n        <h4>Wormhole Manual Control</h4>\n", "Lamp Mode HTML")


lamp_js = r"""

// Lamp Mode controls: color and brightness update live, without an Apply button.
var _lampAnimations = [];
var _activeAnimationId = 'static';
var _lampLiveTimer = null;
var _lampBrightnessDragging = false;
function lampHexToRgb(hex) { return [parseInt(hex.slice(1,3),16), parseInt(hex.slice(3,5),16), parseInt(hex.slice(5,7),16)]; }
function lampRgbToHex(rgb) { return '#' + rgb.map(function(v) { return ('0' + Math.max(0,Math.min(255,v)).toString(16)).slice(-2); }).join(''); }
function refreshLampButtons() {
  $('#lamp_animation_buttons button').each(function() {
    var active = $(this).data('anim-id') === _activeAnimationId;
    $(this).css(active ? {'background-color':'#2980b9','color':'#fff'} : {'background-color':'#e0e0e0','color':'#000'});
  });
}
function updateLampStatus(data) {
  if (!data || data.lamp_mode === undefined) return;
  var color = data.lamp_color || data.color || [255,255,255];
  var brightness = data.lamp_brightness !== undefined ? data.lamp_brightness : data.brightness;
  _activeAnimationId = data.lamp_animation || _activeAnimationId;
  $('#lamp_state_label').text(data.lamp_mode ? 'ON' : 'OFF').css('color', data.lamp_mode ? '#27ae60' : '#c0392b');
  $('#lamp_color_swatch').css('background-color', lampRgbToHex(color));
  $('#lamp_color_label').text(lampRgbToHex(color) + ' (' + color.join(', ') + ')');
  $('#lamp_brightness_label').text(brightness);
  if (!$('#lamp_color_picker').is(':focus')) $('#lamp_color_picker').val(lampRgbToHex(color));
  if (!_lampBrightnessDragging) $('#lamp_brightness_slider').val(brightness);
  $('#lamp_brightness_value').text(brightness);
  var name = _activeAnimationId;
  $.each(_lampAnimations, function(_, a) { if (a.id === _activeAnimationId) name = a.name; });
  $('#lamp_animation_label').text(name);
  refreshLampButtons();
}
function lampPayload(extra) {
  return $.extend({color:lampHexToRgb($('#lamp_color_picker').val()), brightness:parseInt($('#lamp_brightness_slider').val(),10), animation:_activeAnimationId}, extra || {});
}
function sendLampOn(extra) {
  $.ajax({url:'stargate/do/lamp_on',type:'POST',contentType:'application/json',data:JSON.stringify(lampPayload(extra))}).done(updateLampStatus);
}
function sendLampOff() {
  $.ajax({url:'stargate/do/lamp_off',type:'POST',contentType:'application/json',data:'{}'}).done(function() { $.get('stargate/get/dialing_status').done(updateLampStatus); });
}
function sendLampSet(extra) {
  $.ajax({url:'stargate/do/lamp_set',type:'POST',contentType:'application/json',data:JSON.stringify(lampPayload(extra))}).done(function(data) {
    if (data.success === false) sendLampOn(extra);
    else updateLampStatus($.extend({lamp_mode:true}, data));
  });
}
function queueLampLiveUpdate() {
  clearTimeout(_lampLiveTimer);
  _lampLiveTimer = setTimeout(function() { sendLampSet(); }, 120);
}
function initLampControls() {
  $.get('stargate/get/lamp_animations').done(function(data) {
    _lampAnimations = data.animations || [];
    $.each(_lampAnimations, function(_, anim) {
      $('<button type="button"></button>').text(anim.name).data('anim-id',anim.id).css({padding:'6px 16px',border:'2px solid #aaa','border-radius':'4px',cursor:'pointer',height:'40px'}).click(function() {
        _activeAnimationId = anim.id; refreshLampButtons(); sendLampSet({animation:anim.id});
      }).appendTo('#lamp_animation_buttons');
    });
    refreshLampButtons();
  });
  $.get('stargate/get/dialing_status').done(updateLampStatus);
  $('#lamp_on_btn').click(function(){ sendLampOn(); });
  $('#lamp_off_btn').click(sendLampOff);
  $('#lamp_color_picker').on('input change', queueLampLiveUpdate);
  $('#lamp_brightness_slider').on('input', function(){ _lampBrightnessDragging=true; $('#lamp_brightness_value').text($(this).val()); queueLampLiveUpdate(); });
  $('#lamp_brightness_slider').on('change', function(){ _lampBrightnessDragging=false; queueLampLiveUpdate(); });
}
$(initLampControls);
"""


def patch_js(text):
    if "// Lamp Mode controls: color and brightness update live" not in text:
        text = text.rstrip() + lamp_js + "\n"
    text = replace_once(text, "  poll_delay = poll_delay_default\n", "  poll_delay = poll_delay_default\n  updateLampStatus(data);\n", "poll lamp status")
    text = text.replace(
        "$.ajax({url:'stargate/do/lamp_off',type:'POST',contentType:'application/json',data:'{}'}).done(function(data) { updateLampStatus($.extend({lamp_mode:false},data)); });",
        "$.ajax({url:'stargate/do/lamp_off',type:'POST',contentType:'application/json',data:'{}'}).done(function() { $.get('stargate/get/dialing_status').done(updateLampStatus); });",
    )
    return text


update(target / "classes/StargateMilkyWay/stargate.py", patch_stargate)
update(target / "classes/StargateMilkyWay/wormhole_animation_manager.py", patch_animation)
update(target / "classes/web_server.py", patch_server)
update(target / "web/debug.htm", patch_html)
update(target / "web/js/debug.js", patch_js)
