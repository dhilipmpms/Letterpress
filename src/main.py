# main.py
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

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from .file_chooser import FileChooser
from .pasting import Paster
from .window import LetterpressWindow
from .tips_dialog import TipsDialog

from .profile import APP_ID, PROFILE


class LetterpressApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            resource_base_path="/io/gitlab/gregorni/Letterpress",
        )
        self.__create_action("quit", lambda *args: self.quit(), ["<primary>q"])
        self.__create_action("tips", self.__on_tips_action)
        self.__create_action("about", self.__on_about_action)
        self.__create_action(
            "open-file",
            lambda *args: self.get_active_window().on_open_file(),
            ["<primary>o"],
        )
        self.__create_action(
            "increase-output-width",
            lambda *args: self.__change_output_width(False),
            ["<primary>plus"],
        )
        self.__create_action(
            "decrease-output-width",
            lambda *args: self.__change_output_width(True),
            ["<primary>minus"],
        )
        self.__create_action("paste-image", self.__paste_image, ["<primary>v"])
        self.__create_action(
            "copy-output", self.__copy_output_to_clipboard, ["<primary>c"]
        )
        self.__create_action(
            "save-output", self.__save_output_to_file, ["<primary>s"]
        )
        self.__create_action(
            "open-output", self.__open_output, param=GLib.VariantType("s")
        )
        self.file = None

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.get_active_window()
        if win == None:
            win = LetterpressWindow(application=self)
        win.present()

        if PROFILE == "development":
            win.add_css_class("devel")

        if self.file != None:
            win.check_is_image(Gio.File.new_for_path(self.file))

    def __paste_image(self, *args):
        win = self.get_active_window()
        Paster().paste_image(win, win.check_is_image)

    def __change_output_width(self, down):
        win = self.get_active_window()
        if win.filepath != None:
            spin_btn = win.width_spin
            spin_btn.set_value(spin_btn.get_value() + (-10 if down else 10))

    def __copy_output_to_clipboard(self, *args):
        win = self.get_active_window()
        if win.filepath is None:
            return
        output_text = win.output_label.get_label()
        Gdk.Display.get_default().get_clipboard().set(output_text)
        win.toast_overlay.add_toast(Adw.Toast(title=_("Output copied to clipboard")))

    def __save_output_to_file(self, *args):
        win = self.get_active_window()
        if win.filepath is None:
            return
        FileChooser.save_file(win)

    def __open_output(self, app, data):
        file = open(data.unpack(), "r")
        Gio.DBusProxy.new_sync(
            connection=Gio.bus_get_sync(Gio.BusType.SESSION, None),
            flags=Gio.DBusProxyFlags.NONE,
            info=None,
            name="org.freedesktop.portal.Desktop",
            object_path="/org/freedesktop/portal/desktop",
            interface_name="org.freedesktop.portal.OpenURI",
            cancellable=None,
        ).call_with_unix_fd_list_sync(
            method_name="OpenFile",
            parameters=GLib.Variant(
                "(sha{sv})", ("", 0, {"ask": GLib.Variant("b", True)})
            ),
            flags=Gio.DBusCallFlags.NONE,
            timeout_msec=-1,
            fd_list=Gio.UnixFDList.new_from_array([file.fileno()]),
            cancellable=None,
        )

    def do_command_line(self, command_line):
        args = command_line.get_arguments()
        if len(args) > 1:
            file = command_line.create_file_for_arg(args[1])
            self.file = file.get_path()
        self.activate()
        return 0

    def __on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog.new_from_appdata(
            "/io/gitlab/gregorni/Letterpress/metainfo.xml", "2.1"
        )
        about.set_artists(
            [
                "Brage Fuglseth https://bragefuglseth.dev",
                "kramo https://kramo.hu",
            ]
        )
        # These are Python lists: Add your string to the list (separated by a comma)
        # See the translator comment below for possible formats
        about.set_developers(["Gregor Niehl https://gitlab.gnome.org/gregorni"])
        about.set_copyright(_("Copyright © 2023 Letterpress Contributors"))
        # Translators: Translate this string as your translator credits.
        # Name only:    Gregor Niehl
        # Name + URL:   Gregor Niehl https://gitlab.gnome.org/gregorni/
        # Name + Email: Gregor Niehl <gregorniehl@web.de>
        # Do not remove existing names.
        # Names are separated with newlines.
        about.set_translator_credits(_("translator-credits"))

        about.add_acknowledgement_section(
            _("Code and Design borrowed from"),
            [
                "Upscaler https://gitlab.gnome.org/World/Upscaler",
                "Frog https://github.com/TenderOwl/Frog",
            ],
        )

        about.add_legal_section(
            title="artem",
            copyright="Copyright © 2022 artem contributors",
            license_type=Gtk.License.MPL_2_0,
        )

        about.present(self.get_active_window())

    def __on_tips_action(self, *args):
        TipsDialog().present(self.get_active_window())

    def __create_action(self, name, callback, shortcuts=None, param=None):
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
    return LetterpressApplication().run(sys.argv)
