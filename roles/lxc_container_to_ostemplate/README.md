lxc_container_to_ostemplate
=========

Converts a LXC container into an ostemplate that can be used to generate new containers.

This role performs the following actions:
1. Created a gz-compressed backup of a given container with vzdump
2. Moves the backup into the templates location of a given storage volume

Requirements
------------

A Proxmox VE host accessible via SSH and the PVE API that is running the target container (see `defaults/main.yml`) with `become` privileges.

Role Variables
--------------

See `defaults/main.yml` for details on the individual variables

Dependencies
------------

None

Example Playbook
----------------

```
- hosts: all
  gather_facts: no
  roles:
  - role: lxc_container_to_ostemplate
    pve_host: mypvehost.example.com
    pve_ssh_user: root
    lxcostemplate_hostname: ubuntu-18-04
    lxcostemplate_image: custom-ubuntu-18-04
    lxcostemplate_storage: local
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
          lxcostemplate_hostname: ct-a
          lxcostemplate_image: custom-ct-a
          ...
        192.168.1.124:
        ...
      # Common variables shared between containers
      lxcostemplate_storage: local
      pve_host: mypvehost.example.com
      ...
```
Playbook:
```
  # This will generate templates of containers, with each container being a member of the `containers` group
- hosts: containers
  gather_facts: no
  roles:
  - name: lxc_container_to_ostemplate
```

License
-------

GPL 3 or later
