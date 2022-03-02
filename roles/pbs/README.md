# maxhoesel.proxmox.pbs

This role performs basic setup steps on a Proxmox Backup Server host. It does not manage
PBS configuration (storages, pools, etc.) - instead, it configures
the underlying system and platform (such as the root user and proxmox repository).

## Requirements

- A PBS host running and accessible via SSH

## Role Variables

##### `pbs_root_password`
- Password for the root user
- Must be a string of at least 8 characters
- Required: `true`
- Default: undefined

##### `pbs_repo_type`
- Selects which PBS repository is enabled for pulling updates
- Choices: `enterprise`, `no-subscription`, `test`
- Please note that this role does not configure your subscription key, you will have to do so yourself
- Default: `no-subscription`

##### `pbs_configure_smart`


##### `pbs_smart_temperature_warn`
- Hard disk temperature at which the S.M.A.R.T

## Example Playbook
- hosts: pbs
  become: yes
  tasks:
    - name: Setup PBS host
      include_role:
        name: maxhoesel.proxmox.pbs
