#!/usr/bin/env zsh


# Project root directory
# https://unix.stackexchange.com/a/115431
root=${0:A:h:h}

images="$root/images"

data="https://github.com/tnahs/PrintQR"

zint                                       \
 --output "$images/qr-code-light.png"      \
 --data $data                              \
 --barcode 58                              \
 --scale 5                                 \
 --fg 1F2328                               \
 --bg FFFFFF00

zint                                       \
 --output "$images/qr-code-dark.png"       \
 --data $data                              \
 --barcode 58                              \
 --scale 5                                 \
 --fg D1D7E0                               \
 --bg FFFFFF00
