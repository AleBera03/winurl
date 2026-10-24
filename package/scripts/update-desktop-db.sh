#!/bin/bash

# refresh the MIME handler cache so .url files open with winurl
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
