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

from gi.repository import Adw, Gtk, Gio, GLib, Gdk
from .file_chooser import FileChooser
from .error_dialog import ErrorDialog
from .zoom_box import ZoomBox

from os.path import basename
from filecmp import cmp
import subprocess

@Gtk.Template(resource_path='/io/gitlab/gregorni/ASCIIImages/gtk/window.ui')
class LetterpressWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'LetterpressWindow'
    
    menu_btn = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    welcome_illustration = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    output_text_view = Gtk.Template.Child()
    to_file_btn = Gtk.Template.Child()
    to_clipboard_btn = Gtk.Template.Child()
    width_spin = Gtk.Template.Child()
    width_row = Gtk.Template.Child()
    toolbox = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        content = Gdk.ContentFormats.new_for_gtype(Gio.File)
        self.target = Gtk.DropTarget(formats=content, actions=Gdk.DragAction.COPY)
        
        self.target.connect('drop', self.__on_drop)
        self.target.connect('enter', self.__on_enter)
        self.target.connect('leave', self.__on_leave)
        self.add_controller(self.target)
        
        settings = Gio.Settings(schema_id='io.gitlab.gregorni.ASCIIImages')
        settings.bind('width', self, 'default-width',
                           Gio.SettingsBindFlags.DEFAULT)
        settings.bind('height', self, 'default-height',
                           Gio.SettingsBindFlags.DEFAULT)
        settings.bind('is-maximized', self, 'maximized',
                           Gio.SettingsBindFlags.DEFAULT)

        settings.bind('output-width', self.width_spin, 'value',
                           Gio.SettingsBindFlags.DEFAULT)
        self.width_adj = Gtk.Adjustment.new(settings['output-width'],
                                            100, 2000, 10, 100, 0)
        self.width_spin.set_adjustment(self.width_adj)
        
        self.to_clipboard_btn.connect('clicked', self.__copy_output_to_clipboard)
        self.to_file_btn.connect('clicked', self.__save_output_to_file)
        self.width_spin.connect('value-changed', self.__on_spin_value_changed)
        
        file = Gio.File.new_for_uri('resource:///io/gitlab/gregorni/ASCIIImages/assets/welcome.svg')
        self.welcome_illustration.set_file(file)

        self.buffer = self.output_text_view.get_buffer()
        self.previous_stack = 'welcome'
        self.file = None

        self.zoom_box = ZoomBox()
        self.menu_btn.props.popover.add_child(self.zoom_box, 'zoom')

    def do_size_allocate(self, width, height, baseline):
        if width < 350:
            self.width_row.set_subtitle('')
        else:
            self.width_row.set_subtitle(_('Width of the ASCII image in characters'))

        Adw.ApplicationWindow.do_size_allocate(self, width, height, baseline)

    def on_open_file(self):
        self.__show_spinner()
        FileChooser.open_file(self, self.previous_stack)
        
    def __on_open_error(self, error, file_path):
        if error:
            print(f'Unable to open file, {error}')
            # Translators: Do not translate "{basename}"
            self.toast_overlay.add_toast(Adw.Toast.new(_('"{basename}" is not a valid image.').format(basename=basename(file_path))))
            self.main_stack.set_visible_child_name(self.previous_stack)
            
    def check_is_image(self, file):
        self.__show_spinner()
        
        if self.file and file:
            if cmp(self.file.get_path(), file.get_path()):
                self.main_stack.set_visible_child_name(self.previous_stack)
                return
        
        print(f'Input file: {file.get_path()}')
        
        try:
            Gdk.Texture.new_from_file(file) # Just to see if that's a valid image
        except GLib.Error as error:
            self.__on_open_error(error, file.get_path())
            return
            
        self.file = file
        self.__convert_image(file)
        
    def zoom(self, zoom_out=False, zoom_reset=False):
        new_font_size_percent = int(self.zoom_box.zoom_indicator.get_label()[:-1])
        if zoom_out:
            new_font_size_percent -= 11
        elif zoom_reset:
            new_font_size_percent = 100
        else:
            new_font_size_percent += 11

        if new_font_size_percent < 1 or new_font_size_percent > 100 or not self.zoom_box.get_sensitive():
            return

        self.zoom_box.decrease_btn.set_sensitive(new_font_size_percent > 1)
        self.zoom_box.increase_btn.set_sensitive(new_font_size_percent < 100)

        css_provider = Gtk.CssProvider.new()
        css_provider.load_from_data(f'textview{{font-size:{new_font_size_percent / 10 + 1}pt;}}', -1)
        context = self.output_text_view.get_style_context() # get_style_context will be deprecated in Gtk 4.10
        context.add_provider(css_provider, 10)

        self.zoom_box.zoom_indicator.set_label(f'{new_font_size_percent}%')

    def __convert_image(self, file):
        file = file.get_path()
        
        process = subprocess.Popen(['jp2a', f'--width={self.width_spin.get_value()}', file],
                                   stdout=subprocess.PIPE, universal_newlines=True)
        self.image_as_text = self.__read_lines(process)
        self.buffer.set_text(self.image_as_text)
        
        self.toolbox.set_reveal_child(True)
        self.main_stack.set_visible_child_name('view-page')
        self.previous_stack = 'view-page'
        
        self.zoom_box.set_sensitive(True)
        self.zoom_box.increase_btn.set_sensitive(False)

    def __read_lines(self, process):
        output = ''
        for line in iter(process.stdout.readline, ''):
            output += line
        return output
        
    def __copy_output_to_clipboard(self, *args):
        if self.buffer.get_char_count() > 262088:
            ErrorDialog.too_large(self)
            return
        Gdk.Display.get_default().get_clipboard().set(self.image_as_text)
        self.toast_overlay.add_toast(Adw.Toast(title=_('Output copied to clipboard')))
        
    def __save_output_to_file(self, *args):
        FileChooser.save_file(self)
        
    def on_save_file(self, file):
        print(f'Output file: {file.get_path()}')
        buffer = self.output_text_view.get_buffer()
        # Retrieve the iterator at the start of the buffer
        start = buffer.get_start_iter()
        # Retrieve the iterator at the end of the buffer
        end = buffer.get_end_iter()
        # Retrieve all the visible text between the two bounds
        text = buffer.get_text(start, end, False)
        # If there is nothing to save, return early
        if not text:
            return
        bytes = GLib.Bytes.new(text.encode('utf-8'))
        # Start the asynchronous operation to save the data into the file
        file.replace_contents_bytes_async(bytes,
                                          None,
                                          False,
                                          Gio.FileCreateFlags.NONE,
                                          None,
                                          self.__save_file_complete)
                                          
    def __save_file_complete(self, file, result):
        res = file.replace_contents_finish(result)
        info = file.query_info('standard::display-name',
                               Gio.FileQueryInfoFlags.NONE)
        if info:
            display_name = info.get_attribute_string('standard::display-name')
        else:
            display_name = file.get_basename()
        if not res:
            print(f'Unable to save {display_name}')
            # Translators: Do not translate "{display_name}"
            self.toast_overlay.add_toast(Adw.Toast(title=_('Unable to save "{display_name}"').format(display_name=display_name)))
        else:
            # Translators: Do not translate "{display_name}"
            toast = Adw.Toast(title=_('"{display_name}" saved').format(display_name=display_name))
            toast.set_button_label(_('Open'))
            toast.props.action_name = 'app.open-output'
            toast.props.action_target = GLib.Variant('s', file.get_path())
            self.toast_overlay.add_toast(toast)
                                          
    def __on_spin_value_changed(self, spin_button):
        self.__show_spinner()
        self.__convert_image(self.file)
        
    def __show_spinner(self):
        self.main_stack.set_visible_child_name('spinner-page')
        self.spinner.start()
        
    def __on_drop(self, _, file, *args):
        self.check_is_image(file)
        
    def __on_enter(self, *args):
        self.previous_stack = self.main_stack.get_visible_child_name()
        self.main_stack.set_visible_child_name('drop-page')
        return Gdk.DragAction.COPY
    
    def __on_leave(self, *args):
        self.main_stack.set_visible_child_name(self.previous_stack)

