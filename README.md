# Ansible Collection - ariosthephoenix.proxmox

A collection for managing Proxmox VE hosts and their guests.

Currently contains the following components:

#### Roles

- lxc_container: Creates and bootstraps LXC containers for Ansible access
- lxc_container_to_ostemplate: Generates a ostemplate image from an existing container

#### Modules

Nothing so far

# Requirements & Installation

Several roles in this collection require the `proxmoxer` and `requests` Python module.

- Installation with `pip` (venv recommended): `pip3 install proxomxer requests`

To install this role: `ansible-galaxy collection install ariosthephoenix.proxmox`

# License

GNU GPL3 or later

# Author

Arios <ansible@arios.me>
