import subprocess
from typing import List, Optional
from urllib.parse import urlparse

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Nautilus, GObject, Gio, Gtk, Gdk, Adw

class CreateWinWeblink(GObject.GObject, Nautilus.MenuProvider):
    def _normalize_url(self, url: str) -> str:
        url = url.strip()
        if url and "://" not in url:
            url = "https://" + url
        return url

    def _is_valid_url(self, url: str) -> bool:
        parsed = urlparse(self._normalize_url(url))
        return parsed.scheme in ("http", "https", "ftp") and bool(parsed.netloc)

    def _write_weblink(self, folder: str, name: str, url: str) -> None:
        # the core `winurl` binary sanitizes the name and picks a free filename
        result = subprocess.run(
            ["winurl", "--create", folder, url, name],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise OSError(result.stderr.strip() or "winurl failed")

    def _get_parent_window(self) -> Optional[Gtk.Window]:
        app = Gio.Application.get_default()
        if isinstance(app, Gtk.Application):
            return app.get_active_window()
        return None

    def _prefill_from_clipboard(self, url_row: Adw.EntryRow) -> None:
        display = Gdk.Display.get_default()
        if display is None:
            return

        def on_text(clipboard, result):
            try:
                text = clipboard.read_text_finish(result)
            except Exception:
                return
            if text and not url_row.get_text() and self._is_valid_url(text) and " " not in text.strip():
                url_row.set_text(text.strip())

        display.get_clipboard().read_text_async(None, on_text)

    def _show_dialog(self, folder: str) -> None:
        dialog = Adw.AlertDialog(
            heading="New web shortcut",
            body="Create a Windows .url shortcut in the selected folder",
            close_response="cancel",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("create", "Create")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("create")
        dialog.set_response_enabled("create", False)

        url_row = Adw.EntryRow(title="URL")
        name_row = Adw.EntryRow(title="Name (optional)")

        listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        listbox.add_css_class("boxed-list")
        listbox.append(url_row)
        listbox.append(name_row)
        dialog.set_extra_child(listbox)

        def on_url_changed(row):
            valid = self._is_valid_url(row.get_text())
            dialog.set_response_enabled("create", valid)
            if valid or not row.get_text():
                row.remove_css_class("error")
            else:
                row.add_css_class("error")

        def on_entry_activate(_row):
            if dialog.get_response_enabled("create"):
                dialog.emit("response", "create")
                dialog.force_close()

        def on_response(_dialog, response):
            if response != "create":
                return
            try:
                self._write_weblink(folder, name_row.get_text(), url_row.get_text())
            except OSError as e:
                err = Adw.AlertDialog(heading="Impossible to create the link", body=str(e))
                err.add_response("ok", "OK")
                err.present(self._get_parent_window())

        url_row.connect("changed", on_url_changed)
        url_row.connect("entry-activated", on_entry_activate)
        name_row.connect("entry-activated", on_entry_activate)
        dialog.connect("response", on_response)

        self._prefill_from_clipboard(url_row)
        dialog.present(self._get_parent_window())
        url_row.grab_focus()

    def menu_activate_cb(self, menu, folder: Nautilus.FileInfo):
        path = folder.get_location().get_path()
        if path is None:
            return
        self._show_dialog(path)

    def get_file_items(self, files: List[Nautilus.FileInfo]) -> List[Nautilus.MenuItem]:
        if len(files) != 1 or not files[0].is_directory():
            return []

        item = Nautilus.MenuItem(
            name="CreateWinWeblink::create_weblink_folder",
            label="Create Windows Weblink here",
            tip="Create a Windows .url shortcut in the selected folder"
        )
        item.connect("activate", self.menu_activate_cb, files[0])
        return [item]

    def get_background_items(self, current_folder: Nautilus.FileInfo) -> List[Nautilus.MenuItem]:
        item = Nautilus.MenuItem(
            name="CreateWinWeblink::create_weblink_bg",
            label="Create Windows Weblink",
            tip="Create a Windows .url shortcut in the current folder"
        )
        item.connect("activate", self.menu_activate_cb, current_folder)
        return [item]
