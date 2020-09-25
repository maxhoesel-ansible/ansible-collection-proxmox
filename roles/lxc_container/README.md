lxc_container
=========

Creates and bootstraps a LXC container on a Proxmox VE node to a point where the containers root account can be accessed via SSH.

This role has been tested on the following container templates:
- Ubuntu 20.04
- Debian 10
- Fedora 32
- CentOS 7/8
- OpenSUSE 15.2
- Alpine 3.12

Other distributions should work as well, as long as they:
- use a package manager also used by one of the above distros
- use systemd for service management (or rc for Alpine)

Requirements
------------

A Proxmox VE host accessible via SSH and the PVE API.

The following python modules on the controller:
- proxmoxer
- requests
Install via pip: `pip3 install proxmoxer requests`

Role Variables
--------------

See `defaults/main.yml`

Dependencies
------------

None

Example Playbook
----------------

```
- hosts: pve_host
  roles:
  - lxc_container:
    lxccreate_hostname: a-hostname
    lxccreate_ostemplate: local:vztmpl/ubuntu-20.04-standard_20.04-1_amd64.tar.gz
    lxccreate_netif:
      net0: name=eth0,bridge=vmbr0,ip=192.168.1.10/24,gw=192.168.1.1,firewall=0
    lxccreate_password: a-root-password
```

License
-------

GPL 3 or later
