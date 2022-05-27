#!/usr/bin/env bash
set -eu
set -o pipefail

# Sanity checks for our modules
tox -e sanity -- --docker --color -v --python 3.6

# Integration tests for modules
#tox -e integration -- --color -v --controller docker:default --target docker:centos7,seccomp=unconfined,privileged=yes
#tox -e integration -- --color -v --controller docker:default --target docker:default,python=3.6

# Molecule tests - this grabs all molecule scenarios and executes them.
# Note that to run this command, you need to have
# - run and tox command at least once (tox -l is fine)
# - have the collection built and installed locally.
#   Running the module tests will do that for you
tox -e "$(tox -l | grep ansible | grep -v "lint" | tr '\n' ',')"
