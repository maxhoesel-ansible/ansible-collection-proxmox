# maxhoesel.proxmox.pve

Configure an existing Proxmox Virtual Environment hosts system.

Note that this role does not manage PVE settings itself (such as VMS and storage), but rather
the underlying system. Right now, it manages the root users password and configures the PVE repository

## Requirements

- A PVE host accessible via SSH and a user with become privileges

## Role Variables

##### `pve_root_password`
- Password for the root user
- Must be a string of at least 8 characters
- Required: `true`
- Default: undefined

##### `pve_repo_type`
- Selects which PVE repository is enabled for pulling updates
- Choices: `enterprise`, `no-subscription`, `test`
- Please note that this role does not configure your subscription key, you will have to do so yourself
- Default: `no-subscription`
