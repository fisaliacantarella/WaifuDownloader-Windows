# window.py
#
# Copyright 2023 SilverOS
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

from gi.repository import Gtk, Adw, Gdk, GdkPixbuf, GLib
from .waifu import WaifuDownloaderAPI
import ctypes
from ctypes import wintypes
import os
import threading
from pathlib import Path
from gi.repository import Gio
from .preferences import UserPreferences


class OPENFILENAMEW(ctypes.Structure):
    _fields_ = [
        ("lStructSize", wintypes.DWORD),
        ("hwndOwner", ctypes.c_void_p),
        ("hInstance", ctypes.c_void_p),
        ("lpstrFilter", ctypes.c_wchar_p),
        ("lpstrCustomFilter", ctypes.c_wchar_p),
        ("nMaxCustFilter", wintypes.DWORD),
        ("nFilterIndex", wintypes.DWORD),
        ("lpstrFile", ctypes.c_wchar_p),
        ("nMaxFile", wintypes.DWORD),
        ("lpstrFileTitle", ctypes.c_wchar_p),
        ("nMaxFileTitle", wintypes.DWORD),
        ("lpstrInitialDir", ctypes.c_wchar_p),
        ("lpstrTitle", ctypes.c_wchar_p),
        ("Flags", wintypes.DWORD),
        ("nFileOffset", wintypes.WORD),
        ("nFileExtension", wintypes.WORD),
        ("lpstrDefExt", ctypes.c_wchar_p),
        ("lCustData", ctypes.c_ssize_t),
        ("lpfnHook", ctypes.c_void_p),
        ("lpTemplateName", ctypes.c_wchar_p),
        ("pvReserved", ctypes.c_void_p),
        ("dwReserved", wintypes.DWORD),
        ("FlagsEx", wintypes.DWORD),
    ]


def windows_save_dialog(title, filename, extension, initial_directory):
    """Open the Windows Explorer-style Save As dialog."""
    file_buffer = ctypes.create_unicode_buffer(filename, 32768)
    file_title_buffer = ctypes.create_unicode_buffer(260)
    filter_text = f"{extension.upper()} files (*.{extension})\0*.{extension}\0All files (*.*)\0*.*\0\0"
    filter_buffer = ctypes.create_unicode_buffer(filter_text)
    dialog = OPENFILENAMEW()
    dialog.lStructSize = ctypes.sizeof(dialog)
    dialog.lpstrFilter = ctypes.cast(filter_buffer, ctypes.c_wchar_p)
    dialog.nFilterIndex = 1
    dialog.lpstrFile = ctypes.cast(file_buffer, ctypes.c_wchar_p)
    dialog.nMaxFile = len(file_buffer)
    dialog.lpstrFileTitle = ctypes.cast(file_title_buffer, ctypes.c_wchar_p)
    dialog.nMaxFileTitle = len(file_title_buffer)
    dialog.lpstrInitialDir = str(initial_directory)
    dialog.lpstrTitle = title
    dialog.lpstrDefExt = extension
    dialog.Flags = 0x00000002 | 0x00000800 | 0x00000008 | 0x00080000 | 0x00800000

    common_dialogs = ctypes.WinDLL("comdlg32", use_last_error=True)
    common_dialogs.GetSaveFileNameW.argtypes = [ctypes.POINTER(OPENFILENAMEW)]
    common_dialogs.GetSaveFileNameW.restype = wintypes.BOOL
    if common_dialogs.GetSaveFileNameW(ctypes.byref(dialog)):
        return file_buffer.value
    error_code = common_dialogs.CommDlgExtendedError()
    if error_code:
        raise OSError(error_code, "Could not open the Windows Save As dialog")
    return None

