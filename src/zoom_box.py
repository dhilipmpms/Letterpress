# zoom_box.py
#
# Copyright 2024 Letterpress Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .zoom_consts import INITIAL_ZOOM, ZOOM_FACTOR, MIN_ZOOM, MAX_ZOOM


@Gtk.Template(resource_path="/io/gitlab/gregorni/Letterpress/gtk/zoom-box.ui")
class ZoomBox(Gtk.Box):
    __gtype_name__ = "ZoomBox"

    zoom_indicator = Gtk.Template.Child()
    decrease_btn = Gtk.Template.Child()
    increase_btn = Gtk.Template.Child()

    def set_zoom(self, zoom_level):
        # map our actual zoom level to a human readable zoom level between 10% and 100%
        display_zoom = (zoom_level - MIN_ZOOM) / (MAX_ZOOM - MIN_ZOOM) * 90 + 10

        self.zoom_indicator.set_label(f"{int(display_zoom)}%")
        self.decrease_btn.set_sensitive(zoom_level > MIN_ZOOM)
        self.increase_btn.set_sensitive(zoom_level < MAX_ZOOM)
