from __future__ import absolute_import, print_function, unicode_literals
"""
Complete control of KFX CK8 PRO (MIDI Mix layout) with two modes.

MODE 1 (mixer)
  Knobs row 1 / 2 / 3 ........ Send A / Send B / Send C
  Shift + row 1 / 2 / 3 ...... Send D / Send E / Pan
  Faders 1-8 ................. Volume (top = 0 dB)
  BANK L / R ................. 8-track page

MODE 2 (devices)
  Row 1 / 2 / 3 .............. First 8 parameters of the selected device
                               on tracks 1 / 2 / 3 of the page
  Fader N .................... Choose device of track N
                               (min = first, max = last)
  BANK L / R ................. 3-track page

BOTH MODES
  Shift = hold REC ARM 1
  Shift + BANK R ............. Toggle between mode 1 and mode 2
  Shift + BANK L ............. Return to mode 1
  REC ARM: 1 tap arms, 2 taps select track
  MUTE / SOLO ................ Track mute / solo
  Master fader ............... Master volume (top = 0 dB)
  SEND ALL ................... Send knob positions to what they
                               control now (mode, page, and shift),
                               ignoring pickup
"""
import functools
import logging
import time

# ======================= SETTINGS =======================
DEBUG_LOG = True               # False to stop writing to Log.txt

DOUBLE_TAP_SECONDS = 0.35      # window for second tap
SCHEDULE_TICKS = 4             # ~100 ms per tick; keep slightly above window
TAP_MAX_SECONDS = 0.8          # taps longer than this do not count

PICKUP_KNOBS = True            # knob only takes parameter after passing current value
PICKUP_FADERS = True           # same for volume faders (includes master)
PICKUP_TOLERANCE = 0.03        # "close enough" to assume without crossing (0 to 1)

VOLUME_MAX = 0.85              # 0.85 = 0 dB in Live
MASTER_LIMIT_0DB = True        # False for master to go up to +6 dB

MODE1_PAGE = 8                 # BANK step in mode 1
MODE2_PAGE = 3                 # BANK step in mode 2 (= number of rows)

SEND_ALL_SECONDS = 0.4         # window where SEND ALL dump ignores pickup
BURST_SECONDS = 0.15           # dump detected when many controls arrive
BURST_MIN_CONTROLS = 10        # ... together within this interval

DRAW_SESSION_BOX = True
MUTE_LED_ON_WHEN_MUTED = True  # invert if mute LED lights up backward
POLL_TICKS = 3                 # box and LED update frequency
FULL_REFRESH_POLLS = 7         # resend box and LEDs every N updates
# =======================================================

logger = logging.getLogger(__name__)

_ELEMENTS = None
_CONTROLLER = None


def register_elements(elements):
    global _ELEMENTS
    _ELEMENTS = elements


def attach(surface, c_instance):
    """Called by __init__.py after control surface is created."""
    global _CONTROLLER
    elements = getattr(surface, 'elements', None)
    if elements is None or getattr(elements, 'bank_left', None) is None:
        elements = _ELEMENTS
    if elements is None:
        _log_static('CK8: elements not found, control disabled')
        return None
    if _CONTROLLER is not None:
        _CONTROLLER.disconnect()
    _CONTROLLER = CK8Control(surface, c_instance, elements)

    original_disconnect = surface.disconnect

    def disconnect(*a, **k):
        try:
            _CONTROLLER.disconnect()
        except Exception:
            pass
        return original_disconnect(*a, **k)

    try:
        surface.disconnect = disconnect
    except Exception:
        pass
    return _CONTROLLER


def _log_static(msg):
    try:
        logger.info(msg)
    except Exception:
        pass


def _song():
    import Live
    return Live.Application.get_application().get_document()


class _Pickup(object):
    __slots__ = ('target', 'prev', 'picked')

    def __init__(self):
        self.target = None
        self.prev = None
        self.picked = False


