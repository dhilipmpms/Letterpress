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

from gi.repository import Adw, Gio, GLib, Gtk


class FileChooser:
    """Open and load file."""

    @staticmethod
    def open_file(parent, last_view_page, *args):
        def __on_response(_dialog, response):
            """Run if the user selects a file."""
            if response == Gtk.ResponseType.ACCEPT:
                parent.check_is_image(_dialog.get_file())
            else:
                parent.main_stack.set_visible_child_name(last_view_page)

        dialog = Gtk.FileChooserNative.new(
            title=_("Select a file"), parent=parent, action=Gtk.FileChooserAction.OPEN
        )

        dialog.set_modal(True)
        dialog.connect("response", __on_response)

        file_filter = Gtk.FileFilter.new()
        file_filter.set_name(_("Supported image files"))
        file_filter.add_mime_type("image/png")
        file_filter.add_mime_type("image/jpeg")
        dialog.add_filter(file_filter)

        dialog.show()

    @staticmethod
    def save_file(parent, *args):
        def __on_save_file(file):
            print(f"Output file: {file.get_path()}")
            text = parent.output_label.get_label()
            if text != None:
                file.replace_contents_bytes_async(
                    contents=GLib.Bytes.new(text.encode("utf-8")),
                    etag=None,
                    make_backup=False,
                    flags=Gio.FileCreateFlags.NONE,
                    cancellable=None,
                    callback=__save_file_complete,
                )

        def __save_file_complete(file, result):
            info = file.query_info(
                "standard::display-name", Gio.FileQueryInfoFlags.NONE
            )
            display_name = (
                info.get_attribute_string("standard::display-name")
                if info != None
                else file.get_basename()
            )

            toast = Adw.Toast(
                # Translators: Do not translate "{display_name}"
                title=_('Unable to save "{display_name}"').format(
                    display_name=display_name
                )
            )
            if not file.replace_contents_finish(result):
                print(f"Unable to save {display_name}")
            else:
                toast.set_title(
                    # Translators: Do not translate "{display_name}"
                    _('"{display_name}" saved').format(display_name=display_name)
                )
                toast.set_button_label(_("Open"))
                toast.set_action_name("app.open-output")
                toast.set_action_target_value(GLib.Variant("s", file.get_path()))
            parent.toast_overlay.add_toast(toast)

        def __on_response(_dialog, response):
            """Run if the user selects a file."""
            if response == Gtk.ResponseType.ACCEPT:
                __on_save_file(_dialog.get_file())

        dialog = Gtk.FileChooserNative.new(
            title=_("Select a file"), parent=parent, action=Gtk.FileChooserAction.SAVE
        )

        dialog.set_modal(True)
        dialog.connect("response", __on_response)
        dialog.set_current_name("output.txt")
        dialog.show()
