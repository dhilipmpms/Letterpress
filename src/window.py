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
import unicodedata
from tempfile import NamedTemporaryFile

from gi.repository import Adw, Gdk, Gio, Gtk, Pango, PangoCairo
import cairo
from PIL import Image, ImageChops, ImageOps

from . import texture_to_file, supported_formats, character_sets
from .file_chooser import FileChooser


def split_graphemes(text):
    graphemes = []
    current = ""
    for char in text:
        is_mark = unicodedata.category(char).startswith('M')
        is_zwj = char == '\u200d'
        is_vs = '\ufe00' <= char <= '\ufe0f'
        was_zwj = current.endswith('\u200d') if current else False
        
        if current and (is_mark or is_zwj or is_vs or was_zwj):
            current += char
        else:
            if current:
                graphemes.append(current)
            current = char
    if current:
        graphemes.append(current)
    return graphemes


def render_ascii_art(text, is_dark_mode=True):
    lines = text.splitlines()
    grid = []
    max_cols = 0
    for line in lines:
        row = split_graphemes(line)
        grid.append(row)
        if len(row) > max_cols:
            max_cols = len(row)
            
    rows = len(grid)
    if rows == 0 or max_cols == 0:
        return cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)

    dummy_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
    dummy_ctx = cairo.Context(dummy_surface)
    dummy_layout = PangoCairo.create_layout(dummy_ctx)
    
    font_desc_str = "monospace, Noto Sans, Noto Sans Tamil, Noto Sans Devanagari, Noto Color Emoji 12"
    font_desc = Pango.FontDescription.from_string(font_desc_str)
    dummy_layout.set_font_description(font_desc)
    
    dummy_layout.set_text("M", -1)
    cell_w, cell_h = dummy_layout.get_pixel_size()
    
    if cell_w == 0:
        cell_w = 10
    if cell_h == 0:
        cell_h = 20

    img_width = max_cols * cell_w
    img_height = rows * cell_h

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, img_width, img_height)
    ctx = cairo.Context(surface)
    
    if is_dark_mode:
        ctx.set_source_rgb(0.07, 0.07, 0.07)
    else:
        ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.paint()

    if is_dark_mode:
        ctx.set_source_rgb(1.0, 1.0, 1.0)
    else:
        ctx.set_source_rgb(0.0, 0.0, 0.0)

    layout = PangoCairo.create_layout(ctx)
    layout.set_font_description(font_desc)
    
    for r in range(rows):
        row = grid[r]
        for c in range(len(row)):
            grapheme = row[c]
            if not grapheme or grapheme.isspace():
                continue
                
            layout.set_text(grapheme, -1)
            lw, lh = layout.get_pixel_size()
            
            if lw == 0 or lh == 0:
                continue
                
            scale_x = cell_w / lw
            scale_y = cell_h / lh
            scale = min(scale_x, scale_y)
            
            ctx.save()
            ctx.translate(c * cell_w + cell_w / 2.0, r * cell_h + cell_h / 2.0)
            ctx.scale(scale, scale)
            ctx.translate(-lw / 2.0, -lh / 2.0)
            PangoCairo.show_layout(ctx, layout)
            ctx.restore()

    return surface


@Gtk.Template(resource_path="/io/gitlab/gregorni/Letterpress/gtk/window.ui")
class LetterpressWindow(Adw.ApplicationWindow):
    __gtype_name__ = "LetterpressWindow"

    menu_btn = Gtk.Template.Child()
    drag_revealer = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    output_scrolled_window = Gtk.Template.Child()
    output_picture = Gtk.Template.Child()
    width_spin = Gtk.Template.Child()
    charset_combo = Gtk.Template.Child()
    toolbox = Gtk.Template.Child()

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

        # Initialize character set combo box
        self.settings = settings
        self.__setup_charset_combo()
        self.charset_combo.connect("changed", self.__on_charset_changed)

        self.previous_stack = "welcome"
        self.filepath = None
        self.output_text = ""
        self.render_temp_file = None

    def __setup_charset_combo(self):
        """Setup the character set combo box with available options."""
        # Clear existing items
        self.charset_combo.remove_all()
        
        # Add all character sets
        charset_data = character_sets.get_all_character_sets()
        for key, data in charset_data.items():
            self.charset_combo.append(key, data["name"])
        
        # Set active from settings
        current_charset = self.settings.get_string("character-set")
        self.charset_combo.set_active_id(current_charset)

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

        arguments = ["artem", f"--size={int(self.width_spin.get_value())}", filepath]
        
        # Add character set argument (only for non-English sets)
        # English uses artem's default character set
        charset_id = self.charset_combo.get_active_id()
        if charset_id and charset_id != "english":
            charset_chars = character_sets.get_character_set(charset_id)
            if charset_chars:
                arguments.insert(1, f"--characters={charset_chars}")
        
        if not self.style_manager.get_dark():
            arguments.append("--invert")

        output = subprocess.Popen(
            arguments,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        ).stdout.readline

        joint_output = "".join(line for line in iter(output, ""))
        self.output_text = joint_output

        try:
            surface = self.render_output_to_surface()
            if surface:
                if not self.render_temp_file:
                    self.render_temp_file = NamedTemporaryFile(suffix=".png").name
                surface.write_to_png(self.render_temp_file)
                texture = Gdk.Texture.new_from_filename(self.render_temp_file)
                self.output_picture.set_paintable(texture)
        except Exception as e:
            print(f"Error rendering output image: {e}")

        self.toolbox.set_reveal_child(True)
        self.previous_stack = "view-page"
        self.main_stack.set_visible_child_name(self.previous_stack)

    def render_output_to_surface(self):
        if not self.output_text:
            return None
        return render_ascii_art(self.output_text, self.style_manager.get_dark())

    def __on_charset_changed(self, combo):
        """Handle character set selection change."""
        charset_id = combo.get_active_id()
        if charset_id:
            self.settings.set_string("character-set", charset_id)
            # Regenerate if image is loaded
            if self.filepath:
                self.__convert_image(self.filepath)

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
