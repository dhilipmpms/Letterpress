# window.py
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

import subprocess
from tempfile import NamedTemporaryFile

from gi.repository import Adw, Gdk, Gio, Gtk
from PIL import Image, ImageChops, ImageOps

from . import texture_to_file, supported_formats
from .file_chooser import FileChooser


@Gtk.Template(resource_path="/io/gitlab/gregorni/Letterpress/gtk/window.ui")
class LetterpressWindow(Adw.ApplicationWindow):
    __gtype_name__ = "LetterpressWindow"

    menu_btn = Gtk.Template.Child()
    drag_revealer = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    output_scrolled_window = Gtk.Template.Child()
    output_label = Gtk.Template.Child()
    width_spin = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.style_manager = Adw.StyleManager.get_default()
        self.style_manager.connect("notify", self.__set_color_scheme)

        target = Gtk.DropTarget(
            formats=Gdk.ContentFormats.new_for_gtype(Gio.File),
            actions=Gdk.DragAction.COPY,
        )

        target.set_gtypes([Gdk.Texture, Gio.File])
        target.connect("drop", self.__on_drop)
        target.connect("enter", self.__on_enter)
        target.connect(
            "leave", lambda *args: self.drag_revealer.set_reveal_child(False)
        )
        self.add_controller(target)

        settings = Gio.Settings(schema_id="io.gitlab.gregorni.Letterpress")
        bind_flags = Gio.SettingsBindFlags.DEFAULT
        settings.bind("window-width", self, "default-width", bind_flags)
        settings.bind("window-height", self, "default-height", bind_flags)
        settings.bind("window-is-maximized", self, "maximized", bind_flags)

        settings.bind(
            "output-width", self.width_spin, "value", Gio.SettingsBindFlags.DEFAULT
        )
        self.width_spin.set_value(settings["output-width"])

        self.width_spin.connect("value-changed", self.__on_spin_value_changed)

        self.previous_stack = "welcome"
        self.filepath = None

    def on_open_file(self):
        self.main_stack.set_visible_child_name("spinner-page")
        FileChooser.open_file(self, self.previous_stack)

    def check_is_image(self, file):
        filepath = file.get_path()

        def __wrong_image_type():
            print(f"{filepath} is not of a supported image type.")
            # Translators: Do not translate "{basename}"
            toast_text = _("“{basename}” is not of a supported image type.").format(
                basename=file.get_basename()
            )
            self.toast_overlay.add_toast(Adw.Toast.new(toast_text))
            self.main_stack.set_visible_child_name(self.previous_stack)

        try:
            with Image.open(filepath) as img:
                if self.filepath and file:
                    with Image.open(self.filepath) as old_img:
                        same_image = not ImageChops.difference(
                            old_img.convert("RGB"), img.convert("RGB")
                        ).getbbox()
                        if same_image:
                            self.main_stack.set_visible_child_name(self.previous_stack)
                            return

                self.main_stack.set_visible_child_name("spinner-page")
                print(f"Input file: {filepath}")

                img_format = img.format
                uppercase_formats = list(
                    map(lambda x: x.upper(), supported_formats.formats)
                )
                if img_format not in uppercase_formats:
                    __wrong_image_type()
                    return

                self.filepath = NamedTemporaryFile(suffix=f".{img_format}").name

                shrunken_img = ImageOps.cover(img, (500, 500))
                exif_rotated_img = ImageOps.exif_transpose(shrunken_img)
                exif_rotated_img.save(self.filepath, format=img_format)

                self.__convert_image(self.filepath)
        except Image.DecompressionBombError:
            print("Warning! Image is HUGE!!")
            self.__convert_image(filepath)
        except IOError:
            __wrong_image_type()

    def __convert_image(self, filepath):
        self.main_stack.set_visible_child_name("spinner-page")

        arguments = ["jp2a", f"--width={int(self.width_spin.get_value())}", filepath]
        # arguments = ["artem", f"--size={int(self.width_spin.get_value())}", filepath]
        if not self.style_manager.get_dark():
            arguments.append("--invert")

        output = subprocess.Popen(
            arguments,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        ).stdout.readline

        joint_output = "".join(line for line in iter(output, ""))
        self.output_label.set_label(joint_output)

        self.previous_stack = "view-page"
        self.main_stack.set_visible_child_name(self.previous_stack)

    def __set_color_scheme(self, *args):
        if self.filepath != None:
            self.__convert_image(self.filepath)

    def __on_spin_value_changed(self, spin_button):
        self.main_stack.set_visible_child_name("spinner-page")
        self.__convert_image(self.filepath)

    def __on_enter(self, *args):
        self.drag_revealer.set_reveal_child(True)
        return Gdk.DragAction.COPY

    def __on_drop(self, widget, drop, *args):
        failed_as_file = False
        try:
            self.check_is_image(drop)
        except:
            failed_as_file = True

        if not failed_as_file:
            return

        try:
            file = texture_to_file.to_file(drop)
            self.check_is_image(file)
        except:
            toast = Adw.Toast.new(_("Dropped item is not a valid image"))
            self.toast_overlay.add_toast(toast)
