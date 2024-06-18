# maxhoesel.proxmox

![Release](https://img.shields.io/github/v/release/maxhoesel-ansible/ansible-collection-proxmox?style=flat-square)
![Build Status](https://img.shields.io/circleci/build/github/maxhoesel-ansible/ansible-collection-proxmox/main?style=flat-square)
![License](https://img.shields.io/github/license/maxhoesel-ansible/ansible-collection-proxmox?style=flat-square)

A collection for managing Proxmox VE and Backup Server hosts. Contains roles for managing the PVE/PBS ecosystem, as well as modules to manage PBS configuration.
With this collection, you can:

- Perform basic setup of your PVE servers (configuring PVE repositories, root user access, CPU governor)
- Configure a PBS server (including smart monitoring, etc.)
- Install and configure the Proxmox Backup Client on supported systems
- Manage Proxmox Backup Server users, repositories and permissions

## Components

---
**📘 Documentation**

- For role documentation, see their `README.md`s or the online docs [here](https://ansible-collection-proxmox.readthedocs.io)
- For modules documentation, see the online docs [here](https://ansible-collection-proxmox.readthedocs.io)

---

### Roles

- [`lxc_container`](./roles/lxc_container/): Create and bootstrap LXC containers on Proxmox for Ansible access
- [`lxc_container_to_ostemplate`](./roles/lxc_container_to_ostemplate/): Generate ostemplate (LXC container) images from existing LXC containers
- [`pve`](./roles/pve/): Perform basic system-level setup tasks on PVE nodes
- [`pbs`](./roles/pbs/): Perform basic system-level setup tasks on Proxmox Backup Server hosts
- [`pbs_client`](./roles/pbs_client/): Install and configure the Proxmox Backup Client

### Modules

#### Proxmox VE

- [`proxmox_ha`](https://ansible-collection-proxmox.readthedocs.io/en/latest/collections/maxhoesel/proxmox/proxmox_ha_module.html): Manage High Availability settings for a VM/Container

#### Proxmox Backup Server

- [`pbs_acl`](https://ansible-collection-proxmox.readthedocs.io/en/latest/collections/maxhoesel/proxmox/pbs_acl_module.html)`
- [`pbs_datastore`](https://ansible-collection-proxmox.readthedocs.io/en/latest/collections/maxhoesel/proxmox/pbs_datastore_module.html)`
- [`pbs_directory`](https://ansible-collection-proxmox.readthedocs.io/en/latest/collections/maxhoesel/proxmox/pbs_directory_module.html)`
- [`pbs_token`](https://ansible-collection-proxmox.readthedocs.io/en/latest/collections/maxhoesel/proxmox/pbs_token_module.html)`
- [`pbs_user`](https://ansible-collection-proxmox.readthedocs.io/en/latest/collections/maxhoesel/proxmox/pbs_user_module.html)`

## Installation

### Dependencies

- A recent release of Ansible. This collection officially supports the 2 most recent Ansible releases.
  Older versions might still work, but are not supported
- Python 3.7 or newer on the target host
- For module usage, the `proxmoxer` and `requests` python modules are required on the controller host

Individual roles or modules may have additional dependencies, please check their respective documentation.

### Install

Via ansible-galaxy (recommended):

`ansible-galaxy collection install maxhoesel.proxmox`

Alternatively, you can download a collection archive from a [previous release](hhttps://github.com/maxhoesel-ansible/ansible-collection-proxmox/releases).

You can also clone this repository directly if you want a slightly more up-to-date (and potentially buggy) version.

`ansible-galaxy collection install git+https://github.com/maxhoesel-ansible/ansible-collection-proxmox`

## License & Author

Created & Maintained by Max Hösel (@maxhoesel) and Contributors

Licensed under the GPL 3.0 or later
