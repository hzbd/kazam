# -*- coding: utf-8 -*-
#
#       window_countdown.py
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
import cairo

from gettext import gettext as _
from gi.repository import Gtk, GObject, GLib

from kazam.backend.prefs import *
from kazam.backend.constants import *

class CountdownWindow(GObject.GObject):

    __gsignals__ = {
        "counter-finished" : (GObject.SIGNAL_RUN_LAST,
                                   None,
                                   (),
                                  ),
    }

    def __init__(self, indicator, number = 5, show_window = True):
        super(CountdownWindow, self).__init__()
        self.indicator = indicator
        self.number = number
        self.canceled = False
        self.show_window = show_window

        self.window = Gtk.Window()
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.connect("draw", self.cb_draw)
        self.width = 380
        self.height = 380
        self.window.set_default_geometry(self.height, self.width)
        self.window.set_default_size(self.width, self.height)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_app_paintable(True)
        self.window.set_has_resize_grip(False)
        self.window.set_resizable(True)

        self.window.set_decorated(False)
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_keep_above(True)
        self.screen = self.window.get_screen()
        self.visual = self.screen.get_rgba_visual()

        if self.visual is not None and self.screen.is_composited():
            self.window.set_visual(self.visual)


    def run(self, counter):
        if counter > 0:
            self.number = counter + 1
            if self.show_window:
                self.window.show_all()
        else:
            self.number = 0
        self.countdown()

    def countdown(self):
        if not self.canceled:
            if self.number < 5:
                self.indicator.blink_set_state(BLINK_FAST)
            if self.number > 1:
                self.window.queue_draw()
                GLib.timeout_add(1000, self.countdown)
                self.number -= 1
            else:
                self.window.destroy()
                GLib.timeout_add(400, self.counter_finished)

    def cancel_countdown(self):
        self.indicator.blink_set_state(BLINK_STOP)
        self.canceled = True
        self.window.destroy()
        self.number = 0

    def counter_finished(self):
        self.emit("counter-finished")
        return False

    def cb_draw(self, widget, cr):
        w = self.width
        h = self.height
        background = cairo.ImageSurface.create_from_png(os.path.join(prefs.datadir, "icons", "counter", "cb-{0}.png".format(int(self.number))))
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.45)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_source_surface(background, 0, 0)
        cr.paint()
