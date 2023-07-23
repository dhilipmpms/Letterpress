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
import tempfile
from os import path

from gi.repository import Adw, Gdk, Gio, GLib, Gtk
from PIL import Image, ImageChops, ImageOps

from .file_chooser import FileChooser


@Gtk.Template(resource_path="/io/gitlab/gregorni/ASCIIImages/gtk/window.ui")
class LetterpressWindow(Adw.ApplicationWindow):
    __gtype_name__ = "LetterpressWindow"

    menu_btn = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    output_text_view = Gtk.Template.Child()
    to_file_btn = Gtk.Template.Child()
    to_clipboard_btn = Gtk.Template.Child()
    width_row = Gtk.Template.Child()
    width_spin = Gtk.Template.Child()
    toolbox = Gtk.Template.Child()
    gesture_zoom = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.style_manager = Adw.StyleManager.get_default()
        self.style_manager.connect("notify", self.__set_color_scheme)

        target = Gtk.DropTarget(
            formats=Gdk.ContentFormats.new_for_gtype(Gio.File),
            actions=Gdk.DragAction.COPY,
        )

        target.connect("drop", self.__on_drop)
        target.connect("enter", self.__on_enter)
        target.connect("leave", self.__on_leave)
        self.add_controller(target)

        settings = Gio.Settings(schema_id="io.gitlab.gregorni.ASCIIImages")
        settings.bind("width", self, "default-width", Gio.SettingsBindFlags.DEFAULT)
        settings.bind("height", self, "default-height", Gio.SettingsBindFlags.DEFAULT)
        settings.bind("is-maximized", self, "maximized", Gio.SettingsBindFlags.DEFAULT)

        settings.bind(
            "output-width", self.width_spin, "value", Gio.SettingsBindFlags.DEFAULT
        )
        self.width_spin.set_adjustment(
            Gtk.Adjustment.new(settings["output-width"], 100, 5000, 10, 100, 0)
        )

        self.to_clipboard_btn.connect("clicked", self.__copy_output_to_clipboard)
        self.to_file_btn.connect("clicked", self.__save_output_to_file)
        self.width_spin.connect("value-changed", self.__on_spin_value_changed)

        self.gesture_zoom.connect("scale-changed", self.__on_gesture)
        self.scale_delta = 1

        self.buffer = self.output_text_view.get_buffer()
        self.previous_stack = "welcome"
        self.file = None

        self.zoom_box = ZoomBox()
        self.menu_btn.props.popover.add_child(self.zoom_box, "zoom")

    def do_size_allocate(self, width, height, baseline):
        self.width_row.set_subtitle(_("Width of the ASCII image in characters"))
        if width < 350:
            self.width_row.set_subtitle("")

        Adw.ApplicationWindow.do_size_allocate(self, width, height, baseline)

    def on_open_file(self):
        self.__show_spinner()
        FileChooser.open_file(self, self.previous_stack)

    def check_is_image(self, file):
        self.__show_spinner()

        if self.file and file:
            if not ImageChops.difference(
                Image.open(self.file).convert("RGB"),
                Image.open(file.get_path()).convert("RGB"),
            ).getbbox():
                self.main_stack.set_visible_child_name(self.previous_stack)
                return

        print(f"Input file: {file.get_path()}")

        def __wrong_image_type():
            print(f"{file.get_path()} is not of a supported image type.")
            self.toast_overlay.add_toast(
                Adw.Toast.new(
                    # Translators: Do not translate "{basename}"
                    _('"{basename}" is not of a supported image type.').format(
                        basename=path.basename(file.get_path())
                    )
                )
            )
            self.main_stack.set_visible_child_name(self.previous_stack)

        try:
            img = Image.open(file.get_path())
            image_format = img.format
            if image_format in ["JPEG", "PNG"]:
                self.file = f"{tempfile.NamedTemporaryFile().name}img.{image_format}"
                img = ImageOps.exif_transpose(img)
                img.save(self.file, format=image_format)

                self.__convert_image(self.file)
            else:
                __wrong_image_type()
        except IOError:
            __wrong_image_type()

    def zoom(self, zoom_out=False, zoom_reset=False, step=11):
        if self.zoom_box.get_sensitive():
            new_font_size_percent = int(self.zoom_box.zoom_indicator.get_label()[:-1])
            if zoom_out:
                new_font_size_percent -= step
            elif zoom_reset:
                new_font_size_percent = int(
                    round((min(2000 / self.width_spin.get_value(), 11) - 1) * 10, 0)
                )
            else:
                new_font_size_percent += step

            new_font_size_percent = min(max(new_font_size_percent, 1), 100)

            css_provider = Gtk.CssProvider.new()
            css_provider.load_from_data(
                f"textview{{font-size:{new_font_size_percent / 10 + 1}pt;}}", -1
            )
            context = (
                self.output_text_view.get_style_context()
            )  # get_style_context will be deprecated in Gtk 4.10
            context.add_provider(css_provider, 10)

            self.zoom_box.zoom_indicator.set_label(f"{new_font_size_percent}%")
            self.zoom_box.decrease_btn.set_sensitive(new_font_size_percent > 1)
            self.zoom_box.increase_btn.set_sensitive(new_font_size_percent < 100)

    def __convert_image(self, file):
        file = file.get_path()

        arguments = [
            "artem",
            f"--size={int(self.width_spin.get_value())}",
            "--ratio=0.5",
            file,
        ]
        if not self.style_manager.get_dark():
            arguments.append("--invert")

        process = subprocess.Popen(
            arguments,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )

        self.image_as_text = ""
        for line in iter(process.stdout.readline, ""):
            self.image_as_text += line
        self.buffer.set_text(self.image_as_text)

        self.toolbox.set_reveal_child(True)
        self.main_stack.set_visible_child_name("view-page")
        self.previous_stack = "view-page"

        self.zoom_box.set_sensitive(True)
        self.zoom(zoom_reset=True)

    def __copy_output_to_clipboard(self, *args):
        if self.buffer.get_char_count() > 262088:
            dialog = Adw.MessageDialog(
                transient_for=self,
                heading=_("The output is too large to be copied."),
                body=_(
                    "Please save it to a file instead or decrease the output width."
                ),
            )
            dialog.add_response("ok", _("_OK"))
            dialog.present()
            return
        Gdk.Display.get_default().get_clipboard().set(self.image_as_text)
        self.toast_overlay.add_toast(Adw.Toast(title=_("Output copied to clipboard")))

    def __save_output_to_file(self, *args):
        FileChooser.save_file(self)

    def __on_gesture(self, gesture, scale, *args):
        if scale != self.scale_delta:
            self.zoom(
                zoom_out=scale < self.scale_delta,
                step=max(int(abs(scale - self.scale_delta) * 100), 1),
            )
        self.scale_delta = scale

    def __set_color_scheme(self, *args):
        if self.file:
            self.__convert_image(self.file)

    def __on_spin_value_changed(self, spin_button):
        self.__show_spinner()
        self.__convert_image(self.file)

    def __show_spinner(self):
        self.main_stack.set_visible_child_name("spinner-page")
        self.spinner.start()

    def __on_drop(self, widget, file, *args):
        self.check_is_image(file)

    def __on_enter(self, *args):
        self.previous_stack = self.main_stack.get_visible_child_name()
        self.main_stack.set_visible_child_name("drop-page")
        return Gdk.DragAction.COPY

    def __on_leave(self, *args):
        self.main_stack.set_visible_child_name(self.previous_stack)


@Gtk.Template(resource_path="/io/gitlab/gregorni/ASCIIImages/gtk/zoom-box.ui")
class ZoomBox(Gtk.Box):
    __gtype_name__ = "ZoomBox"

    zoom_indicator = Gtk.Template.Child()
    decrease_btn = Gtk.Template.Child()
    increase_btn = Gtk.Template.Child()
