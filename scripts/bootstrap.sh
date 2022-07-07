#!/bin/bash

set -euo pipefail

if [[ ! -d /Library/Developer/CommandLineTools ]]; then
    echo "Installing Xcode command line tools"
    TMP_FILE=/private/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress
    touch "$TMP_FILE"
    PACKAGE_NAME=$(sudo softwareupdate -l | grep -o 'Command Line Tools for Xcode-.*' | tail -n 1)
    sudo softwareupdate --install "$PACKAGE_NAME"
    rm -fv "$TMP_FILE"
fi

