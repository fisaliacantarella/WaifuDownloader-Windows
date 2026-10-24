"""Windows launcher that runs the original GTK4/libadwaita application."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APP_ROOT = Path(getattr(sys, "_MEIPASS", ROOT))
RESOURCE_XML = ROOT / "src" / "waifudownloader.gresource.xml"
RESOURCE_FILE = APP_ROOT / "waifudownloader-windows.gresource" if getattr(sys, "frozen", False) else Path(tempfile.gettempdir()) / "waifudownloader-windows.gresource"


def register_ui_resources():
    if RESOURCE_FILE.is_file():
        return
    compiler = "glib-compile-resources.exe" if os.name == "nt" else "glib-compile-resources"
    subprocess.run(
        [compiler, str(RESOURCE_XML), f"--sourcedir={ROOT / 'src'}", f"--target={RESOURCE_FILE}"],
        cwd=ROOT,
        check=True,
    )


def main():
    if getattr(sys, "frozen", False):
        typelib_dir = APP_ROOT / "gi_typelibs"
        os.environ["GI_TYPELIB_PATH"] = str(typelib_dir)

    try:
        import gi
    except ModuleNotFoundError as error:
        if error.name == "gi":
            print(
                "GTK/PyGObject is not available in the standard Windows Python installation.\n"
                "Install the dependencies with .\\setup_windows.ps1, then launch the app with "
                ".\\run_windows.ps1 (MSYS2 UCRT64).",
                file=sys.stderr,
            )
            return 1
        raise

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    gi.require_version("Gdk", "4.0")
    from gi.repository import Adw, Gdk, Gio, Gtk

    register_ui_resources()
    resource = Gio.Resource.load(str(RESOURCE_FILE))
    resource._register()

    from src.main import WaifudownloaderApplication

    class WindowsWaifudownloaderApplication(WaifudownloaderApplication):
        def do_startup(self):
            Adw.Application.do_startup(self)
            icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
            icon_theme.add_search_path(str(APP_ROOT / "data" / "icons" / "hicolor"))
            Gtk.Window.set_default_icon_name("moe.nyarchlinux.waifudownloader")

        def do_activate(self):
            super().do_activate()
            self.window.set_title("Waifu Downloader for Windows")
            self.window.set_icon_name("moe.nyarchlinux.waifudownloader")

    return WindowsWaifudownloaderApplication().run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
