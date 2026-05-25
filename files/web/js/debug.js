function poll_success(singleShot, data){
  // Hide the offline modal
  hideOfflineModal()

  poll_delay = poll_delay_default
  updateLampStatus(data);

  // Schedule the next polling
  if ( !singleShot ){
    setTimeout(function(){doPoll( false ); }, poll_delay);
  }
}

function initialize_button_handlers(){
  $('.debug_button_container .cycleChevronButton').click(function() {
      const chevron_number = $(this).attr('chevron_number');

      $.post({
          url: 'stargate/do/chevron_cycle',
          data: JSON.stringify({
              chevron_number: chevron_number
          })
      })
      .fail(function() {
          console.log("Failed to communicate with Stargate")
          $("<div>Failed to communicate with Stargate</div>").dialog();
      });
  });

  $('.debug_button_container .controlButton').click(function() {
      const action = $(this).attr('action');

      $.post({
          url: 'stargate/do/' + action,
      })
      .fail(function() {
          console.log("Failed to communicate with Stargate")
          $("<div>Failed to communicate with Stargate</div>").dialog();
      });
  });
}


// Lamp Mode controls
var _lampAnimations = [];
var _activeAnimationId = 'static';

function hexToRgb(hex) {
  return [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)];
}
function rgbToHex(r, g, b) {
  return '#' + [r, g, b].map(function(v) { return ('0' + Math.max(0, Math.min(255, v)).toString(16)).slice(-2); }).join('');
}
function updateLampStatus(data) {
  if (data === undefined || data.lamp_mode === undefined) return;
  var isOn = data.lamp_mode;
  var color = data.lamp_color || [255, 255, 255];
  var brightness = data.lamp_brightness !== undefined ? data.lamp_brightness : 255;
  var animId = data.lamp_animation || 'static';
  $('#lamp_state_label').text(isOn ? 'ON' : 'OFF').css('color', isOn ? '#27ae60' : '#c0392b');
  var hex = rgbToHex(color[0], color[1], color[2]);
  $('#lamp_color_swatch').css('background-color', hex);
  $('#lamp_color_label').text(hex + ' (' + color.join(', ') + ')');
  $('#lamp_brightness_label').text(brightness);
  var animName = animId;
  $.each(_lampAnimations, function(_, a) { if (a.id === animId) { animName = a.name; return false; } });
  $('#lamp_animation_label').text(animName);
  if (!$('#lamp_color_picker').is(':focus')) $('#lamp_color_picker').val(hex);
  $('#lamp_brightness_slider').val(brightness);
  $('#lamp_brightness_value').text(brightness);
  _activeAnimationId = animId;
  refreshAnimationButtonStyles();
}
function refreshAnimationButtonStyles() {
  $('#lamp_animation_buttons button').each(function() {
    var id = $(this).data('anim-id');
    $(this).css(id === _activeAnimationId ? {'background-color':'#2980b9','color':'#fff','border-color':'#1a5276'} : {'background-color':'#e0e0e0','color':'#000','border-color':'#aaa'});
  });
}
function buildAnimationButtons(animations) {
  var $container = $('#lamp_animation_buttons');
  $container.empty();
  $.each(animations, function(_, anim) {
    $('<button type="button"></button>').text(anim.name).data('anim-id', anim.id).css({'padding':'6px 16px','border':'2px solid #aaa','border-radius':'4px','cursor':'pointer','font-size':'0.95em','height':'40px'}).click(function() {
      _activeAnimationId = anim.id;
      refreshAnimationButtonStyles();
      sendLampSet({ animation: anim.id });
    }).appendTo($container);
  });
  refreshAnimationButtonStyles();
}
function sendLampOn(extraPayload) {
  var payload = { color: hexToRgb($('#lamp_color_picker').val()), brightness: parseInt($('#lamp_brightness_slider').val(), 10), animation: _activeAnimationId };
  if (extraPayload) $.extend(payload, extraPayload);
  $.ajax({ url:'stargate/do/lamp_on', type:'POST', contentType:'application/json', data:JSON.stringify(payload) }).done(updateLampStatus);
}
function sendLampOff() {
  $.ajax({ url:'stargate/do/lamp_off', type:'POST', contentType:'application/json', data:JSON.stringify({}) }).done(function(data) {
    updateLampStatus($.extend({ lamp_mode: false }, data));
    $.get('stargate/get/dialing_status').done(updateLampStatus);
  });
}
function sendLampSet(extraPayload) {
  var payload = { color: hexToRgb($('#lamp_color_picker').val()), brightness: parseInt($('#lamp_brightness_slider').val(), 10) };
  if (extraPayload) $.extend(payload, extraPayload);
  $.ajax({ url:'stargate/do/lamp_set', type:'POST', contentType:'application/json', data:JSON.stringify(payload) }).done(function(data) {
    if (data.success === false) sendLampOn(extraPayload); else $.get('stargate/get/dialing_status').done(updateLampStatus);
  });
}
function initLampControls() {
  $.get('stargate/get/lamp_animations').done(function(data) { _lampAnimations = data.animations || []; buildAnimationButtons(_lampAnimations); });
  $.get('stargate/get/dialing_status').done(updateLampStatus);
  $('#lamp_brightness_slider').on('input', function() { $('#lamp_brightness_value').text($(this).val()); });
  $('#lamp_on_btn').click(function() { sendLampOn(); });
  $('#lamp_off_btn').click(function() { sendLampOff(); });
  $('#lamp_apply_btn').click(function() { sendLampSet(); });
}
$(function() { initLampControls(); });
