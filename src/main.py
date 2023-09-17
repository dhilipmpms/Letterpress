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
from .window import LetterpressWindow


class LetterpressApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id="io.gitlab.gregorni.Letterpress",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        self.create_action("quit", self.__quit, ["<primary>q"])
        self.create_action(
            "close-active-win",
            lambda *_: self.props.active_window.destroy(),
            ["<primary>w"],
        )
        self.create_action(
            "open-menu", lambda *_: self.win.menu_btn.activate(), ["F10"]
        )
        self.create_action("tips", self.__on_tips_action)
        self.create_action("about", self.__on_about_action)
        self.create_action(
            "open-file", lambda *_: self.win.on_open_file(), ["<primary>o"]
        )
        self.create_action(
            "zoom-out", self.__zoom_out, ["<primary>minus", "<primary>underscore"]
        )
        self.create_action("zoom-in", self.__zoom_in, ["<primary>plus"])
        self.create_action(
            "reset-zoom", self.__reset_zoom, ["<primary>0", "<primary>r"]
        )
        self.create_action(
            "increase-output-width",
            self.__increase_output_width,
            ["<primary><alt>plus"],
        )
        self.create_action(
            "decrease-output-width",
            self.__decrease_output_width,
            ["<primary><alt>minus"],
        )
        self.create_action(
            "copy-output", self.__copy_output_to_clipboard, ["<primary><shift>c"]
        )
        self.create_action(
            "save-output",
            lambda *_: FileChooser.save_file(self.win),
            ["<primary>s", "<primary><shift>c"],
        )
        self.create_action(
            "open-output", self.__open_output, param=GLib.VariantType("s")
        )
        self.create_action("close-tips", self.__close_tips_dialog, ["Escape"])
        self.file = None

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        self.win = self.props.active_window
        if not self.win:
            self.win = LetterpressWindow(application=self)
            self.tips_dialog = None
        self.win.present()
        if self.file is not None:
            self.win.check_is_image(Gio.File.new_for_path(self.file))

    def __zoom_out(self, *args):
        self.win.zoom(zoom_out=True)

    def __zoom_in(self, *args):
        self.win.zoom()

    def __reset_zoom(self, *args):
        self.win.zoom(zoom_reset=True)

    def __increase_output_width(self, *args):
        if self.win.filepath:
            self.win.width_spin.set_value(self.win.width_spin.get_value() + 100)

    def __decrease_output_width(self, *args):
        if self.win.filepath:
            self.win.width_spin.set_value(self.win.width_spin.get_value() - 100)

    def __copy_output_to_clipboard(self, *args):
        Gdk.Display.get_default().get_clipboard().set(self.win.image_as_text)
        self.win.toast_overlay.add_toast(
            Adw.Toast(title=_("Output copied to clipboard"))
        )

    def __open_output(self, app, data):
        try:
            file = open(data.unpack(), "r")
            Gio.DBusProxy.new_sync(
                Gio.bus_get_sync(Gio.BusType.SESSION, None),
                Gio.DBusProxyFlags.NONE,
                None,
                "org.freedesktop.portal.Desktop",
                "/org/freedesktop/portal/desktop",
                "org.freedesktop.portal.OpenURI",
                None,
            ).call_with_unix_fd_list_sync(
                "OpenFile",
                GLib.Variant("(sha{sv})", ("", 0, {"ask": GLib.Variant("b", True)})),
                Gio.DBusCallFlags.NONE,
                -1,
                Gio.UnixFDList.new_from_array([file.fileno()]),
                None,
            )
        except Exception as e:
            print(f"Error: {e}")

    def do_command_line(self, command_line):
        args = command_line.get_arguments()
        if len(args) > 1:
            self.file = command_line.create_file_for_arg(args[1]).get_path()
        self.activate()
        return 0

    def __quit(self, *args):
        if self.win is not None:
            self.win.destroy()

    def __on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(
            transient_for=self.win,
            application_name=_("Letterpress"),
            application_icon="io.gitlab.gregorni.Letterpress",
            developer_name=_("Letterpress Contributors"),
            version="2.0",
            # These are Python lists: Add your string to the list (separated by a comma)
            # See the translator comment below for possible formats
            developers=["gregorni https://gitlab.gnome.org/gregorni"],
            artists=[
                "Brage Fuglseth https://bragefuglseth.dev",
                "kramo https://kramo.hu",
            ],
            # Translators: Translate this string as your translator credits.
            # Name only:    gregorni
            # Name + URL:   gregorni https://gitlab.gnome.org/gregorni/
            # Name + Email: gregorni <gregorniehl@web.de>
            # Do not remove existing names.
            # Names are separated with newlines.
            translator_credits=_("translator-credits"),
            copyright=_("Copyright © 2023 Letterpress Contributors"),
            license_type=Gtk.License.GPL_3_0,
            website="https://gitlab.gnome.org/World/Letterpress",
            issue_url="https://gitlab.gnome.org/World/Letterpress/-/issues",
            support_url="https://matrix.to/#/#gregorni-apps:matrix.org",
        )

        about.add_acknowledgement_section(
            _("Code and Design borrowed from"),
            [
                "Upscaler https://gitlab.gnome.org/World/Upscaler",
                "Frog https://github.com/TenderOwl/Frog",
            ],
        )

        about.add_legal_section(
            title="jp2a",
            copyright="Copyright © 2020 Christoph Raitzig",
            license_type=Gtk.License.GPL_2_0,
        )

        about.present()

    def __close_tips_dialog(self, *args):
        if self.tips_dialog is not None:
            self.tips_dialog.destroy()
            self.tips_dialog = None

    def __on_tips_action(self, *args):
        self.tips_dialog = TipsDialog(transient_for=self.win, application=self)
        self.tips_dialog.present()

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
    return LetterpressApplication().run(sys.argv)


@Gtk.Template(resource_path="/io/gitlab/gregorni/Letterpress/gtk/tips-dialog.ui")
class TipsDialog(Adw.Window):
    __gtype_name__ = "TipsDialog"
