#!/bin/bash

set -euo pipefail
source .env

PKG_NAME="open-win-link"
VERSION=$(grep -m1 '^version' Cargo.toml | cut -d'"' -f2)
ARCH=$(dpkg --print-architecture)
DEB_BUILD_ROOT="dev/debian"
STAGE="${DEB_BUILD_ROOT}/build/${PKG_NAME}_${VERSION}_${ARCH}"

echo "Compiling rust in release mode ..."
cargo build --release

echo "Preparing packaging tree in $STAGE ..."
rm -rf build
mkdir -p "$STAGE"
cp -r ${DEB_BUILD_ROOT}/packaging/. "$STAGE/"

install -Dm755 "target/release/$PKG_NAME" "$STAGE/usr/bin/$PKG_NAME"

# sync arch and version within control file
sed -i "s/^Architecture:.*/Architecture: ${ARCH}/; s/^Version:.*/Version: ${VERSION}/; s/^Maintainer:.*/Maintainer: ${FULLNAME} <${EMAIL}>/" "${STAGE}/DEBIAN/control"

# required debian permissions
# directory 755
# file 644
# executable 755
find "$STAGE" -type d -exec chmod 755 {} +
find "$STAGE/usr/share" -type f -exec chmod 644 {} +

echo "Creating .deb ..."
dpkg-deb --build --root-owner-group "$STAGE"

echo "Done build/${PKG_NAME}_${VERSION}_${ARCH}.deb"
