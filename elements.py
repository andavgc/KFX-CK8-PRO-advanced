from __future__ import absolute_import, print_function, unicode_literals
from ableton.v3.control_surface import MIDI_NOTE_TYPE, MIDI_CC_TYPE, ElementsBase
import logging

from . import ck8_control

logger = logging.getLogger(__name__)

# Factory MIDI Mix layout notes and CCs (CK8 PRO uses the same).
# Knob rows, top to bottom, channels 1 to 8.
KNOB_CCS = [(16, 20, 24, 28, 46, 50, 54, 58),
            (17, 21, 25, 29, 47, 51, 55, 59),
            (18, 22, 26, 30, 48, 52, 56, 60)]
FADER_CCS = (19, 23, 27, 31, 49, 53, 57, 61)
MASTER_FADER_CC = 62

LEFT_BUTTON_NOTE = 25
RIGHT_BUTTON_NOTE = 26
MUTE_BUTTON_NOTES = (1, 4, 7, 10, 13, 16, 19, 22)
SOLO_BUTTON_NOTES = (2, 5, 8, 11, 14, 17, 20, 23)
REC_ARM_BUTTON_NOTES = (3, 6, 9, 12, 15, 18, 21, 24)   # REC ARM 1 (note 3) is also shift
SEND_ALL_NOTE = 62                                      # note (not CC; CC 62 is the master fader)


class Elements(ElementsBase):

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        logger.info("=========================================")

        # No controls are mapped to framework components:
        # ck8_control.py receives everything and decides what to do in each mode.
        self.add_button(LEFT_BUTTON_NOTE, 'bank_left', msg_type=MIDI_NOTE_TYPE)
        self.add_button(RIGHT_BUTTON_NOTE, 'bank_right', msg_type=MIDI_NOTE_TYPE)

        for c in range(8):
            self.add_button(MUTE_BUTTON_NOTES[c], 'mute_%d' % c, msg_type=MIDI_NOTE_TYPE)
            self.add_button(SOLO_BUTTON_NOTES[c], 'solo_%d' % c, msg_type=MIDI_NOTE_TYPE)
            self.add_button(REC_ARM_BUTTON_NOTES[c], 'arm_%d' % c, msg_type=MIDI_NOTE_TYPE)
            self.add_encoder(FADER_CCS[c], 'fader_%d' % c, msg_type=MIDI_CC_TYPE)
            for r in range(3):
                self.add_encoder(KNOB_CCS[r][c], 'knob_%d_%d' % (r, c), msg_type=MIDI_CC_TYPE)

        self.add_encoder(MASTER_FADER_CC, 'master_fader', msg_type=MIDI_CC_TYPE)
        self.add_button(SEND_ALL_NOTE, 'send_all', msg_type=MIDI_NOTE_TYPE)

        ck8_control.register_elements(self)
