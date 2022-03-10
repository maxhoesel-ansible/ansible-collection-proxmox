#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Max Hösel <ansible@maxhoesel.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r"""
---
module: pbs_acl
author: Max Hösel (@maxhoesel)
short_description: Manage ACLs on a Proxmox Backup Server
version_added: '4.0.0'
description: Create, update and delete ACLs for users/tokens on a Proxmox Backup Server
notes:
  - Check mode is supported.
options:
  auth_id:
    description: >
        Authentication ID to assign the ACL to. Example: john@pbs
    type: str
  path:
    description: Access control path.
    type: str
    required: yes
  propagate:
    description: Propagate this ACL so subdirectories (inherit this ACL)
    type: bool
  role:
    description: >
        Role name to be assigned to the ACL. Example: DatastoreAdmin
    type: str
    required: yes
  state:
    description: Whether this ACL should be C(present) or C(absent)
    default: present
    type: str
    choices:
      - present
      - absent

extends_documentation_fragment:
  - maxhoesel.proxmox.api_connection
"""

EXAMPLES = r"""
- name: ACL for user john is present
  maxhoesel.proxmox.pbs_acl:
    api_user: root@pam
    api_password: secret
    api_host: helldorado
    path: /datastore/backup1
    role: DatastoreBackup
    auth_id: john@pbs
"""

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.api_connection import api_connection_argspec, init

try:
    import proxmoxer
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


def _make_acl_params(module: AnsibleModule, delete=False) -> dict:
    acl_params = {
        "path": module.params["path"],
        "role": module.params["role"],
        "auth-id": module.params["auth_id"],
        "propagate": module.params["propagate"],
        "delete": delete
    }
    acl_params = {key: acl_params[key] for key in acl_params if acl_params[key] is not None}
    return acl_params


def add_acl(module: AnsibleModule, proxmox, result: dict) -> dict:
    acl = _make_acl_params(module, delete=False)
    try:
        proxmox.access.acl.put(**acl)
    except proxmoxer.ResourceException as e:
        result["msg"] = "Could not add/update ACL. Exception: {0}".format(e)
        module.fail_json(**result)
    result["changed"] = True
    return result


def delete_acl(module: AnsibleModule, proxmox, result: dict) -> dict:
    acl = _make_acl_params(module, delete=True)
    try:
        proxmox.access.acl.put(**acl)
    except proxmoxer.ResourceException as e:
        result["msg"] = "Could not delete ACL. Exception: {0}".format(e)
        module.fail_json(**result)
    result["changed"] = True
    return result


def main():

    module_args = dict(
        auth_id=dict(type="str"),
        path=dict(type="str", required=True),
        propagate=dict(type="bool"),
        role=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    result = dict(changed=False, msg="")
    module = AnsibleModule(
        argument_spec={**module_args, **api_connection_argspec},
        supports_check_mode=True
    )

    proxmox = init(module, result, "PBS")

    try:
        acls = proxmox.access.acl.get(path=module.params["path"], exact=True)
    except proxmoxer.ResourceException as e:
        result["msg"] = "Could not get ACL for {0}. Exception: {1}".format(
            module.params["path"], e)
        module.fail_json(**result)

    def acl_match(pbs_acl):
        return (
            pbs_acl["path"] == module.params["path"] and
            pbs_acl["roleid"] == module.params["role"] and
            pbs_acl["ugid"] == module.params["auth_id"]
        )
    match = [acl for acl in acls if acl_match(acl)]

    action = None
    if module.params["state"] == "present" and not match:
        action = add_acl
    elif module.params["state"] == "absent" and match:
        action = delete_acl

    if action is not None:
        if module.check_mode:
            result["changed"] = True
        else:
            result = action(module, proxmox, result)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