@Gtk.Template(resource_path='/moe/nyarchlinux/waifudownloader/../data/ui/window.ui')
class WaifudownloaderWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'WaifudownloaderWindow'

    refresh_button = Gtk.Template.Child("refresh_button")
    spinner = Gtk.Template.Child("spinner")
    image = Gtk.Template.Child("image")
    save_button = Gtk.Template.Child("savebutton")
    search_button = Gtk.Template.Child("search_button")
    search_bar = Gtk.Template.Child("search_bar")
    search_entry = Gtk.Template.Child("search_entry")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = UserPreferences()
        self.set_icon_name("moe.nyarchlinux.waifudownloader")
        self.current_provider = self.settings.get_preference("provider") or "Auto"
        self.update_search_placeholder()
        self.refresh_button.connect("clicked", self.async_reloadimage)
        self.save_button.connect("clicked", self.file_chooser_dialog)
        self.search_button.connect("toggled", self.toggle_search)
        self.search_entry.connect("activate", self.async_reloadimage)
        self.async_reloadimage()

    def reloadimage(self, search_term="", provider="Waifu.im"):
        """Reload current image
        Args:
            idk (none): not useful but need to put it.
        """
        nsfwsetting = self.settings.get_preference("nsfw")
        use_doh = bool(self.settings.get_preference("doh"))
        ct = WaifuDownloaderAPI(use_doh=use_doh)
        try:
            info, content = ct.get_random_image(bool(nsfwsetting), search_term, provider)
        except Exception as error:
            GLib.idle_add(self.show_load_error, str(error))
            return
        GLib.idle_add(self.display_image, info, content)

    def display_image(self, info, content):
        self.info = info
        self.imagecontent = content
        loader = GdkPixbuf.PixbufLoader()
        loader.write_bytes(GLib.Bytes.new(content))
        loader.close()
        texture = Gdk.Texture.new_for_pixbuf(loader.get_pixbuf())
        self.image.set_paintable(texture)
        self.spinner.stop()
        self.spinner.set_visible(False)
        self.image.set_visible(True)
        self.refresh_button.set_sensitive(True)
        self.save_button.set_sensitive(True)
        return False

    def show_load_error(self, message):
        self.spinner.stop()
        self.spinner.set_visible(False)
        self.refresh_button.set_sensitive(True)
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text=f"Failed to load image:\n{message}",
        )
        dialog.connect("response", lambda current_dialog, _response: current_dialog.destroy())
        dialog.present()
        return False

    def async_reloadimage(self, _widget=None):
        """Call the function to load the image on another thread
        """
        self.spinner.set_visible(True)
        self.spinner.start()
        self.refresh_button.set_sensitive(False)
        self.save_button.set_sensitive(False)
        search_term = self.search_entry.get_text().strip()
        provider = self.settings.get_preference("provider") or "Auto"
        t = threading.Thread(target=self.reloadimage, args=[search_term, provider])
        t.start()

    def update_provider_selection(self, provider):
        self.current_provider = provider
        self.update_search_placeholder()
        self.async_reloadimage()

    def update_search_placeholder(self):
        provider = self.current_provider
        if provider == "Waifu.im":
            self.search_entry.set_placeholder_text("Search waifu name or tag")
        elif provider == "Auto":
            self.search_entry.set_placeholder_text("Search name or tags across providers")
        else:
            self.search_entry.set_placeholder_text("Search booru tags (e.g. genshin_impact)")

    def toggle_search(self, button):
        enabled = button.get_active()
        self.search_bar.set_search_mode(enabled)
        if enabled:
            self.search_entry.grab_focus()
        elif self.search_entry.get_text():
            self.search_entry.set_text("")
            self.async_reloadimage()

    def file_chooser_dialog(self, ae=None):
        """Displays the dialog to save the image
        """
        file_extension = self.info["items"][0]["extension"].lstrip(".")
        image_id = self.info["items"][0]["id"]
        filename = f"waifu.im_{image_id}.{file_extension}"
        downloads = Path.home() / "Downloads"
        initial_folder = downloads if downloads.is_dir() else Path.home()

        if os.name == "nt":
            path = windows_save_dialog("Save image", filename, file_extension, initial_folder)
            if path:
                self.write_image(path)
            return

        self.dialog = Gtk.FileChooserDialog(title="Save image", parent=self,
                                            action=Gtk.FileChooserAction.SAVE)
        self.dialog.set_current_folder(Gio.File.new_for_path(str(initial_folder)))

        # Add correct extension to file name
        image_filter = Gtk.FileFilter()
        image_filter.set_name(f"{file_extension.upper()} files")
        image_filter.add_pattern(f"*.{file_extension}")
        self.dialog.add_filter(image_filter)

        # Suggest a sensible default filename
        # using this format ensures the image source can easily be found from its name
        self.dialog.set_current_name(filename)

        # Buttons
        self.dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        self.dialog.add_button('Save', Gtk.ResponseType.OK)
        self.dialog.connect('response', self.responsehandler)
        self.dialog.show()

    def responsehandler(self, dialog, response_id):
        """Save image and destroy file chooser"""
        if response_id == Gtk.ResponseType.OK:
            file = dialog.get_file()
            filename = file.get_path()
            if filename:
                self.write_image(filename)
        dialog.destroy()

    def write_image(self, filename):
        try:
            Path(filename).write_bytes(self.imagecontent)
        except OSError as error:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CLOSE,
                text=f"Failed to save image:\n{error}",
            )
            dialog.connect("response", lambda current_dialog, _response: current_dialog.destroy())
            dialog.present()
