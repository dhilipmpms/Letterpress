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

from . import texture_to_file
from .file_chooser import FileChooser


@Gtk.Template(resource_path="/io/gitlab/gregorni/Letterpress/gtk/window.ui")
class LetterpressWindow(Adw.ApplicationWindow):
    __gtype_name__ = "LetterpressWindow"

    menu_btn = Gtk.Template.Child()
    drag_revealer = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    output_scrolled_window = Gtk.Template.Child()
    output_label = Gtk.Template.Child()
    width_spin = Gtk.Template.Child()
    toolbox = Gtk.Template.Child()
    gesture_zoom = Gtk.Template.Child()
    scroll_controller = Gtk.Template.Child()

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

        self.scroll_controller.connect("scroll", self.__on_scroll)

        self.previous_stack = "welcome"
        self.filepath = None

        self.zoom_box = ZoomBox()
        self.menu_btn.props.popover.add_child(self.zoom_box, "zoom")
        self.pinch_counter = 0
        self.scrolled = 0

        self.heights = (0, 0)

    def do_size_allocate(self, width, height, baseline):
        if self.main_stack.get_visible_child_name() == "view-page":
            new_heights = (height, self.output_scrolled_window.get_height())
            if self.heights != new_heights:
                self.zoom(zoom_reset=True)
                self.heights = new_heights

        Adw.ApplicationWindow.do_size_allocate(self, width, height, baseline)

    def on_open_file(self):
        self.main_stack.set_visible_child_name("spinner-page")
        FileChooser.open_file(self, self.previous_stack)

    def check_is_image(self, file):
        filepath = file.get_path()

        def __wrong_image_type():
            print(f"{filepath} is not of a supported image type.")
            # Translators: Do not translate "{basename}"
            toast_text = _('"{basename}" is not of a supported image type.').format(
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

                if img.format in ["JPEG", "PNG"]:
                    self.filepath = NamedTemporaryFile(suffix=f".{img.format}").name

                    shrunken_img = ImageOps.cover(img, (500, 500))
                    exif_rotated_img = ImageOps.exif_transpose(shrunken_img)
                    exif_rotated_img.save(self.filepath, format=img.format)

                    self.__convert_image(self.filepath)
                    self.zoom(zoom_reset=True)
                else:
                    __wrong_image_type()
        except IOError:
            __wrong_image_type()

    def zoom(self, zoom_out=False, zoom_reset=False):
        if self.zoom_box.get_sensitive():
            if zoom_reset:
                available_height = self.output_scrolled_window.get_width()
                available_width = self.output_scrolled_window.get_height()

                output_width_in_chars = self.width_spin.get_value()
                output_height_in_lines = len(self.output_label.get_label().splitlines())

                norm_char_width = 0.75
                norm_char_height = 1.5

                norm_max_width = (
                    available_width / output_width_in_chars / norm_char_width
                )
                norm_max_height = (
                    available_height / output_height_in_lines / norm_char_height
                )

                requested_font_size = int(min(norm_max_height, norm_max_width))
            else:
                current_font_size = int(self.zoom_box.zoom_indicator.get_label()[:-2])
                requested_font_size = current_font_size + (-1 if zoom_out else 1)

            max_font_size = 11
            min_font_size = 1

            new_font_size = min(max_font_size, max(min_font_size, requested_font_size))
            new_font_size_str = f"{new_font_size}pt"

            line_height = 1
            match new_font_size:
                case 5 | 8 | 9 | 10:
                    line_height = 0.9
                case 3 | 4:
                    line_height = 0.8
                case 1:
                    line_height = 0.7

            css_provider = Gtk.CssProvider.new()
            css_provider.load_from_string(
                f"""label {{
                    font-size: {new_font_size_str};
                    line-height: {line_height};
                }}"""
            )
            self.output_label.get_style_context().add_provider(css_provider, 10)

            self.zoom_box.zoom_indicator.set_label(new_font_size_str)
            self.zoom_box.decrease_btn.set_sensitive(new_font_size > 1)
            self.zoom_box.increase_btn.set_sensitive(new_font_size < 11)

    def __convert_image(self, filepath):
        self.main_stack.set_visible_child_name("spinner-page")

        arguments = ["jp2a", f"--width={self.width_spin.get_value()}", filepath]
        if not self.style_manager.get_dark():
            arguments.append("--invert")

        output = subprocess.Popen(
            arguments,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        ).stdout.readline

        joint_output = "".join(line for line in iter(output, ""))
        self.output_label.set_label(joint_output)

        self.toolbox.set_reveal_child(True)
        self.main_stack.set_visible_child_name("view-page")
        self.previous_stack = "view-page"

        self.zoom_box.set_sensitive(True)

    def __on_gesture(self, gesture, scale, *args):
        self.pinch_counter += 1
        scale_changed = scale != self.scale_delta
        change_is_big_enough = self.pinch_counter >= 6

        if scale_changed and change_is_big_enough:
            self.zoom(zoom_out=scale < self.scale_delta)
            self.scale_delta = scale
            self.pinch_counter = 0

    def __on_scroll(self, scroll, dx, dy, *args):
        ctrl_is_held = scroll.get_current_event_state() == Gdk.ModifierType.CONTROL_MASK
        device_is_mouse = (
            scroll.get_current_event_device().get_source() == Gdk.InputSource.MOUSE
        )

        if ctrl_is_held and device_is_mouse:
            self.scrolled += abs(dy)
            if self.scrolled >= 1:
                self.zoom(zoom_out=dy > 0)
                self.scrolled = 0

    def __set_color_scheme(self, *args):
        if self.filepath is not None:
            self.__convert_image(self.filepath)

    def __on_spin_value_changed(self, spin_button):
        self.main_stack.set_visible_child_name("spinner-page")
        self.__convert_image(self.filepath)
        self.zoom(zoom_reset=True)

    def __on_enter(self, *args):
        self.drag_revealer.set_reveal_child(True)
        return Gdk.DragAction.COPY

    def __on_drop(self, widget, drop, *args):
        failed_as_file = False
        try:
            self.check_is_image(drop)
        except:
            failed_as_file = True

        if failed_as_file:
            try:
                file = texture_to_file.to_file(drop)
                self.check_is_image(file)
            except:
                toast = Adw.Toast.new(_("Dropped item is not a valid image"))
                self.toast_overlay.add_toast(toast)


@Gtk.Template(resource_path="/io/gitlab/gregorni/Letterpress/gtk/zoom-box.ui")
class ZoomBox(Gtk.Box):
    __gtype_name__ = "ZoomBox"

    zoom_indicator = Gtk.Template.Child()
    decrease_btn = Gtk.Template.Child()
    increase_btn = Gtk.Template.Child()
