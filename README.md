# Ansible Collection - maxhoesel.proxmox

A collection for managing Proxmox VE hosts and their guests.

NOTE: The collection hosted at Galaxy is currently outdated due to [this issue.](https://github.com/ansible/galaxy/issues/2519) As a workaround, you can download the tar.gz file from a release or link to this repository in your requirements file

Currently contains the following components:

#### Roles

- lxc_container: Creates and bootstraps LXC containers for Ansible access
- lxc_container_to_ostemplate: Generates a ostemplate image from an existing container

#### Modules

- ha: Manage a hosts HA settings

# Requirements & Installation

Several roles in this collection require the `proxmoxer` and `requests` Python module.

- Installation with `pip` (venv recommended): `pip3 install proxomxer requests`

To install this role: `ansible-galaxy collection install maxhoesel.proxmox`

# License

GNU GPL3 or later

# Author

Max Hösel <ansible@maxhoesel.de>
