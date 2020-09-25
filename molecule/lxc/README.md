# General

As many of the roles in this collection require a dedicated PVE node for their action, our testing environment is a little more complicated than normal:

- A full PVE node is created inside a standard VM
- Container and Virtual machines are created on this node
- Both the node and guests are accessible from the test host

To achieve this setup, several extra dependencies are needed, as well as a more elaborate network setup

# Testing procedure & directory layout

The test suite currently consists out of the following components:

- dependency
    1 Create the Proxmox VE Vagrant box if needed
- create
    1. Create the Proxmox PVE Node
- prepare
    1. Perform setup of the node (root password, networking)
- converge
    1. Create and bootstrap containers using the lxc_container role
    2. Create templates of each container using lxc_container_to_ostemplate
- verify
    1. Test connection and Ansible execution on the containers
    2. Create custom containers based on the templates generated in the converge phase
    3. Test connection and Ansible execution on the new containers

Explanation of the extra directories in this scenario:

- `tasks`: Contains sets of tasks used during the `converge` and `verify` phases of the test suite.
- `templates`: Configuration files used to setup and prepare the testing enviroment
- `vars`: Contains information about the containers that are created during testing.

# Dependencies

In addition to molecule, the following applications need to be installed on the test host:

- Vagrant
- Virtualbox

The following python packages are required:

- molecule-vagrant
- proxmoxer
- requests

# Network setup

As this project incorporates a Proxmox VE node and the creation of containers on that server, a more sophisticated network setup than usual is required for testing:

```
                                                            Vagrant -> PVE connection
                                                          and PVE node internet access                     PVE Node
+---------+          +--------------+                         +----------------+                    +---------------------+
| Network | -------  | -----+------ | --------NET1----------- | VirtualBox NAT | ------------------ |-------eth0          |
+---------+          |      |       |                         +----------------+                    |       DHCP          |                 Guest
                     |   Test Host  |                                                               |                     |        +--------------------+
                     |      |       | --------NET2 ------------------------------------------- eth1 |-------vmbr0---------| ------ |--------eth0        |
                     +--------------+ 192.168.111.100/24    Provisioning network for                | 192.168.111.100/24  |        | 192.168.111.200/24 |
                            |                                    node + guests                      |                     |        |                    |
                            |                                     (host-only)                       |                     |        |                    |
                            |                                                                       |                     |        |                    |
                            |                                 +----------------+                    |                     |        |                    |
                            +-----------------NET3----------- | VirtualBox NAT | ------------- eth2 |-------vmbr1---------| ------ |--------eth1        |
                                                              +----------------+                    |      (DHCP)         |        |        DHCP        |
                                                              Internet Access for                   +---------------------+        +--------------------+
                                                                   Guests
```
Explanation of the individual networks:
- NET1: NAT interface - default network created by Vagrant for the pve node. Assigned to eth0 on the node
- NET2: Host-Only Network - used to access the nodes PVE API, as well as the created guests. Assigned to eth1 on the node and eth0 on guests
- NET3: NAT interface - Only used for internet access on the guests. eth2 on the node, eth1 on guests

#### Rationale
The default Vagrant network *must* be assigned to eth0 on all created boxes such as the PVE node. However, PVE needs to assign its IP address to a bridge (like vmbr0)in order for the guests connected to that bridge to have network access. This means that the default network can't be used to give the guests network access and a second network (NET3) is required. This network is assigned to a bridge on the PVE node, which in turn connects to the individual guests.

However, VirtualBox NATs do not allow the host access a guest service, such as the SSH server on a container. Vagrant can setup port forwards on boxes defined through it (such as the PVE host), but this doesn't work too well for hosts outside of Vagrants control, such as our PVE guests. Hence, we use a third, host-only network (NET2), which creates a completely regular network between the host and any connected guests without external internet access. A second bridge is used on the PVE node for this purpose

This setup allows us to test multiple nodes and guests, while preventing compatibility issues that might arise with a bridged network configuration


## Adding a new container

We provision multiple containers to test the bootstrap process on various distributions. If you need to add a new distro/container, follow these steps:

1. Add the container the inventory in `molecule.yml`. Use the next free IP address in the host-only network (counting from 200 for containers)
2. Add the custom container based on the template in `molecule.yml`. Use the next free IP address in the host-only network (counting form 2020)
2. Set the containers hostvars in `vars/${CONTAINER_IP}.yml`:
    - Make sure that both network interfaces are configured properly, using the IP address from step 1 (see the other containers for reference)
