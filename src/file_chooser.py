# file_chooser.py
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

from gi.repository import Gtk

class FileChooser:

    """ Open and load file. """
    @staticmethod
    def open_file(parent, last_view_page, *args):
        def __on_response(_dialog, response):

            """ Run if the user selects a file. """
            if response == Gtk.ResponseType.ACCEPT:
                parent.check_is_image(_dialog.get_file())
                    
            else:
                parent.main_stack.set_visible_child_name(last_view_page)

        dialog = Gtk.FileChooserNative.new(
            title=_('Select a file'),
            parent=parent,
            action=Gtk.FileChooserAction.OPEN
        )

        dialog.set_modal(True)
        dialog.connect('response', __on_response)

        file_filter = Gtk.FileFilter.new()
        file_filter.set_name(_('Supported image files'))
        file_filter.add_mime_type('image/png')
        file_filter.add_mime_type('image/jpeg')
        file_filter.add_mime_type('image/jpg')
        dialog.add_filter(file_filter)

        dialog.show()
    
    @staticmethod
    def save_file(parent, *args):
        def __on_response(_dialog, response):

            """ Run if the user selects a file. """
            if response == Gtk.ResponseType.ACCEPT:
                parent.on_save_file(_dialog.get_file())

        dialog = Gtk.FileChooserNative.new(
            title=_('Select a file'),
            parent=parent,
            action=Gtk.FileChooserAction.SAVE
        )

        dialog.set_modal(True)
        dialog.connect('response', __on_response)
        dialog.set_current_name('output.txt')
        dialog.show()

