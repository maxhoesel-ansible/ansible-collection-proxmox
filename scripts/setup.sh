#!/usr/bin/env bash
set -eu
set -e pipefail

python3 -m venv .venv
source .venv/bin/activate

pip3 install pre-commit tox gitlint ansible proxmoxer requests

pre-commit install --hook-type commit-msg

# Initialize tox venvs
tox -l > /dev/null
