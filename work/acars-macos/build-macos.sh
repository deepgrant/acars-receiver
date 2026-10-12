#!/bin/bash
set -euo pipefail
acars_base="$(cd -- "$(dirname -- "$0")" && pwd)"
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Library/Developer/CommandLineTools}"
export PATH="/opt/homebrew/bin:$PATH"
export PKG_CONFIG_PATH="/opt/homebrew/opt/cjson/lib/pkgconfig:/opt/homebrew/opt/libusb/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
acars_sdk="$(/usr/bin/xcrun --show-sdk-path)"
acars_clang="$(/usr/bin/xcrun --find clang)"
acars_cmake=/opt/homebrew/bin/cmake

for acars_dependency in "$acars_cmake" /opt/homebrew/bin/pkg-config /opt/homebrew/opt/libusb /opt/homebrew/opt/cjson; do
    if [ ! -e "$acars_dependency" ]; then
        printf 'Missing build dependency: %s\n' "$acars_dependency" >&2
        exit 1
    fi
done

if [ ! -d "$acars_base/acarsdec" ]; then
    /usr/bin/git clone https://github.com/f00b4r0/acarsdec.git "$acars_base/acarsdec"
    /usr/bin/git -C "$acars_base/acarsdec" checkout --detach cbaa28c4173fc1529a01ab50708e29d12d09a644
    /usr/bin/git -C "$acars_base/acarsdec" apply "$acars_base/acarsdec-macos.patch"
fi
if [ ! -d "$acars_base/rtl-sdr" ]; then
    /usr/bin/git clone https://github.com/osmocom/rtl-sdr.git "$acars_base/rtl-sdr"
    /usr/bin/git -C "$acars_base/rtl-sdr" checkout --detach 797f8143266d983c56d8f35d2d442527529dd8a5
fi

"$acars_cmake" -S "$acars_base/rtl-sdr" -B "$acars_base/build-macos/rtl" \
    -DCMAKE_INSTALL_PREFIX="$acars_base/runtime" \
    -DCMAKE_C_COMPILER="$acars_clang" -DCMAKE_OSX_SYSROOT="$acars_sdk" \
    -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=15.0 \
    -DINSTALL_UDEV_RULES=OFF
"$acars_cmake" --build "$acars_base/build-macos/rtl" --parallel 4
"$acars_cmake" --install "$acars_base/build-macos/rtl"

"$acars_cmake" -S "$acars_base/acarsdec" -B "$acars_base/build-macos/acars" \
    -DCMAKE_PREFIX_PATH="$acars_base/runtime;/opt/homebrew" \
    -DCMAKE_C_COMPILER="$acars_clang" -DCMAKE_OSX_SYSROOT="$acars_sdk" \
    -DCMAKE_C_FLAGS="-I$acars_base/runtime/include" \
    -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=15.0 \
    -DCJSON=ON -DRTLSDR=ON -DSNDFILE=OFF -DLIBACARS=OFF -DMQTT=OFF \
    -DALSA=OFF -DAIRSPY=OFF -DSDRPLAY=OFF -DSOAPYSDR=OFF
"$acars_cmake" --build "$acars_base/build-macos/acars" --parallel 4

"$acars_clang" -isysroot "$acars_sdk" -mmacosx-version-min=15.0 \
    -I "$acars_base/runtime/include" "$acars_base/check-sdr.c" \
    -L "$acars_base/runtime/lib" -lrtlsdr \
    -Wl,-rpath,"$acars_base/runtime/lib" -o "$acars_base/check-sdr"
/usr/bin/python3 "$acars_base/package.py"
