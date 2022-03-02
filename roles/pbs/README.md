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

##### `pbs_configure_smartd`
- Whether to enable configuration of smartd with this role.
- Default: `false` (to preserve compatibility)

##### `pbs_smartd_mail`
- Where to send mail alerts
- Can be a user name or an email address
- Default: `root`

##### `pbs_smartd_temperature_warn`
- Hard disk temperature at which smartd should throw an alarm.
- Default: `40`

##### `pbs_smartd_test_schedule`
- Schedule regex for drive self-tests, as passed to the `-s` parameter of smartd.
- See [the man page](https://linux.die.net/man/5/smartd.conf) for more details
- Default: `(S/../.././02|L/../../6/03)` (Short self-test every day at 2 AM, Long self-test every Saturday at 3 AM)


## Example Playbook

```yaml
- hosts: pbs
  become: yes
  tasks:
    - name: Setup PBS host
      include_role:
        name: maxhoesel.proxmox.pbs
      vars:
        pbs_root_password: "mysecretpassword"
        pbs_configure_smartd: yes
        pbs_smartd_mail: monitoring@example.org
```
