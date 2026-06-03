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
from PIL import Image

from . import supported_formats


class FileChooser:
    """Open and load file."""

    @staticmethod
    def open_file(parent, last_view_page, *args):
        def __on_response(_dialog, result):
            """Run if the user selects a file."""
            try:
                parent.check_is_image(_dialog.open_finish(result))
            except GLib.GError:
                parent.main_stack.set_visible_child_name(last_view_page)

        dialog = Gtk.FileDialog.new()

        file_filters = Gio.ListStore.new(Gtk.FileFilter)
        file_filter = Gtk.FileFilter.new()
        file_filter.set_name(_("Supported image files"))
        for file_format in supported_formats.formats:
            file_filter.add_mime_type(f"image/{file_format}")
        file_filters.append(file_filter)
        dialog.set_filters(file_filters)

        dialog.open(callback=__on_response, parent=parent)

    @staticmethod
    def save_file(parent, *args):
        def __on_save_file(file):
            filepath = file.get_path()
            display_name = file.get_basename()
            ext = filepath.split('.')[-1].lower() if '.' in filepath else ''
            
            if ext in ['png', 'jpg', 'jpeg', 'webp']:
                success = False
                try:
                    surface = parent.render_output_to_surface()
                    if surface:
                        if ext == 'png':
                            surface.write_to_png(filepath)
                            success = True
                        else:
                            width = surface.get_width()
                            height = surface.get_height()
                            data = surface.get_data()
                            img = Image.frombuffer("RGBA", (width, height), data, "raw", "BGRA", 0, 1)
                            if ext in ['jpg', 'jpeg']:
                                img.convert("RGB").save(filepath, "JPEG")
                                success = True
                            elif ext == 'webp':
                                img.save(filepath, "WEBP")
                                success = True
                except Exception as e:
                    print(f"Error saving image: {e}")
                    success = False
                
                toast = Adw.Toast()
                if success:
                    toast.set_title(_("“{display_name}” saved").format(display_name=display_name))
                    toast.set_button_label(_("Open"))
                    toast.set_action_name("app.open-output")
                    toast.set_action_target_value(GLib.Variant("s", filepath))
                else:
                    toast.set_title(_("Unable to save “{display_name}”").format(display_name=display_name))
                parent.toast_overlay.add_toast(toast)
            else:
                text = parent.output_text
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
                title=_("Unable to save “{display_name}”").format(
                    display_name=display_name
                )
            )
            if not file.replace_contents_finish(result):
                print(f"Unable to save {display_name}")
            else:
                toast.set_title(
                    # Translators: Do not translate "{display_name}"
                    _("“{display_name}” saved").format(display_name=display_name)
                )
                toast.set_button_label(_("Open"))
                toast.set_action_name("app.open-output")
                toast.set_action_target_value(GLib.Variant("s", file.get_path()))
            parent.toast_overlay.add_toast(toast)

        def __on_response(_dialog, result):
            """Run if the user selects a file."""
            try:
                __on_save_file(_dialog.save_finish(result))
            except GLib.GError:
                pass

        dialog = Gtk.FileDialog.new()
        dialog.set_initial_name("output.txt")
        
        file_filters = Gio.ListStore.new(Gtk.FileFilter)
        
        # Plain text filter
        txt_filter = Gtk.FileFilter.new()
        txt_filter.set_name(_("Plain Text (.txt)"))
        txt_filter.add_mime_type("text/plain")
        txt_filter.add_pattern("*.txt")
        file_filters.append(txt_filter)
        
        # Image filter
        img_filter = Gtk.FileFilter.new()
        img_filter.set_name(_("Images (.png, .jpg, .webp)"))
        img_filter.add_mime_type("image/png")
        img_filter.add_mime_type("image/jpeg")
        img_filter.add_mime_type("image/webp")
        img_filter.add_pattern("*.png")
        img_filter.add_pattern("*.jpg")
        img_filter.add_pattern("*.jpeg")
        img_filter.add_pattern("*.webp")
        file_filters.append(img_filter)
        
        dialog.set_filters(file_filters)
        dialog.save(callback=__on_response, parent=parent)
