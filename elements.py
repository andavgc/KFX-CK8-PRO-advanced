from __future__ import absolute_import, print_function, unicode_literals
from ableton.v3.control_surface import MIDI_NOTE_TYPE, MIDI_CC_TYPE, ElementsBase
import logging

logger = logging.getLogger(__name__)

# note that the SEND ALL button on the midimix sends midi note #62
ENCODER_CCS =        [(16, 20, 24, 28, 46, 50, 54, 58),
                      (17, 21, 25, 29, 47, 51, 55, 59)]
PAN_CONTROL_CCS =    [(18, 22, 26, 30, 48, 52, 56, 60)]
VOLUME_CONTROL_CCS = [(19, 23, 27, 31, 49, 53, 57, 61)]
MASTER_VOLUME_CC =  62

LEFT_BUTTON_NOTE =  25
RIGHT_BUTTON_NOTE = 26
SOLO_BUTTON_NOTE =  27
MUTE_BUTTON_NOTES =    [(1, 4, 7, 10, 13, 16, 19, 22)]
SOLO_BUTTON_NOTES =    [(2, 5, 8, 11, 14, 17, 20, 23)]
REC_ARM_BUTTON_NOTES = [(3, 6, 9, 12, 15, 18, 21, 24)]

class Elements(ElementsBase):

    def __init__(self, *a, **k):
        (super().__init__)(*a, **k)
        logger.info("=========================================")

        self.add_button(LEFT_BUTTON_NOTE, 'left_button', msg_type=MIDI_NOTE_TYPE)
        self.add_button(RIGHT_BUTTON_NOTE, 'right_button', msg_type=MIDI_NOTE_TYPE)
        self.add_modifier_button(SOLO_BUTTON_NOTE, 'shift_button', msg_type=MIDI_NOTE_TYPE)
        self.add_encoder_matrix(ENCODER_CCS, 'encoders', msg_type=MIDI_CC_TYPE)
        self.add_submatrix((self.encoders), 'send_a_controls', rows=(0, 1))
        self.add_submatrix((self.encoders), 'send_b_controls', rows=(1, 2))
        self.add_encoder_matrix(PAN_CONTROL_CCS, 'pan_controls', msg_type=MIDI_CC_TYPE)
        self.add_button_matrix(MUTE_BUTTON_NOTES, 'mute_buttons', msg_type=MIDI_NOTE_TYPE)
        self.add_button_matrix(SOLO_BUTTON_NOTES, 'solo_buttons', msg_type=MIDI_NOTE_TYPE)
        self.add_button_matrix(REC_ARM_BUTTON_NOTES, 'rec_arm_buttons', msg_type=MIDI_NOTE_TYPE)
        self.add_encoder_matrix(VOLUME_CONTROL_CCS, 'volume_controls', msg_type=MIDI_CC_TYPE)
        self.add_encoder(MASTER_VOLUME_CC, 'master_volume_control', msg_type=MIDI_CC_TYPE)
