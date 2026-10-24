import subprocess
from typing import List, Optional
from urllib.parse import urlparse

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Thunarx", "3.0")
from gi.repository import Thunarx, GObject, Gtk, Gdk


def _normalize_url(url: str) -> str:
    url = url.strip()
    if url and "://" not in url:
        url = "https://" + url
    return url


def _is_valid_url(url: str) -> bool:
    parsed = urlparse(_normalize_url(url))
    return parsed.scheme in ("http", "https", "ftp") and bool(parsed.netloc)


def _write_weblink(folder: str, name: str, url: str) -> None:
    # the core `winurl` binary sanitizes the name and picks a free filename
    result = subprocess.run(
        ["winurl", "--create", folder, url, name],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise OSError(result.stderr.strip() or "winurl failed")


def _show_error(parent: Optional[Gtk.Window], message: str) -> None:
    err = Gtk.MessageDialog(
        transient_for=parent, modal=True,
        message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
        text="Impossible to create the link",
    )
    err.format_secondary_text(message)
    err.run()
    err.destroy()


def _show_dialog(parent: Optional[Gtk.Window], folder: str) -> None:
    dialog = Gtk.Dialog(title="New web shortcut", transient_for=parent, modal=True)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    create_btn = dialog.add_button("Create", Gtk.ResponseType.OK)
    create_btn.get_style_context().add_class("suggested-action")
    create_btn.set_sensitive(False)
    dialog.set_default_response(Gtk.ResponseType.OK)

    url_entry = Gtk.Entry(placeholder_text="https://example.com", activates_default=True, hexpand=True)
    name_entry = Gtk.Entry(placeholder_text="optional", activates_default=True, hexpand=True)

    grid = Gtk.Grid(row_spacing=6, column_spacing=12, margin=12)
    grid.attach(Gtk.Label(label="Create a Windows .url shortcut in the selected folder", xalign=0), 0, 0, 2, 1)
    grid.attach(Gtk.Label(label="URL", xalign=1), 0, 1, 1, 1)
    grid.attach(url_entry, 1, 1, 1, 1)
    grid.attach(Gtk.Label(label="Name", xalign=1), 0, 2, 1, 1)
    grid.attach(name_entry, 1, 2, 1, 1)
    dialog.get_content_area().add(grid)

    def on_url_changed(entry):
        create_btn.set_sensitive(_is_valid_url(entry.get_text()))

    url_entry.connect("changed", on_url_changed)

    text = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).wait_for_text()
    if text and _is_valid_url(text) and " " not in text.strip():
        url_entry.set_text(text.strip())

    dialog.show_all()
    while dialog.run() == Gtk.ResponseType.OK:
        if not _is_valid_url(url_entry.get_text()):
            continue
        try:
            _write_weblink(folder, name_entry.get_text(), url_entry.get_text())
        except OSError as e:
            _show_error(dialog, str(e))
            continue
        break
    dialog.destroy()


class CreateWinWeblink(GObject.GObject, Thunarx.MenuProvider):
    def _activate(self, _item, window, file_info) -> None:
        path = file_info.get_location().get_path()
        if path is not None:
            _show_dialog(window, path)

    def get_file_menu_items(self, window, files) -> List[Thunarx.MenuItem]:
        if len(files) != 1 or not files[0].is_directory():
            return []
        item = Thunarx.MenuItem(
            name="CreateWinWeblink::create_weblink_folder",
            label="Create Windows Weblink here",
            tooltip="Create a Windows .url shortcut in the selected folder",
        )
        item.connect("activate", self._activate, window, files[0])
        return [item]

    def get_folder_menu_items(self, window, folder) -> List[Thunarx.MenuItem]:
        item = Thunarx.MenuItem(
            name="CreateWinWeblink::create_weblink_bg",
            label="Create Windows Weblink",
            tooltip="Create a Windows .url shortcut in the current folder",
        )
        item.connect("activate", self._activate, window, folder)
        return [item]
