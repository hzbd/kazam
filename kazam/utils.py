# -*- coding: utf-8 -*-
#
#       utils.py
#
#       Copyright 2012 David Klasinc <bigwhale@lubica.net>
#       Copyright 2010 Andrew <andrew@karmic-desktop>
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

import os
import math
import logging
from gi.repository import Gst
from kazam.backend.constants import *

Gst.init(None)

logger = logging.getLogger("Utils")


def get_next_filename(sdir, prefix, ext):
    for cnt in range(0, 99999):
        fname = os.path.join(sdir, "{0}_{1}{2}".format(prefix,
                                                       str(cnt).zfill(5),
                                                       ext))
        if os.path.isfile(fname):
            continue
        else:
            return fname

    return "Kazam_recording{0}".format(ext)


def detect_codecs():
    codecs_supported = []
    codec_test = None
    for codec in CODEC_LIST:
        logger.debug("Testing for: {0}".format(codec[2]))
        if codec[0]:
            try:
                codec_test = Gst.ElementFactory.make(codec[1], "video_encoder")
            except:
                logger.debug("Unable to find {0} GStreamer plugin - support disabled.".format(codec))
                codec_test = None

            if codec_test:
                codecs_supported.append(codec[0])
                logger.debug("Supported encoder: {0}.".format(codec[2]))
        else:
            # RAW codec is None, so we don't try to load it.
            codecs_supported.append(codec[0])
            logger.debug("Supported encoder: {0}.".format(codec[2]))
        codec_test = None
    return codecs_supported


def get_codec(codec):
    for c in CODEC_LIST:
        if c[0] == codec:
            return c
    return None


def in_circle(center_x, center_y, radius, x, y):
    dist = math.sqrt((center_x - x) ** 2 + (center_y - y) ** 2)
    return dist <= radius
