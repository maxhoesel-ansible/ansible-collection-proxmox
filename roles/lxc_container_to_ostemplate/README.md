lxc_container_to_ostemplate
=========

Converts a LXC container into an ostemplate that can be used to generate new containers.

This role performs the following actions:
1. Created a gz-compressed backup of a given container with vzdump
2. Moves the backup into the templates location of a given storage volume

Requirements
------------

A Proxmox VE host accessible via SSH and the PVE API.

Role Variables
--------------

See `defaults/main.yml` for details on the individual variables

Dependencies
------------

None

Example Playbook
----------------

- hosts: pve_node
  roles:
  - role: lxc_container_to_ostemplate
    pve_lxcostemplate_hostname: ubuntu-18-04
    pve_lxcostemplate_image: custom-ubuntu-18-04
    pve_lxcostemplate_storage: local


License
-------

GPL 3 or later