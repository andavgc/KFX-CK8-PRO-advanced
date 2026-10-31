from __future__ import absolute_import, print_function, unicode_literals
import logging
import time

logger = logging.getLogger(__name__)

# The 8 REC ARM follow the same logic (channel 0 = REC ARM 1, which is also SHIFT):
#   - 1 short tap ........................ ARM/UNARM track at that session box position
#   - 2 short taps on the same button ..... SELECT track at that position
#   - REC ARM 1 held + L/R BANK ........ shift (Send / Device), does nothing here
TAP_MAX_SECONDS = 0.8       # button held longer than this (without BANK) does not count as tap
DOUBLE_TAP_SECONDS = 0.35   # window for second tap; increase if difficult to hit
SCHEDULE_TICKS = 4          # 1 Live tick ~ 100 ms; single tap acts ~0.4 s later
DEBUG_LOG = True            # record events in Live's Log.txt (turn off after testing)

# Where the "session ring" is in control surface (v3). Log.txt confirmed '_session_ring'.
RING_ATTRIBUTE_NAMES = ('_session_ring', 'session_ring', '_tracks_provider', 'tracks_provider')
OFFSET_ATTRIBUTE_NAMES = ('track_offset', 'offset')

# L BANK / R BANK skip by PAGE_SIZE tracks (like original MIDI Mix),
# instead of 1 by 1. To return to 1-track step, set False here and restore
# original 'Session_Navigation' mapping in mappings.py.
PAGE_BANK_BY_EIGHT = True
PAGE_SIZE = 8

# Red box (session highlight). The script draws it directly in Live and keeps it
# aligned with ring, because framework was not drawing in your setup.
DRAW_SESSION_BOX = True
BOX_WIDTH = 8               # number of tracks (= num_tracks of Specification)
BOX_HEIGHT = 1              # number of scenes (= num_scenes of Specification)
BOX_INCLUDE_RETURNS = True  # = include_returns of Specification
BOX_POLL_TICKS = 3          # check position every ~0.3 s
BOX_REFRESH_TICKS = 20      # resend box every ~2 s even without change

try:
    from ableton.v3.live import liveobj_valid
except Exception:
    def liveobj_valid(obj):
        return obj is not None


