# Open windows link on linux

When you share data between Windows machine and a Linux one, `.url` files from windows may be there. Without any script, if you attempt to open it from file manager a INI format text file will be opened.

This simple script is able to read those files and open the contained url via [`xdg-open`](https://linux.die.net/man/1/xdg-open).

## Packages

Packages are built with [nfpm](https://nfpm.goreleaser.com/):

| Package | Content | Tested |
| --- | --- | --- |
| `winurl-core` | `winurl` binary + desktop entry that opens `.url` files | :white_check_mark: |
| `winurl-nautilus` | Nautilus extension (nautilus-python) | :white_check_mark: |
| `winurl-nemo` | Nemo extension (nemo-python) | :x: |
| `winurl-caja` | Caja extension (caja-python) | :x: |
| `winurl-thunar` | Thunar extension (thunarx-python) | :x: |
| `winurl-dolphin` | Dolphin service menu (kdialog) | :x: |
| `winurl-pcmanfm` | PCManFM action (zenity) | :x: |

File manager packages add a "Create Windows Weblink" context menu entry and depend on `winurl-core`, whose `winurl` binary writes the file:

```
winurl --create FOLDER URL [NAME]
```

## Development

Project uses [`justfile`](https://github.com/casey/just). By running `just -l|--list` on root project folder, you can view all building possibilities.

Requirements:
- `cargo`
- [`nfpm`](https://nfpm.goreleaser.com/install/)
- `.env` file (see `.env.example`) with maintainer info

`package/build.sh` compiles the rust project in release mode and runs nfpm for each package config (`package/nfpm.yaml` for the core, `file_manager/<name>/nfpm.yaml` for extensions). For example, run on root folder

```
just build                          # all packages, all formats
just build deb                      # all packages, only .deb
just build deb rpm core nautilus    # only some formats and packages
```

Packages are written to `package/build/`, e.g. `winurl-core_0.1.0_amd64.deb` and `winurl-nautilus_0.1.0_all.deb`.
