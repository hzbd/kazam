# -*- coding: utf-8 -*-
#
#       constants.py
#
#       Copyright 2012 David Klasinc <bigwhale@lubica.net>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.


# Codecs

CODEC_RAW = 0
CODEC_VP8 = 1
CODEC_H264 = 2
CODEC_HUFF = 3
CODEC_JPEG = 4

#
# Number, gstreamer element name, string description, file extension, advanced
#

CODEC_LIST = [[0, None, 'RAW / AVI', '.avi', True],
              [1, 'vp8enc', 'VP8 / WEBM', '.webm', False],
              [2, 'x264enc', 'H264 / MP4', '.mp4', False],
              [3, 'ffenc_huffyuv', 'HUFFYUV / AVI', '.avi', True],
              [4, 'ffenc_ljpeg', 'Lossless JPEG / AVI', '.avi', True],
              ]

# PulseAudio Error Codes
PA_LOAD_ERROR = 1
PA_GET_STATE_ERROR = 2
PA_STARTUP_ERROR = 3
PA_UNABLE_TO_CONNECT = 4
PA_UNABLE_TO_CONNECT2 = 5
PA_MAINLOOP_START_ERROR = 6
PA_GET_SOURCES_ERROR = 7
PA_GET_SOURCES_TIMEOUT = 8
PA_GET_SOURCE_ERROR = 9
PA_GET_SOURCE_TIMEOUT = 10
PA_MAINLOOP_END_ERROR = 11


# PulseAudio Status Codes
PA_STOPPED = 0
PA_WORKING = 1
PA_FINISHED = 2
PA_ERROR = 3

# PulseAudio State Codes
PA_STATE_READY = 0
PA_STATE_BUSY = 1
PA_STATE_FAILED = 2
PA_STATE_WORKING = 3


# Various actions
ACTION_SAVE = 0
ACTION_EDIT = 1

# Blink modes and states
BLINK_STOP = 0
BLINK_START = 1
BLINK_SLOW = 2
BLINK_FAST = 3
BLINK_STOP_ICON = 4
BLINK_READY_ICON = 5

# Main modes
MODE_SCREENCAST = 0
MODE_SCREENSHOT = 1

# Record modes
MODE_FULL = 0
MODE_ALL = 1
MODE_AREA = 2
MODE_WIN = 3
MODE_ACTIVE = 4
MODE_GOD = 666


# Area resize handles
HANDLE_TL = 0
HANDLE_TC = 1
HANDLE_TR = 2
HANDLE_CL = 3
HANDLE_MOVE = 4
HANDLE_CR = 5
HANDLE_BL = 6
HANDLE_BC = 7
HANDLE_BR = 8

import logging

from gi.repository import Gdk, GdkX11


# Area resize handle cursors
HANDLE_CURSORS = (
    Gdk.CursorType.TOP_LEFT_CORNER,
    Gdk.CursorType.TOP_SIDE,
    Gdk.CursorType.TOP_RIGHT_CORNER,
    Gdk.CursorType.LEFT_SIDE,
    Gdk.CursorType.FLEUR,
    Gdk.CursorType.RIGHT_SIDE,
    Gdk.CursorType.BOTTOM_LEFT_CORNER,
    Gdk.CursorType.BOTTOM_SIDE,
    Gdk.CursorType.BOTTOM_RIGHT_CORNER
)


class hw:
    def __init__(self):
        self.logger = logging.getLogger("Constants")
        self.logger.debug("Getting hardware specs")
        self.screens = None
        self.combined_screen = None

        self.get_screens()

    def get_current_screen(self, window = None):
        try:
            if window:
                screen = self.default_screen.get_monitor_at_window(window.get_window())
            else:
                disp = GdkX11.X11Display.get_default()
                dm = Gdk.Display.get_device_manager(disp)
                pntr_device = dm.get_client_pointer()
                (src, x, y) = pntr_device.get_position()
                screen = self.default_screen.get_monitor_at_point(x, y)
        except:
            screen = 0
        return screen

    def get_screens(self):
        try:
            self.logger.debug("Getting Video sources.")
            self.screens = []
            self.default_screen = Gdk.Screen.get_default()
            self.logger.debug("Found {0} monitor(s).".format(self.default_screen.get_n_monitors()))

            for i in range(self.default_screen.get_n_monitors()):
                rect = self.default_screen.get_monitor_geometry(i)
                self.logger.debug("  Monitor {0} - X: {1}, Y: {2}, W: {3}, H: {4}".format(i,
                                                                                          rect.x,
                                                                                          rect.y,
                                                                                          rect.width,
                                                                                          rect.height))
                self.screens.append({"x": rect.x,
                                     "y": rect.y,
                                     "width": rect.width,
                                     "height": rect.height})

            if self.default_screen.get_n_monitors() > 1:
                self.combined_screen = {"x": 0, "y": 0,
                                        "width": self.default_screen.get_width(),
                                        "height": self.default_screen.get_height()}
                self.logger.debug("  Combined screen - X: 0, Y: 0, W: {0}, H: {1}".format(self.default_screen.get_width(),
                                                                                          self.default_screen.get_height()))
            else:
                self.combined_screen = None

        except:
            self.logger.warning("Unable to find any video sources.")

HW = hw()
