# pasting.py
#
# Copyright 2023 Letterpress Contributors
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

from gi.repository import Adw, Gdk, Gio


class Paster:
    def __on_file_pasted(self, clipboard, result):
        try:
            paste_as_file = clipboard.read_value_finish(result)
            self.callback(paste_as_file)

        except:
            clipboard.read_value_async(Gdk.Texture, 0, None, self.__on_texture_pasted)

    def __on_texture_pasted(self, clipboard, result):
        try:
            paste_as_texture = clipboard.read_value_finish(result)
            save_file = Gio.File.new_tmp()[0]
            save_path = save_file.get_path()
            paste_as_texture.save_to_png(save_path)
            self.callback(save_file)

        except:
            toast = Adw.Toast.new(_("No Image in Clipboard"))
            self.parent_window.toast_overlay.add_toast(toast)

    def paste_image(self, parent_window, callback) -> None:
        self.parent_window = parent_window
        self.callback = callback

        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.read_value_async(Gio.File, 0, None, self.__on_file_pasted)
