# -*- coding: utf-8 -*-
#
#       prefs.py
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

import os
import logging
from os.path import expanduser
from gettext import gettext as _
from xdg.BaseDirectory import xdg_config_home

from kazam.backend.config import KazamConfig
from kazam.utils import detect_codecs

CODEC_RAW = 0
CODEC_VP8 = 1
CODEC_H264 = 2


class Prefs():
    def __init__(self):
        """Initialize prefs and set all the preference variables to their
           default values.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self.logger = logging.getLogger("Prefs")

        #
        # GUI preferences and stuff
        #
        self.capture_cursor = False
        self.capture_speakers = False
        self.capture_microphone = False

        self.capture_cursor_pic = False
        self.capture_borders_pic = False

        self.countdown_timer = 5

        self.speakers_source = None
        self.microphone_source = None

        self.speakers_volume = 0
        self.microphone_volume = 0

        self.countdown_splash = True
        self.silent_start = False

        #
        # Other stuff
        #
        self.datadir = None

        #
        # Capture related stuff
        #
        self.codec = None
        self.pa_q = None
        self.framerate = 15
        self.autosave_video = False
        self.autosave_video_dir = None
        self.autosave_video_file = None

        self.autosave_picture = False
        self.autosave_picture_dir = None
        self.autosave_picture_file = None
        self.shutter_sound = True
        self.shutter_type = 0
        self.shutter_sound_file = ""

        self.area = None
        self.xid = None
        self.xid_geometry = None

        #
        # Audio sources
        #  - Tuple of all sources
        #  - Selected first source
        #  - Selected second source
        #
        self.audio_sources = None
        self.audio_source = None
        self.audio2_source = None

        self.speaker_sources = []
        self.mic_sources = []

        #
        # Command line parameters
        #
        self.debug = False
        self.test = False
        self.dist = ('Ubuntu', '12.10', 'quantal')
        self.silent = False
        self.sound = True
        self.first_run = True

        self.config = KazamConfig()

        self.read_config()

        self.get_dirs()

    def get_audio_sources(self):
        self.logger.debug("Getting Audio sources.")
        try:
            self.audio_sources = prefs.pa_q.get_audio_sources()
            for src in self.audio_sources:
                if "Monitor" in src[2]:
                    self.speaker_sources.append(src)
                else:
                    self.mic_sources.append(src)

            if prefs.debug:
                for src in self.audio_sources:
                    self.logger.debug(" Device found: ")
                    for item in src:
                        self.logger.debug("  - {0}".format(item))
        except:
            # Something went wrong, just fallback to no-sound
            self.logger.warning("Unable to find any audio devices.")
            self.audio_sources = [[0, _("Unknown"), _("Unknown")]]

    def get_dirs(self):
        paths = {}
        f = None
        try:
            f = open(os.path.join(xdg_config_home, "user-dirs.dirs"))
            for la in f:
                if la.startswith("XDG_VIDEOS") or la.startswith("XDG_DOCUMENTS") or la.startswith("XDG_PICTURES"):
                    (idx, val) = la.strip()[:-1].split('="')
                    paths[idx] = os.path.expandvars(val)
        except:
            paths['XDG_VIDEOS_DIR'] = os.path.expanduser("~/Videos/")
            paths['XDG_PICTURES_DIR'] = os.path.expanduser("~/Pictures/")
            paths['XDG_DOCUMENTS_DIR'] = os.path.expanduser("~/Documents/")
        finally:
            if f is not None:
                f.close()

        paths['HOME_DIR'] = os.path.expandvars("$HOME")

        if 'XDG_VIDEOS_DIR' in paths and os.path.isdir(paths['XDG_VIDEOS_DIR']):
            self.video_dest = paths['XDG_VIDEOS_DIR']
        elif 'XDG_DOCUMENTS_DIR' in paths and os.path.isdir(paths['XDG_DOCUMENTS_DIR']):
            self.video_dest = paths['XDG_DOCUMENTS_DIR']
        elif 'HOME_DIR' in paths and os.path.isdir(paths['HOME_DIR']):
            self.video_dest = paths['HOME_DIR']
        else:
            self.video_dest = expanduser("~")

        if 'XDG_PICTURES_DIR' in paths and os.path.isdir(paths['XDG_PICTURES_DIR']):
            self.logger.debug("XDG_PICTURES is a directory and accessible")
            self.picture_dest = paths['XDG_PICTURES_DIR']
        elif 'XDG_DOCUMENTS_DIR' in paths and os.path.isdir(paths['XDG_DOCUMENTS_DIR']):
            self.logger.debug("XDG_DOCUMENTS is a directory and accessible")
            self.picture_dest = paths['XDG_DOCUMENTS_DIR']
        elif 'HOME_DIR' in paths and os.path.isdir(paths['HOME_DIR']):
            self.logger.debug("HOME_DIR is a directory and accessible")
            self.picture_dest = paths['HOME_DIR']
        else:
            self.logger.debug("Fallback to ~ for save files.")
            self.picture_dest = expanduser("~")

    def get_sound_files(self):
        self.sound_files = []
        for root, d_dir, files in os.walk(os.path.join(self.datadir, "sounds")):
            for f_file in files:
                if f_file.endswith('.ogg'):
                    self.sound_files.append(f_file)

    def read_config(self):
        self.audio_source = int(self.config.get("main", "audio_source"))
        self.audio2_source = int(self.config.get("main", "audio2_source"))
        self.main_x = int(self.config.get("main", "last_x"))
        self.main_y = int(self.config.get("main", "last_y"))
        self.countdown_timer = float(self.config.get("main", "counter"))

        #
        # Just in case this blows up in our face later
        #
        if self.countdown_timer > 10:
            self.countdown_timer = 10
        self.framerate = float(self.config.get("main", "framerate"))

        self.capture_cursor = self.config.getboolean("main", "capture_cursor")
        self.capture_microphone = self.config.getboolean("main", "capture_microphone")
        self.capture_speakers = self.config.getboolean("main", "capture_speakers")

        self.capture_cursor_pic = self.config.getboolean("main", "capture_cursor_pic")
        self.capture_borders_pic = self.config.getboolean("main", "capture_borders_pic")

        self.countdown_splash = self.config.getboolean("main", "countdown_splash")

        self.autosave_video = self.config.getboolean("main", "autosave_video")
        self.autosave_video_dir = self.config.get("main", "autosave_video_dir")
        self.autosave_video_file = self.config.get("main", "autosave_video_file")

        self.autosave_picture = self.config.getboolean("main", "autosave_picture")
        self.autosave_picture_dir = self.config.get("main", "autosave_picture_dir")
        self.autosave_picture_file = self.config.get("main", "autosave_picture_file")

        self.shutter_sound = self.config.getboolean("main", "shutter_sound")
        self.shutter_type = int(self.config.get("main", "shutter_type"))

        self.first_run = self.config.getboolean("main", "first_run")

        #
        # Determine which codec to use
        #
        if self.first_run:
            self.logger.debug("First run detected.")
            self.config.set("main", "first_run", False)
            self.config.write()

            codecs_avail = detect_codecs()
            if CODEC_H264 in codecs_avail:
                self.codec = CODEC_H264
                self.logger.debug("Setting H264 as default codec.")
            elif CODEC_VP8 in codecs_avail:
                self.codec = CODEC_VP8
                self.logger.debug("Setting VP8 as default codec.")
            else:
                self.codec = CODEC_RAW
                self.logger.debug("Setting RAW as default codec.")
        else:
            self.codec = int(self.config.get("main", "codec"))

    def save_config(self):
        self.config.set("main", "capture_cursor", self.capture_cursor)
        self.config.set("main", "capture_speakers", self.capture_speakers)
        self.config.set("main", "capture_microphone", self.capture_microphone)

        self.config.set("main", "capture_cursor_pic", self.capture_cursor_pic)
        self.config.set("main", "capture_borders_pic", self.capture_borders_pic)

        self.config.set("main", "last_x", self.main_x)
        self.config.set("main", "last_y", self.main_y)

        if self.sound:
            self.config.set("main", "audio_source", self.audio_source)
            self.config.set("main", "audio2_source", self.audio2_source)

        self.config.set("main", "countdown_splash", self.countdown_splash)
        self.config.set("main", "counter", self.countdown_timer)
        self.config.set("main", "codec", self.codec)
        self.config.set("main", "framerate", self.framerate)
        self.config.set("main", "autosave_video", self.autosave_video)
        self.config.set("main", "autosave_video_dir", self.autosave_video_dir)
        self.config.set("main", "autosave_video_file", self.autosave_video_file)
        self.config.set("main", "autosave_picture", self.autosave_picture)
        self.config.set("main", "autosave_picture_dir", self.autosave_picture_dir)
        self.config.set("main", "autosave_picture_file", self.autosave_picture_file)
        self.config.set("main", "shutter_sound", self.shutter_sound)
        self.config.set("main", "shutter_type", self.shutter_type)

        self.config.write()

prefs = Prefs()
