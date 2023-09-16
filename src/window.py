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

from gi.repository import Adw, Gdk, Gio, Gtk
from PIL import Image, ImageChops, ImageOps

from .file_chooser import FileChooser


@Gtk.Template(resource_path="/io/gitlab/gregorni/Letterpress/gtk/window.ui")
class LetterpressWindow(Adw.ApplicationWindow):
    __gtype_name__ = "LetterpressWindow"

    menu_btn = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    output_scrolled_window = Gtk.Template.Child()
    output_text_view = Gtk.Template.Child()
    width_spin = Gtk.Template.Child()
    toolbox = Gtk.Template.Child()
    gesture_zoom = Gtk.Template.Child()
    conscroller = Gtk.Template.Child()

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

        settings = Gio.Settings(schema_id="io.gitlab.gregorni.Letterpress")
        settings.bind("width", self, "default-width", Gio.SettingsBindFlags.DEFAULT)
        settings.bind("height", self, "default-height", Gio.SettingsBindFlags.DEFAULT)
        settings.bind("is-maximized", self, "maximized", Gio.SettingsBindFlags.DEFAULT)

        settings.bind(
            "output-width", self.width_spin, "value", Gio.SettingsBindFlags.DEFAULT
        )
        self.width_spin.set_adjustment(
            Gtk.Adjustment.new(settings["output-width"], 50, 500, 10, 100, 0)
        )

        self.width_spin.connect("value-changed", self.__on_spin_value_changed)

        self.gesture_zoom.connect("scale-changed", self.__on_gesture)
        self.scale_delta = 1

        self.conscroller.connect("scroll", self.__on_scroll)

        self.buffer = self.output_text_view.get_buffer()
        self.previous_stack = "welcome"
        self.filepath = None

        self.zoom_box = ZoomBox()
        self.menu_btn.props.popover.add_child(self.zoom_box, "zoom")
        self.pinch_counter = 0
        self.scrolled = 0

        self.heights = (0, 0)

    def do_size_allocate(self, width, height, baseline):
        new_heights = (height, self.output_scrolled_window.get_height())
        if self.heights != new_heights:
            self.zoom(zoom_reset=True)
            self.heights = new_heights

        Adw.ApplicationWindow.do_size_allocate(self, width, height, baseline)

    def on_open_file(self):
        self.__show_spinner()
        FileChooser.open_file(self, self.previous_stack)

    def check_is_image(self, file):
        filepath = file.get_path()

        def __wrong_image_type():
            print(f"{filepath} is not of a supported image type.")
            self.toast_overlay.add_toast(
                Adw.Toast.new(
                    # Translators: Do not translate "{basename}"
                    _('"{basename}" is not of a supported image type.').format(
                        basename=file.get_basename()
                    )
                )
            )
            self.main_stack.set_visible_child_name(self.previous_stack)

        try:
            if self.filepath and file:
                with Image.open(self.filepath) as old_img, Image.open(
                    filepath
                ) as new_img:
                    if not ImageChops.difference(
                        old_img.convert("RGB"),
                        new_img.convert("RGB"),
                    ).getbbox():
                        self.main_stack.set_visible_child_name(self.previous_stack)
                        return

            self.__show_spinner()
            print(f"Input file: {filepath}")

            with Image.open(filepath) as img:
                image_format = img.format
                if image_format in ["JPEG", "PNG"]:
                    self.filepath = filepath
                    try:
                        if img._getexif()[274] != 1:
                            self.filepath = (
                                f"{tempfile.NamedTemporaryFile().name}.{image_format}"
                            )
                            ImageOps.exif_transpose(img).save(
                                self.filepath, format=image_format
                            )
                    except:
                        pass

                    self.__convert_image(self.filepath)
                    self.zoom(zoom_reset=True)
                else:
                    __wrong_image_type()
        except IOError:
            __wrong_image_type()

    def zoom(self, zoom_out=False, zoom_reset=False):
        if self.zoom_box.get_sensitive():
            new_font_size = min(
                max(
                    int(
                        min(
                            self.output_scrolled_window.get_width()
                            / self.width_spin.get_value()
                            / 0.75,
                            self.output_scrolled_window.get_height()
                            / self.buffer.get_line_count()
                            / 1.5,
                        )
                    )
                    if zoom_reset
                    else int(self.zoom_box.zoom_indicator.get_label()[:-2])
                    + (-1 if zoom_out else 1),
                    1,
                ),
                11,
            )

            new_font_size_str = f"{new_font_size}pt"

            line_height = 1
            if new_font_size in (5, 8, 9, 10):
                line_height = 0.9
            elif new_font_size in (1, 3, 4):
                line_height = 0.8

            css_provider = Gtk.CssProvider.new()
            css_provider.load_from_data(
                f"""textview{{
                  font-size: {new_font_size_str};
                  line-height: {line_height};
                }}""",
                -1,
            )
            self.output_text_view.get_style_context().add_provider(
                css_provider, 10
            )  # get_style_context will be deprecated in Gtk 4.10

            self.zoom_box.zoom_indicator.set_label(new_font_size_str)
            self.zoom_box.decrease_btn.set_sensitive(new_font_size > 1)
            self.zoom_box.increase_btn.set_sensitive(new_font_size < 11)

    def __convert_image(self, filepath):
        self.__show_spinner()
        arguments = ["jp2a", f"--width={self.width_spin.get_value()}", filepath]
        if not self.style_manager.get_dark():
            arguments.append("--invert")

        self.image_as_text = ""
        for line in iter(
            subprocess.Popen(
                arguments,
                stdout=subprocess.PIPE,
                universal_newlines=True,
            ).stdout.readline,
            "",
        ):
            self.image_as_text += line
        self.buffer.set_text(self.image_as_text)

        self.toolbox.set_reveal_child(True)
        self.main_stack.set_visible_child_name("view-page")
        self.previous_stack = "view-page"

        self.zoom_box.set_sensitive(True)

    def __on_gesture(self, gesture, scale, *args):
        self.pinch_counter += 1
        if scale != self.scale_delta and self.pinch_counter >= 6:
            self.zoom(
                zoom_out=scale < self.scale_delta,
            )
            self.scale_delta = scale
            self.pinch_counter = 0

    def __on_scroll(self, scroll, dx, dy, *args):
        if (
            scroll.get_current_event_state() == Gdk.ModifierType.CONTROL_MASK
            and scroll.get_current_event_device().get_source() == Gdk.InputSource.MOUSE
        ):
            self.scrolled += abs(dy)
            if self.scrolled >= 1:
                self.zoom(zoom_out=dy > 0)
                self.scrolled = 0

    def __set_color_scheme(self, *args):
        if self.filepath:
            self.__convert_image(self.filepath)

    def __on_spin_value_changed(self, spin_button):
        self.__show_spinner()
        self.__convert_image(self.filepath)
        self.zoom(zoom_reset=True)

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


@Gtk.Template(resource_path="/io/gitlab/gregorni/Letterpress/gtk/zoom-box.ui")
class ZoomBox(Gtk.Box):
    __gtype_name__ = "ZoomBox"

    zoom_indicator = Gtk.Template.Child()
    decrease_btn = Gtk.Template.Child()
    increase_btn = Gtk.Template.Child()
