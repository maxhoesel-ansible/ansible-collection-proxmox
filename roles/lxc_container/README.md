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

A Proxmox VE host accessible via SSH and the PVE API (see `defaults/main.yml`) with `become` privileges.

The following python modules are required on the controller:
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

Generic example:

```
- hosts: all
  gather_facts: no
  roles:
  - lxc_container:
    # This role will connect to this PVE host for various tasks related to container setup
    # Make sure that the pve_host (here: pve1.example.com) is present in your inventory
    # and that ansible can connect via SSH (+ become) and via API
    pve_host: pve1.example.com
    pve_api_user: root@pam
    pve_api_password: some-password
    # Parameters for the container that you want to create
    lxccreate_hostname: a-hostname
    lxccreate_ostemplate: local:vztmpl/ubuntu-20.04-standard_20.04-1_amd64.tar.gz
```

Creating a batch of containers based on an inventory is also possible using a customized inventory. An example layout is show below:

Inventory:
```
all:
  children:
    containers:
      hosts:
        192.168.1.123:
          # Variables unique to every container
          lxccreate_hostname: ct-a
          ...
        192.168.1.124:
        ...
      # Common variables shared between containers
      lxccreate_ostemplate: local:vztmpl/ubuntu-20.04-standard_20.04-1_amd64.tar.gz
      lxccreate_args:
        cores: 4
      # PVE connection variables
      pve_api_user: root@pam
      pve_api_password: some-secret-password
      pve_host: pve1.example.com
      ...
  hosts:
    pve1.example.com:
      # Parameters for the PVE API and SSH host.
      ansible_user: root
```

```
  # This will create a set of containers, with each container being a member of the `containers` group
- hosts: containers
  serial: 1 # Needed to prevent race conditions
  gather_facts: no
  roles:
  - name: lxc_container
```


License
-------

GPL 3 or later