class CK8Control(object):

    def __init__(self, surface, c_instance, elements):
        self._surface = surface
        self._c_instance = c_instance
        self._el = elements
        self._alive = True

        self._mode = 1
        self._offset = 0

        self._shift_held = False
        self._shift_used = False
        self._arm_down_at = [0.0] * 8
        self._pending = [None] * 8          # (token, tap timestamp)
        self._token = 0

        self._pickups = {}
        self._fader_device = [None] * 8     # last device index chosen by fader
        self._led_cache = {}
        self._last_box = None
        self._polls = 0
        self._listeners = []                # strong references to callbacks
        self._knob_pos = {}                 # last physical position of each knob
        self._dump_until = 0.0
        self._dump_shift = False            # shift state at the instant of SEND ALL
        self._dump_token = 0
        self._recent_selects = []           # (timestamp, channel, track, previous device)
        self._recent = []                   # (timestamp, control) to detect dump

        self._bind()
        self._log('started (mode 1, offset 0)')
        self._schedule(POLL_TICKS, self._poll)

    # ------------------------------------------------------------ infra

    def disconnect(self):
        self._alive = False

    def _log(self, msg):
        if DEBUG_LOG:
            _log_static('CK8: ' + msg)

    def _schedule(self, ticks, callback):
        def run():
            if self._alive:
                try:
                    callback()
                except Exception as e:
                    _log_static('CK8: error in scheduled task: %r' % (e,))
        try:
            self._surface.schedule_message(ticks, run)
        except Exception as e:
            _log_static('CK8: schedule_message failed: %r' % (e,))

    def _element(self, name):
        el = getattr(self._el, name, None)
        if el is None:
            _log_static('CK8: element %s not found' % name)
        return el

    def _listen(self, name, handler, *args):
        el = self._element(name)
        if el is None:
            return

        cb = functools.partial(self._guarded, handler, *args)
        self._listeners.append(cb)
        try:
            el.add_value_listener(cb)
        except Exception as e:
            _log_static('CK8: could not listen to %s: %r' % (name, e))

    def _guarded(self, handler, *args):
        if not self._alive:
            return
        try:
            handler(*args)
        except Exception as e:
            _log_static('CK8: error in %s%r: %r' % (handler.__name__, args, e))

    def _bind(self):
        self._listen('bank_left', self._on_bank, -1)
        self._listen('bank_right', self._on_bank, 1)
        for c in range(8):
            self._listen('arm_%d' % c, self._on_arm, c)
            self._listen('mute_%d' % c, self._on_mute, c)
            self._listen('solo_%d' % c, self._on_solo, c)
            self._listen('fader_%d' % c, self._on_fader, c)
            for r in range(3):
                self._listen('knob_%d_%d' % (r, c), self._on_knob, r, c)
        self._listen('master_fader', self._on_master)
        self._listen('send_all', self._on_send_all)

    # ------------------------------------------------------------ tracks

    def _tracks(self):
        song = _song()
        return list(song.visible_tracks) + list(song.return_tracks)

    def _track_at(self, index):
        tracks = self._tracks()
        if 0 <= index < len(tracks):
            return tracks[index]
        return None

    def _page_size(self):
        return MODE1_PAGE if self._mode == 1 else MODE2_PAGE

    def _box_width(self):
        return 8 if self._mode == 1 else MODE2_PAGE

    def _touch(self):
        # any control used with shift held cancels REC ARM 1 tap
        if self._shift_held:
            self._shift_used = True

    # ------------------------------------------------------------ modes & pages

    def _set_mode(self, mode):
        if mode == self._mode:
            return
        self._mode = mode
        self._fader_device = [None] * 8
        self._pickups = {}   # when returning from a mode, controls need to re-assume
        self._log('mode %d (offset %d)' % (mode, self._offset))
        self._refresh(force=True)

    def _on_bank(self, direction, value):
        if not value:
            return
        if self._shift_held:
            self._shift_used = True
            if direction > 0:
                self._set_mode(2 if self._mode == 1 else 1)
            else:
                self._set_mode(1)
            return

        total = len(self._tracks())
        step = self._page_size()
        new = self._offset + direction * step
        if direction > 0 and new >= total:
            return
        new = max(0, new)
        if new != self._offset:
            self._offset = new
            self._fader_device = [None] * 8
            self._log('page: offset %d' % new)
            self._refresh(force=True)

    # ------------------------------------------------------------ REC ARM / shift

    def _on_arm(self, channel, value):
        now = time.time()
        if channel != 0:
            self._touch()

        if value:
            self._arm_down_at[channel] = now
            if channel == 0:
                self._shift_held = True
                self._shift_used = False
            return

        held = now - self._arm_down_at[channel]
        if channel == 0:
            used = self._shift_used
            self._shift_held = False
            self._shift_used = False
            if used:
                return
        if held > TAP_MAX_SECONDS:
            return
        self._on_tap(channel, now)

    def _on_tap(self, channel, now):
        pending = self._pending[channel]
        if pending is not None and now - pending[1] <= DOUBLE_TAP_SECONDS:
            self._pending[channel] = None
            self._select(channel)
            return
        self._token += 1
        token = self._token
        self._pending[channel] = (token, now)
        self._schedule(SCHEDULE_TICKS, functools.partial(self._resolve_tap, channel, token))

    def _resolve_tap(self, channel, token):
        pending = self._pending[channel]
        if pending is not None and pending[0] == token:
            self._pending[channel] = None
            self._toggle_arm(channel)

    def _toggle_arm(self, channel):
        track = self._track_at(self._offset + channel)
        if track is None or not getattr(track, 'can_be_armed', False):
            self._log('channel %d: track cannot be armed' % (channel + 1))
            return
        track.arm = not track.arm
        self._log('channel %d: arm=%s' % (channel + 1, track.arm))
        self._refresh_leds()

    def _select(self, channel):
        track = self._track_at(self._offset + channel)
        if track is None:
            return
        _song().view.selected_track = track
        self._log('channel %d: track selected' % (channel + 1))

    # ------------------------------------------------------------ mute / solo

    def _on_mute(self, channel, value):
        self._touch()
        if not value:
            return
        track = self._track_at(self._offset + channel)
        if track is None:
            return
        track.mute = not track.mute
        self._refresh_leds()

    def _on_solo(self, channel, value):
        self._touch()
        if not value:
            return
        track = self._track_at(self._offset + channel)
        if track is None:
            return
        new = not track.solo
        song = _song()
        if new and getattr(song, 'exclusive_solo', False):
            for other in self._tracks():
                if other != track and other.solo:
                    other.solo = False
        track.solo = new

    # ------------------------------------------------------------ knobs

    def _knob_param(self, row, channel, shift=None):
        if shift is None:
            shift = self._dump_shift if self._in_dump() else self._shift_held
        if self._mode == 1:
            track = self._track_at(self._offset + channel)
            if track is None:
                return None
            mixer = track.mixer_device
            if shift:
                if row == 2:
                    return mixer.panning
                send = 3 if row == 0 else 4          # Send D / Send E
            else:
                send = row                           # Send A / B / C
            sends = list(mixer.sends)
            return sends[send] if send < len(sends) else None

        track = self._track_at(self._offset + row)
        if track is None:
            return None
        device = self._current_device(track)
        if device is None:
            return None
        params = list(device.parameters)
        index = channel + 1                          # skip "Device On"
        return params[index] if index < len(params) else None

    def _current_device(self, track):
        devices = list(track.devices)
        if not devices:
            return None
        try:
            selected = track.view.selected_device
        except Exception:
            selected = None
        if selected is not None:
            for d in devices:
                if d == selected:
                    return d
        return devices[0]

    def _on_knob(self, row, channel, value):
        self._touch()
        self._knob_pos[(row, channel)] = value
        self._note_cc(('knob', row, channel))

        track = self._track_at(self._offset + channel if self._mode == 1 else self._offset + row)
        if track is not None:
            try:
                _song().view.selected_track = track
            except Exception:
                pass

        param = self._knob_param(row, channel)
        self._apply(('knob', row, channel), param, value / 127.0, PICKUP_KNOBS,
                    force=self._in_dump())

    # ------------------------------------------------------------ SEND ALL

    def _in_dump(self):
        return time.time() < self._dump_until

    def _note_cc(self, key):
        now = time.time()
        recent = [(t, k) for (t, k) in self._recent if now - t <= BURST_SECONDS]
        recent.append((now, key))
        self._recent = recent
        if not self._in_dump() and len(set(k for _, k in recent)) >= BURST_MIN_CONTROLS:
            self._log('SEND ALL dump detected')
            self._start_dump()

    def _on_send_all(self, value):
        self._touch()
        if value:
            self._log('SEND ALL')
            self._start_dump()

    def _start_dump(self):
        self._undo_burst_selects()
        self._dump_until = time.time() + SEND_ALL_SECONDS
        self._dump_shift = self._shift_held
        shift = self._dump_shift
        self._dump_token += 1
        self._force_knobs(shift)
        # reapply after dump finishes arriving, with the same shift
        self._schedule(2, functools.partial(self._force_knobs, shift, self._dump_token))

    def _undo_burst_selects(self):
        # faders that arrived at the start of the dump, before it was detected,
        # may have changed device; revert to previously selected
        now = time.time()
        for when, channel, track, previous in reversed(self._recent_selects):
            if now - when <= BURST_SECONDS and previous is not None:
                self._select_device(track, previous)
                self._fader_device[channel] = None
        self._recent_selects = []

    def _force_knobs(self, shift, token=None):
        if token is not None and token != self._dump_token:
            return                                   # a newer SEND ALL has already taken over
        count = 0
        for (row, channel), value in list(self._knob_pos.items()):
            param = self._knob_param(row, channel, shift)
            if param is not None:
                self._apply(('knob', row, channel), param, value / 127.0, PICKUP_KNOBS, force=True)
                count += 1
        self._log('SEND ALL: %d knobs sent (mode %d, offset %d, shift=%s)'
                  % (count, self._mode, self._offset, shift))

    # ------------------------------------------------------------ faders

    def _on_fader(self, channel, value):
        self._touch()
        self._note_cc(('fader', channel))
        norm = value / 127.0
        track = self._track_at(self._offset + channel)
        if track is None:
            return
        if self._mode == 1:
            self._apply(('fader', channel), track.mixer_device.volume,
                        norm * VOLUME_MAX, PICKUP_FADERS)
            return

        if self._in_dump():
            return                                   # SEND ALL does not change devices
        devices = list(track.devices)
        if not devices:
            return
        index = int(round(norm * (len(devices) - 1)))
        if index == self._fader_device[channel]:
            return
        self._fader_device[channel] = index
        try:
            previous = track.view.selected_device
        except Exception:
            previous = None
        now = time.time()
        self._recent_selects = [x for x in self._recent_selects if now - x[0] <= BURST_SECONDS]
        self._recent_selects.append((now, channel, track, previous))
        self._select_device(track, devices[index])

    def _select_device(self, track, device):
        view = _song().view
        try:
            view.select_device(device, False)
        except Exception:
            try:
                view.select_device(device)
            except Exception as e:
                self._log('could not select device: %r' % (e,))
                return
        self._log('selected device: %s' % getattr(device, 'name', '?'))

    def _on_master(self, value):
        self._touch()
        self._note_cc(('master',))
        scale = VOLUME_MAX if MASTER_LIMIT_0DB else 1.0
        self._apply(('master',), _song().master_track.mixer_device.volume,
                    value / 127.0 * scale, PICKUP_FADERS)

    # ------------------------------------------------------------ apply value (with pickup)

    def _apply(self, slot, param, norm, pickup, force=False):
        state = self._pickups.get(slot)
        if state is None:
            state = self._pickups[slot] = _Pickup()

        if param is None:
            state.target = None
            state.prev = None
            state.picked = False
            return

        same = False
        try:
            same = state.target is not None and state.target == param
        except Exception:
            same = False
        if not same:
            state.target = param
            state.prev = None
            state.picked = not pickup
        if force:
            state.picked = True

        if not getattr(param, 'is_enabled', True):
            return

        low, high = param.min, param.max
        span = (high - low) or 1.0

        if not state.picked:
            current = (param.value - low) / span
            crossed = state.prev is not None and (state.prev - current) * (norm - current) <= 0
            if crossed or abs(norm - current) <= PICKUP_TOLERANCE:
                state.picked = True
            else:
                state.prev = norm
                return

        new = low + norm * span
        if getattr(param, 'is_quantized', False):
            new = round(new)
        new = min(max(new, low), high)
        param.value = new
        state.prev = norm

    # ------------------------------------------------------------ red box & LEDs

    def _poll(self):
        self._polls += 1
        force = self._polls % FULL_REFRESH_POLLS == 0
        self._refresh(force=force)
        self._schedule(POLL_TICKS, self._poll)

    def _refresh(self, force=False):
        total = len(self._tracks())
        if total and self._offset > total - 1:
            self._offset = max(0, total - 1)
        if force:
            self._last_box = None
            self._led_cache = {}
        self._draw_box()
        self._refresh_leds()

    def _draw_box(self):
        if not DRAW_SESSION_BOX:
            return
        box = (self._offset, 0, self._box_width(), 1, True)
        if box == self._last_box:
            return
        try:
            self._c_instance.set_session_highlight(*box)
            if self._last_box is None or box[:3] != self._last_box[:3]:
                self._log('red box: %r' % (box,))
            self._last_box = box
        except Exception as e:
            _log_static('CK8: could not draw box: %r' % (e,))

    def _send_led(self, name, on):
        value = 127 if on else 0
        if self._led_cache.get(name) == value:
            return
        el = getattr(self._el, name, None)
        if el is None:
            return
        try:
            el.send_value(value, True)
        except TypeError:
            try:
                el.send_value(value)
            except Exception:
                return
        except Exception:
            return
        self._led_cache[name] = value

    def _refresh_leds(self):
        tracks = self._tracks()
        for c in range(8):
            i = self._offset + c
            track = tracks[i] if i < len(tracks) else None
            muted = bool(track is not None and track.mute)
            armed = bool(track is not None and getattr(track, 'can_be_armed', False) and track.arm)
            mute_on = muted if MUTE_LED_ON_WHEN_MUTED else (track is not None and not muted)
            self._send_led('mute_%d' % c, mute_on)
            self._send_led('arm_%d' % c, armed)
