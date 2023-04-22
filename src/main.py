# main.py
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

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw, GLib
from .window import AsciiimagesWindow

class AsciiimagesApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='io.gitlab.gregorni.ASCIIImages',
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.create_action('quit', self.__quit, ['<primary>q'])
        self.create_action('open-menu', self.__open_menu, ['F10'])
        self.create_action('about', self.__on_about_action)
        self.create_action('open-file', self.__open_file, ['<primary>o'])
        self.create_action('open-output', self.__open_output, param=GLib.VariantType('s'))
        self.file = None
        
    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = AsciiimagesWindow(application=self)
        win.present()
        if self.file is not None:
            win.check_is_image(Gio.File.new_for_path(self.file))

    def __open_file(self, *args):
        self.props.active_window.on_open_file()
        
    def __open_output(self, app, data):
        file_path = data.unpack()
        file = open(file_path, 'r')
        fid = file.fileno()
        connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        proxy = Gio.DBusProxy.new_sync(connection,
                                       Gio.DBusProxyFlags.NONE,
                                       None,
                                       'org.freedesktop.portal.Desktop',
                                       '/org/freedesktop/portal/desktop',
                                       'org.freedesktop.portal.OpenURI',
                                       None)

        try:
            proxy.call_with_unix_fd_list_sync('OpenFile',
                                              GLib.Variant('(sha{sv})', ('', 0, {'ask': GLib.Variant('b', True)})),
                                              Gio.DBusCallFlags.NONE,
                                              -1,
                                              Gio.UnixFDList.new_from_array([fid]),
                                              None)
        except Exception as e:
            print(f'Error: {e}')

    def __open_menu(self, *args):
        self.props.active_window.menu_button.activate()

    def do_command_line(self, command_line):
        args = command_line.get_arguments()
        if len(args) > 1:
            self.file = command_line.create_file_for_arg(args[1]).get_path()
        self.activate()
        return 0
        
    def __quit(self, *args):
        win = self.props.active_window
        if win:
            win.destroy()

    def __on_about_action(self, *args):
    
        """ If you contributed code or translations,
            feel free to add yourself to the appropriate list.
            To add yourself into the list, you can add your
            name/username, and optionally an email or URL:

            Name only:    gregorni
            Name + URL:   gregorni https://gitlab.com/gregorni/
            Name + Email: gregorni <gregorniehl@web.de>
        """
        # This is a Python list: Add your string to the list (separated by a comma)
        devs_list = ['gregorni https://gitlab.com/gregorni']
        # This is a string: Add your name to the string (separated by a newline '\n')
        translators_list = 'gregorni https://gitlab.com/gregorni\nIrénée Thirion\nAlbano Battistella https://gitlab.com/albanobattistella\nQuentin PAGÈS https://github.com/mejans\nFyodor Sobolev https://github.com/fsobolev'
        
        """Callback for the app.about action."""
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='ASCII Images',
                                application_icon='io.gitlab.gregorni.ASCIIImages',
                                developer_name=_('ASCII Images Contributors'),
                                version='1.2.0',
                                developers=devs_list,
                                translator_credits=translators_list,
                                copyright=_('Copyright © 2023 ASCII Images Contributors'),
                                license_type=Gtk.License.GPL_3_0,
                                website='https://gitlab.com/gregorni/ASCIIImages',
                                issue_url='https://gitlab.com/gregorni/ASCIIImages/-/issues',
                                support_url='https://matrix.to/#/#ASCIIImages:matrix.org')
                                
        about.add_credit_section(
            _('Icon by'),
            ['Jakub Steiner https://jimmac.eu']
        )
        
        about.add_acknowledgement_section(
            _('Code and Design Borrowed from'),
            [
                'Upscaler https://gitlab.com/TheEvilSkeleton/Upscaler',
                'Frog https://github.com/TenderOwl/Frog',
            ]
        )
        
        about.add_legal_section(
            title='jp2a',
            copyright='Copyright © 2020 Christoph Raitzig',
            license_type=Gtk.License.GPL_2_0,
        )
        
        about.present()

    def create_action(self, name, callback, shortcuts=None, param=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
            param: an optional list of parameters for the action
        """
        action = Gio.SimpleAction.new(name, param)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

def main(version):
    """The application's entry point."""
    app = AsciiimagesApplication()
    return app.run(sys.argv)

