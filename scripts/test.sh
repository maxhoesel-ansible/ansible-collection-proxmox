#!/usr/bin/env bash
set -eu
set -o pipefail

# Lint ansible roles and git commits
tox -e lint

# Sanity checks for our modules
## --docker isn't technically required as tox-ansible autodetects it,
## however, this prevents it from falling back to a venv and potentially modifying the local environment
tox -e sanity -- --docker --color -v --python 3.6

# Integration tests for modules - we don't have an unit tests as of now
## --docker isn't technically required as tox-ansible autodetects it,
## however, this prevents it from falling back to a venv and potentially modifying the local environment
#tox -e integration -- --docker --color -v --python 3.6 --docker-terminate success

# Molecule tests - this grabs all molecule scenarios and executes them.
#tox -e "$(tox -l | grep ansible | grep -v "lint" | tr '\n' ',')"
