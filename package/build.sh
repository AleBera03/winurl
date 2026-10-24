#!/bin/bash

help() {
    echo "Usage: package/build.sh [PACKAGER...] [PACKAGE...]"
    echo "  PACKAGER: deb, rpm, archlinux, apk (default: all)"
    echo "  PACKAGE: core, nautilus, dolphin, nemo, caja, thunar, pcmanfm (default: all)"
}

set -euo pipefail

cd "$(dirname "$0")/.."

[ -f .env ] && source .env

FILE_MANAGERS=(nautilus dolphin nemo caja thunar pcmanfm)
ALL_PACKAGERS=(deb rpm archlinux apk)
OUT_DIR="package/build"
NFPM="${NFPM:-nfpm}" # NFPM is a general path to nfpm binary

if ! command -v "$NFPM" >/dev/null 2>&1; then
    echo "nfpm not found: install it from https://nfpm.goreleaser.com/install/" >&2
    exit 1
fi

export VERSION="$(grep -m1 '^version' Cargo.toml | cut -d'"' -f2)"
export MAINTAINER="${FULLNAME:?set FULLNAME in .env} <${EMAIL:?set EMAIL in .env}>"
# nfpm expects GOARCH-style names and maps them to each packager's naming
case "$(uname -m)" in
    x86_64) export ARCH=amd64 ;;
    aarch64) export ARCH=arm64 ;;
    armv7l) export ARCH=arm7 ;;
    i?86) export ARCH=386 ;;
    *) export ARCH="$(uname -m)" ;;
esac

PACKAGERS=()
PACKAGES=()
for arg in "$@"; do
    case "$arg" in
        -h|--help) help; exit 0 ;;
        deb|rpm|archlinux|apk) PACKAGERS+=("$arg") ;;
        *) PACKAGES+=("$arg") ;;
    esac
done
[ ${#PACKAGERS[@]} -eq 0 ] && PACKAGERS=("${ALL_PACKAGERS[@]}")
[ ${#PACKAGES[@]} -eq 0 ] && PACKAGES=(core "${FILE_MANAGERS[@]}")

config_for() {
    if [ "$1" = core ]; then
        echo package/nfpm.yaml
    elif [ -f "file_manager/$1/nfpm.yaml" ]; then
        echo "file_manager/$1/nfpm.yaml"
    else
        echo "Unknown package '$1'" >&2
        return 1
    fi
}

mkdir -p "$OUT_DIR"

for pkg in "${PACKAGES[@]}"; do
    config="$(config_for "$pkg")"

    if [ "$pkg" = core ]; then
        echo "Compiling rust in release mode ..."
        cargo build --release
    fi

    for packager in "${PACKAGERS[@]}"; do
        echo "Packaging $pkg ($packager) ..."
        "$NFPM" package --config "$config" --packager "$packager" --target "$OUT_DIR/"
    done
done

echo "Done: packages in $OUT_DIR/"
