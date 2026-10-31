from __future__ import absolute_import, print_function, unicode_literals


def create_mappings(control_surface):
    # All controls are handled by ck8_control.py, so no
    # framework components are mapped. Thus CCs and notes reach the script
    # instead of going directly to Live parameters.
    return {}
