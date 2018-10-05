# -*- coding: utf-8 -*-
#
#       config.py
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
from configparser import ConfigParser, NoSectionError, NoOptionError
from xdg.BaseDirectory import xdg_config_home


class KazamConfig(ConfigParser):

    DEFAULTS = [{
                "name": "main",
                "keys": {"video_toggled":        "True",
                         "video_source":          "0",
                         "audio_toggled":         "False",
                         "audio_source":          "0",
                         "audio_volume":          "0",
                         "audio2_toggled":        "False",
                         "audio2_source":         "0",
                         "audio2_volume":         "0",
                         "codec":                 "0",
                         "counter":               "5",
                         "capture_cursor":        "True",
                         "capture_microphone":    "False",
                         "capture_speakers":      "False",
                         "capture_cursor_pic":    "True",
                         "capture_borders_pic":   "True",
                         "framerate":             "15",
                         "countdown_splash":      "True",
                         "last_x":                "60",
                         "last_y":                "25",
                         "advanced":              "0",
                         "silent":                "0",
                         "autosave_video":        "False",
                         "autosave_video_dir":     "",
                         "autosave_video_file":   "Kazam_screencast",
                         "autosave_picture":      "False",
                         "autosave_picture_dir":   "",
                         "autosave_picture_file":  "Kazam_screenshot",
                         "shutter_sound":          "True",
                         "shutter_type":           "0",
                         "first_run":              "True",
                         },
                },
                {"name": "keyboard_shortcuts",
                 "keys": {"pause":  "<Shift><Control>p",
                          "finish": "<Shift><Control>f",
                          "show":   "<Shift><Control>s",
                          "quit":   "<Shift><Control>q",
                          },
                 }]

    CONFIGDIR = os.path.join(xdg_config_home, "kazam")
    CONFIGFILE = os.path.join(CONFIGDIR, "kazam.conf")

    def __init__(self):
        super().__init__(self)
        if not os.path.isdir(self.CONFIGDIR):
            os.makedirs(self.CONFIGDIR)
        if not os.path.isfile(self.CONFIGFILE):
            self.create_default()
            self.write()
        self.read(self.CONFIGFILE)

    def create_default(self):
        # For every section
        for section in self.DEFAULTS:
            # Add the section
            self.add_section(section["name"])
            # And add every key in it, with its default value
            for key in section["keys"]:
                value = section["keys"][key]
                self.set(section["name"], key, value)

    def find_default(self, section, key):
        for d_section in self.DEFAULTS:
            if d_section["name"] == section:
                for d_key in d_section["keys"]:
                    if d_key == key:
                        return d_section["keys"][key]

    def get(self, section, key, **kwargs):
        try:
            return super().get(section, key, **kwargs)
        except NoSectionError:
            default = self.find_default(section, key)
            self.set(section, key, default)
            self.write()
            return default
        except NoOptionError:
            default = self.find_default(section, key)
            self.set(section, key, default)
            self.write()
            return default

    def getboolean(self, section, key):
        val = self.get(section, key)
        if val.lower() == 'true' or val.lower == "on" or val.lower() == "yes":
            return True
        else:
            return False

    def set(self, section, option, value):
        super().set(section, option, str(value))

    def write(self):
        file_ = open(self.CONFIGFILE, "w")
        ConfigParser.write(self, file_)
        file_.close()


