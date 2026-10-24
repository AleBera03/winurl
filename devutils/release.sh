#!/bin/bash

help() {
    echo "Usage: devutils/release.sh LEVEL"
    echo "  LEVEL: major, minor, fix (semver bump of Cargo.toml version)"
}

set -euo pipefail

cd "$(dirname "$0")/.."

[ $# -eq 1 ] || { help >&2; exit 1; }

CURRENT="$(grep -m1 '^version' Cargo.toml | cut -d'"' -f2)"
IFS=. read -r MAJOR MINOR FIX <<< "$CURRENT"

case "${1,,}" in
    -h|--help) help; exit 0 ;;
    major) VERSION="$((MAJOR + 1)).0.0" ;;
    minor) VERSION="$MAJOR.$((MINOR + 1)).0" ;;
    fix) VERSION="$MAJOR.$MINOR.$((FIX + 1))" ;;
    *) echo "Unknown level '$1'" >&2; help >&2; exit 1 ;;
esac

if git rev-parse -q --verify "refs/tags/v$VERSION" >/dev/null; then
    echo "Tag 'v$VERSION' already exists" >&2
    exit 1
fi

read -rp "Release $CURRENT -> $VERSION (commit, tag and push)? [y/N] " answer
[[ "$answer" =~ ^[yY]$ ]] || { echo "Aborted"; exit 1; }

# the release workflow requires the tag to match the Cargo.toml version
sed -i "0,/^version = \".*\"/s//version = \"$VERSION\"/" Cargo.toml
cargo update --workspace --quiet

git commit -am "release: $VERSION"
git tag "v$VERSION"
git push
git push --tags

echo "Done: released v$VERSION"
