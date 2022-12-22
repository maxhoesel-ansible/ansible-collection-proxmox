lxc_container_to_ostemplate
=========

Converts a LXC container into an ostemplate that can be used to generate new containers.

This role performs the following actions:
1. Creates a gz-compressed backup of a given container with vzdump
2. Moves the backup into the templates location of a given storage volume

Requirements
------------

### Proxmox Host

To execute this role, Ansible needs to access the Proxmox host on which the container image will be created.
To speficy the host, set `pve_host` to the hots' inventory name. If you don't want to add the host
to your inventory file, you can also add it at runtime with the `add_host` module - see [here for an example.](#with-a-dynamic-pve-host)

Role Variables
--------------

See `defaults/main.yml` for details on the individual variables

Dependencies
------------

None

Example Playbook
----------------

### Simple

```yaml
- hosts: all
  gather_facts: no
  roles:
  - role: lxc_container_to_ostemplate
    # Make sure that the PVE host is present in your inventory
    pve_host: pve1.example.com
    lxcostemplate_hostname: ubuntu-18-04
    lxcostemplate_image: custom-ubuntu-18-04
    lxcostemplate_storage: local
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
  - role: lxc_container_to_ostemplate
    pve_host: pve1.example.com
    lxcostemplate_hostname: ubuntu-18-04
    lxcostemplate_image: custom-ubuntu-18-04
    lxcostemplate_storage: local
```

### Batch Conversion

Converting a batch of containers based on an inventory is also possible using a customized inventory. An example layout is show below:

Inventory:
```yaml
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
      pve_host: pve1.example.com
  pve:
    pve1.example.com:
      ansible_user: ansible
      ...
```
Playbook:
```yaml
  # This will generate templates of containers, with each container being a member of the `containers` group
- hosts: containers
  gather_facts: no
  roles:
  - name: lxc_container_to_ostemplate
```

License
-------

GPL 3 or later
