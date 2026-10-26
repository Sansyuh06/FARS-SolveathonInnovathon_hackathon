#!/usr/bin/env bash
echo "Booting FARS..."
cd "$(dirname "$0")"
python3 fars_studio/launch_FARS.py
