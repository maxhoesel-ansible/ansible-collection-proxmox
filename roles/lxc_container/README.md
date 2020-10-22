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

### Proxmox Host

To execute this role, Ansible needs to access the Proxmox host on which the container will be created.
To speficy the host, set `pve_host` to the hots' inventory name. If you don't want to add the host
to your inventory file, you can also add it at runtime with the `add_host` module - see [here for an example.](#with-a-dynamic-pve-host)

### Controller

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

Example Playbooks
----------------

### Basic example

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

### With a dynamic pve host

If you don't want to clutter your inventory with the PVE host, you can just add it dynamically like so:

```
- hosts: all
  gather_facts: no
  pre_tasks:
  - name: Add PVE host to runtime inventory
    add_host:
      hostname: pve1.example.com
      ansible_python_interpreter: /usr/bin/python3
      ansible_user: ansible
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

### Batch creation

Creating a batch of containers based on an inventory is also possible using a customized inventory. An example is show here:

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
      # PVE connection variables shared between containers
      pve_api_user: root@pam
      pve_api_password: some-secret-password
      pve_host: pve1.example.com
      ...
  hosts:
    pve1.example.com:
      # Parameters for the PVE API and SSH host.
      ansible_user: root
      ansible_python_interpreter: /usr/bin/python3
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
