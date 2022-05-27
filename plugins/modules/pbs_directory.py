#!/usr/bin/python

# Copyright: (c) 2022, Max Hösel <ansible@maxhoesel.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# pylint: disable=duplicate-code
DOCUMENTATION = r"""
---
module: pbs_directory
author: Max Hösel (@maxhoesel)
short_description: Manage the mountpoint for a physical disk on a PBS node
version_added: '4.0.0'
description: >
    Initialize a disk, create a FS and mount it on a path on a PBS node, or delete such a path mount.
    This module can only create mounts on unused disks and will not perform potentially destructive tasks.
notes:
  - This module will not add the directory as a datastore, use the M(maxhoesel.proxmox.pbs_datastore) module to do so
  - Check mode is supported.
options:
  disk:
    description: >
        Disk identifier, such as sda or nvme0n1.
        Ignored if C(state) is absent
    type: str
    required: yes
  filesystem:
    description: Type of filesystem to use.
    type: str
    choices:
      - ext4
      - xfs
  init_gpt:
    description: Whether to first initialize the disk with GPT before adding it as a directory.
    default: yes
    type: bool
  mount_name:
    description: >
        Name of the path under which the disk should be mounted.
        For example, if mount_name=disk1, then the mount will be under /mnt/datastore/disk1.
        Note that once a disk is mounted that mount path cannot be moved.
        If C(state) is absent, then this mount will be deleted
    type: str
    required: yes
    aliases:
      - name
  node:
    description: >
        Node on which the disk resides. Default: hostname section of I(api_host).
    type: str
  state:
    description: >
        The state that the disk should be in.
        C(present) will ensure that the disk has a filesystem mounted at the location defined in (mount_name),
        while absent will remove that directory without touching the disk itself.
        Note that once a disk is mounted that mount path cannot be moved.
    type: str
    choices:
      - present
      - absent
    default: present

extends_documentation_fragment:
  - maxhoesel.proxmox.api_connection
"""

EXAMPLES = r"""
- name: Create a mount
  maxhoesel.proxmox.pbs_directory:
    api_user: root@pam
    api_password: secret
    api_host: helldorado
    disk: sda
    mount_name: disk1
    node: hellodorado
    filesystem: ext4
"""

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.api_connection import api_connection_argspec, init

try:
    import proxmoxer
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


def _make_directory_params(module: AnsibleModule) -> dict:
    directory_params = {
        "disk": module.params["disk"],
        "filesystem": module.params["filesystem"],
        "name": module.params["mount_name"],
        "add-datastore": False
    }
    directory_params = {key: directory_params[key]
                        for key in directory_params if directory_params[key] is not None}
    return directory_params


def add_directory(module: AnsibleModule, proxmox, result: dict) -> dict:
    directory = _make_directory_params(module)

    try:
        getattr(proxmox.nodes, module.params["node"]).disks.directory.post(**directory)
    except proxmoxer.ResourceException as e:
        result["msg"] = f"Could not create directory mount. Exception: {e}"
        module.fail_json(**result)
    result["changed"] = True
    return result


def delete_directory(module: AnsibleModule, proxmox, result: dict) -> dict:
    try:
        getattr(getattr(proxmox.nodes, module.params["node"]
                        ).disks.directory, module.params["mount_name"]).delete()
    except proxmoxer.ResourceException as e:
        result["msg"] = f"Could not delete directory mount. Exception: {e}"
        module.fail_json(**result)
    result["changed"] = True
    return result


def init_gpt(module: AnsibleModule, proxmox, result: dict) -> dict:
    try:
        getattr(proxmox.nodes, module.params["node"]).disks.initgpt.post(disk=module.params["disk"])
    except proxmoxer.ResourceException as e:
        result["msg"] = f"Could not initialize disk with GPT table. Exception: {e}"
        module.fail_json(**result)
    result["changed"] = True
    return result


def main():

    module_args = dict(
        disk=dict(type="str", required=True),
        filesystem=dict(type="str", choices=["ext4", "xfs"]),
        init_gpt=dict(type="bool", default=True),
        mount_name=dict(type="str", required=True, aliases=["name"]),
        node=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present")
    )
    result = dict(changed=False, msg="")
    module = AnsibleModule(
        argument_spec={**module_args, **api_connection_argspec},
        supports_check_mode=True
    )

    if not module.params["node"]:
        module.params["node"] = module.params["api_host"].split(".", maxsplit=1)[0]

    proxmox = init(module, result, "PBS")

    try:
        mounts = getattr(proxmox.nodes, module.params["node"]).disks.directory.get()
    except proxmoxer.ResourceException as e:
        result["msg"] = f"Could not get list of disk mounts on node {module.params['node']}. Exception: {e}"
        module.fail_json(**result)

    mounts_by_name = {mount["name"]: mount for mount in mounts}
    mount_exists = module.params["mount_name"] in mounts_by_name

    action = None
    if mount_exists and module.params["state"] == "absent":
        action = delete_directory
    elif not mount_exists and module.params["state"] == "present":
        try:
            disks = getattr(proxmox.nodes, module.params["node"]).disks.list.get(skipsmart=True)
        except proxmoxer.ResourceException as e:
            result["msg"] = f"Could not get list of disks on node {module.params['node']}. Exception: {e}"
            module.fail_json(**result)

        disks_by_name = {disk["name"]: disk for disk in disks}
        disk_exists = module.params["disk"] in disks_by_name

        if not disk_exists:
            result["msg"] = f"Disk with name {module.params['disk']} does not exist"
            module.fail_json(**result)

        disk = disks_by_name[module.params["disk"]]
        if disk["used"] != "unused":
            result["msg"] = f"Cannot operate on disk that is in state {disk['used']}. Disk must either be unused"
            module.fail_json(**result)

        if not disk["gpt"]:
            if module.params["init_gpt"]:
                if module.check_mode:
                    result["changed"] = True
                else:
                    result = init_gpt(module, proxmox, result)
            else:
                result["msg"] = "Disk does not have a GPT partition table and init_gpt is not set, cannot continue"
                module.fail_json(**result)
        action = add_directory

    if action is not None:
        if module.check_mode:
            result["changed"] = True
        else:
            result = action(module, proxmox, result)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
