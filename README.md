# Open windows link on linux

When you share data between Windows machine and a Linux one, `.url` files from windows may be there. Without any script, if you attempt to open it from file manager a INI format text file will be opened.

This simple script is able to read those files and open the contained url via [`xdg-open`](https://linux.die.net/man/1/xdg-open).

## Development

Project uses [`justfile`](https://github.com/casey/just). By running `just -l|--list` on root project folder, you can view all building possibilities.

For example, to test debian build, run on root folder

```
just build-deb
```

Then a `.deb` file it appears within `ROOT_FOLDER/dev/debian/build`. If machine architecture is `amd64` and app version is `0.1.0`, then filename become `open-win-link_0.1.0_amd64.deb`.