class TapSelect(object):

    def __init__(self):
        self._control_surface = None
        self._shift_down = False
        self._bank_used = False
        self._pressed_at = {}        # channel -> timestamp when pressed
        self._pending = {}           # channel -> timestamp of 1st tap, waiting for potential 2nd
        self._tokens = {}            # channel -> valid timer token
        self._counter = 0
        self._listeners = []         # keep listeners alive
        self._warned = False
        self._box_generation = 0     # invalidate box cycle from a previous script load
        self._last_box = None
        self._ticks_since_draw = 0
        self._box_error_logged = False

    def attach(self, control_surface):
        self._control_surface = control_surface
        self._shift_down = False
        self._bank_used = False
        self._pressed_at = {}
        self._pending = {}
        self._tokens = {}
        self._warned = False
        logger.info('TapSelect: attached')
        self._box_generation += 1
        self._last_box = None
        self._ticks_since_draw = 0
        self._box_error_logged = False
        if DRAW_SESSION_BOX:
            self._schedule_box(2, self._box_generation)

    # ---- red box (session highlight) ----

    def _schedule_box(self, ticks, generation):
        def run():
            if generation == self._box_generation:
                self._box_tick(generation)
        try:
            self._control_surface.schedule_message(ticks, run)
        except Exception:
            if not self._box_error_logged:
                self._box_error_logged = True
                logger.exception('TapSelect: could not schedule red box')

    def _ring_offset(self, ring):
        for name in OFFSET_ATTRIBUTE_NAMES:
            value = getattr(ring, name, None)
            if isinstance(value, int) and not isinstance(value, bool):
                return value
        # Without offset attribute: find where 1st controlled track is in track list.
        controlled = self._call_or_value(ring, 'controlled_tracks')
        controlled = list(controlled) if controlled is not None else []
        if not controlled or controlled[0] is None:
            return None
        pool = self._call_or_value(ring, 'tracks_to_use')
        if pool is None:
            song = self._get_song()
            pool = list(song.visible_tracks) + list(song.return_tracks)
        for index, track in enumerate(list(pool)):
            if track == controlled[0]:
                return index
        return None

    def _current_box(self):
        ring = self._find_ring()
        if ring is None:
            return None
        offset = self._ring_offset(ring)
        if offset is None:
            return None
        scene_offset = getattr(ring, 'scene_offset', 0)
        if not isinstance(scene_offset, int) or isinstance(scene_offset, bool):
            scene_offset = 0
        return (offset, scene_offset, BOX_WIDTH, BOX_HEIGHT, BOX_INCLUDE_RETURNS)

    def _box_tick(self, generation):
        try:
            box = self._current_box()
            self._ticks_since_draw += 1
            if box is not None and (box != self._last_box or self._ticks_since_draw >= BOX_REFRESH_TICKS):
                self._control_surface._c_instance.set_session_highlight(*box)
                if box != self._last_box:
                    self._log('red box drawn: %s' % (box,))
                self._last_box = box
                self._ticks_since_draw = 0
        except Exception:
            if not self._box_error_logged:
                self._box_error_logged = True
                logger.exception('TapSelect: error drawing red box')
        self._schedule_box(BOX_POLL_TICKS, generation)

    # ---- listeners bound to elements (see elements.py) ----

    def make_rec_arm_listener(self, channel):
        def listener(value, *args):
            self.on_rec_arm(channel, value)
        self._listeners.append(listener)
        return listener

    def on_rec_arm(self, channel, value):
        """REC ARM of channels 2 to 8 (indices 1 to 7)."""
        try:
            now = time.time()
            if value:
                self._pressed_at[channel] = now
                self._log('rec arm %d pressed' % (channel + 1))
            else:
                started = self._pressed_at.pop(channel, None)
                if started is not None and now - started <= TAP_MAX_SECONDS:
                    self._on_tap(channel)
        except Exception:
            logger.exception('TapSelect: error in on_rec_arm')

    def on_shift(self, value, *args):
        """REC ARM 1 (index 0), which is also SHIFT button."""
        try:
            if value:
                if not self._shift_down:
                    self._shift_down = True
                    self._bank_used = False
                    self._pressed_at[0] = time.time()
                    self._log('shift pressed')
            else:
                was_down = self._shift_down
                self._shift_down = False
                held = time.time() - self._pressed_at.get(0, time.time())
                self._log('shift released (held %.2fs, bank_used=%s)' % (held, self._bank_used))
                if was_down and not self._bank_used and held <= TAP_MAX_SECONDS:
                    self._on_tap(0)
        except Exception:
            logger.exception('TapSelect: error in on_shift')

    def on_bank_left(self, value, *args):
        self._on_bank(-1, value)

    def on_bank_right(self, value, *args):
        self._on_bank(1, value)

    def _on_bank(self, direction, value):
        try:
            if not value:
                return
            if self._shift_down:
                self._bank_used = True
                self._log('bank button used while shift held')
            elif PAGE_BANK_BY_EIGHT:
                self._page(direction)
        except Exception:
            logger.exception('TapSelect: error in on_bank')

    # ---- BANK L/R skipping by PAGE_SIZE tracks ----

    def _track_pool(self, ring):
        pool = self._call_or_value(ring, 'tracks_to_use')
        if pool is None:
            song = self._get_song()
            pool = list(song.visible_tracks) + list(song.return_tracks)
        return list(pool)

    def _page(self, direction):
        ring = self._find_ring()
        if ring is None:
            self._warn_once('session ring not found on control surface')
            return
        offset = self._ring_offset(ring)
        if offset is None:
            self._warn_once('could not read ring offset to page')
            return
        if direction > 0:
            new_offset = offset + PAGE_SIZE
            if new_offset >= len(self._track_pool(ring)):
                self._log('BANK R: already on last page')
                return
        else:
            new_offset = max(0, offset - PAGE_SIZE)
            if new_offset == offset:
                self._log('BANK L: already on first page')
                return
        scene_offset = getattr(ring, 'scene_offset', 0)
        if not isinstance(scene_offset, int) or isinstance(scene_offset, bool):
            scene_offset = 0
        try:
            ring.set_offsets(new_offset, scene_offset)
        except Exception:
            try:
                ring.move(new_offset - offset, 0)
            except Exception:
                try:
                    public = [n for n in dir(ring) if not n.startswith('__')]
                except Exception:
                    public = []
                logger.exception('TapSelect: could not move ring. Attributes: %s', public)
                return
        self._log('BANK %s: ring %d -> %d' % ('R' if direction > 0 else 'L', offset, new_offset))

    # ---- single vs double tap (per channel) ----

    def _on_tap(self, channel):
        now = time.time()
        since = self._pending.get(channel)
        if since is not None:
            if now - since <= DOUBLE_TAP_SECONDS:
                self._pending.pop(channel, None)
                self._tokens.pop(channel, None)
                self._log('channel %d: double tap -> select' % (channel + 1))
                self._select_track(channel)
                return
            # timer has not fired yet, but window has passed: execute previous single tap
            self._log('channel %d: window expired before timer; executing previous single tap' % (channel + 1))
            self._flush_single(channel)
        self._pending[channel] = now
        self._counter += 1
        self._tokens[channel] = self._counter
        self._schedule(channel, self._counter)

    def _schedule(self, channel, token):
        def fire():
            try:
                if channel in self._pending and self._tokens.get(channel) == token:
                    self._flush_single(channel)
            except Exception:
                logger.exception('TapSelect: error in single tap timer')
        try:
            self._control_surface.schedule_message(SCHEDULE_TICKS, fire)
        except Exception:
            logger.exception('TapSelect: schedule_message unavailable; acting without waiting')
            fire()

    def _flush_single(self, channel):
        self._pending.pop(channel, None)
        self._tokens.pop(channel, None)
        self._log('channel %d: single tap -> arm/unarm' % (channel + 1))
        self._toggle_arm(channel)

    # ---- locate track of that channel ----

    def _log(self, message):
        if DEBUG_LOG:
            logger.info('TapSelect: %s', message)

    def _warn_once(self, message):
        if not self._warned:
            self._warned = True
            logger.warning('TapSelect: %s', message)

    def _find_ring(self):
        cs = self._control_surface
        if cs is None:
            return None
        for name in RING_ATTRIBUTE_NAMES:
            try:
                candidate = getattr(cs, name, None)
            except Exception:
                candidate = None
            if candidate is not None:
                return candidate
        return None

    @staticmethod
    def _call_or_value(obj, name):
        value = getattr(obj, name, None)
        if callable(value):
            value = value()
        return value

    def _track_of_ring(self, ring, channel):
        try:
            tracks = self._call_or_value(ring, 'controlled_tracks')
            if tracks is not None:
                tracks = list(tracks)
                if tracks:
                    return tracks[channel] if channel < len(tracks) else None
        except Exception:
            logger.exception('TapSelect: controlled_tracks failed')
        try:
            all_tracks = self._call_or_value(ring, 'tracks_to_use')
            if all_tracks is not None:
                all_tracks = list(all_tracks)
                for name in OFFSET_ATTRIBUTE_NAMES:
                    offset = getattr(ring, name, None)
                    if isinstance(offset, int):
                        index = offset + channel
                        return all_tracks[index] if 0 <= index < len(all_tracks) else None
        except Exception:
            logger.exception('TapSelect: tracks_to_use failed')
        return None

    def _controlled_track(self, channel):
        ring = self._find_ring()
        if ring is None:
            self._warn_once('session ring not found on control surface')
            return None
        track = self._track_of_ring(ring, channel)
        if track is None or not liveobj_valid(track):
            self._log('channel %d: no track at this window position' % (channel + 1))
            return None
        return track

    def _get_song(self):
        try:
            song = self._control_surface.song
            if callable(song):
                song = song()
            if song is not None:
                return song
        except Exception:
            pass
        import Live
        return Live.Application.get_application().get_document()

    # ---- actions ----

    def _select_track(self, channel):
        track = self._controlled_track(channel)
        if track is None:
            return
        self._get_song().view.selected_track = track
        self._log('selected track: %s' % getattr(track, 'name', '?'))

    def _toggle_arm(self, channel):
        track = self._controlled_track(channel)
        if track is None:
            return
        if not getattr(track, 'can_be_armed', False):
            self._log('track "%s" cannot be armed' % getattr(track, 'name', '?'))
            return
        track.arm = not track.arm
        self._log('track "%s" arm=%s' % (getattr(track, 'name', '?'), track.arm))


tap_select = TapSelect()
