#!/usr/bin/env zsh


ROOT=${0:A:h:h}
IMAGES="$ROOT/images"
DATA="https://github.com/tnahs/PrintQR"

zint                                       \
 --output "$IMAGES/qr-code-light.png"      \
 --data $DATA                              \
 --barcode 58                              \
 --scale 5                                 \
 --fg 1F2328                               \
 --bg FFFFFF00

zint                                       \
 --output "$IMAGES/qr-code-dark.png"       \
 --data $DATA                              \
 --barcode 58                              \
 --scale 5                                 \
 --fg D1D7E0                               \
 --bg FFFFFF00
