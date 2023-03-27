# file_chooser.py
#
# Copyright 2023 ASCII Images Contributors
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

from gi.repository import Gtk, Adw

class ErrorDialog():
    
    @staticmethod
    def too_large(parent, *args):
        
        def __on_response(_dialog, response):
            _dialog.close()
        
        # Replace with Gtk.AlertDialog for Gtk 4.10
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            buttons=Gtk.ButtonsType(1),
            text=_('The output is too large to be copied.'),
            secondary_text=_('Please save it to a file instead or decrease the output width.'),
        )
        
        dialog.connect('response', __on_response)

        dialog.show()
