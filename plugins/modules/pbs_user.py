#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Max Hösel <ansible@maxhoesel.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r"""
---
module: pbs_user
author: Max Hösel (@maxhoesel)
short_description: Manage users on a Proxmox Backup Server
version_added: '4.0.0'
description: Create, update and delete user accounts on a Proxmox backup Server instance.
notes:
  - Check mode is supported.
  - Only PBS-Native users are currently supported (i.e. the @pbs realm)
options:
  comment:
    description: User account comment
    type: str
  email:
    description: E-Mail Address of the user
    type: str
  enabled:
    description: Whether to enable the account. false means disabled.
    type: bool
  expire:
    description: Account expiration data (seconds since UNIX epoch). 0 means no expiration date
    type: int
  firstname:
    description: User First Name
    type: str
  lastname:
    description: User Last Name
    type: str
  password:
    description: >
        Password for the user. Note that this module does B(not) update the password by default!
        To force this behavior (this also causes the module to always return as changed), set I(password_update) to True
    type: str
  password_update:
    description: Whether to force update the password of an existing user
    type: bool
    default: no
    aliases:
      - update_password
  state:
    description: C(present) makes sure the user exists, C(absent) makes sure the user is removed.
    default: present
    type: str
    choices:
      - present
      - absent
  userid:
    description: >
        User ID, in the format "user@realm". Example: john@pbs
    aliases:
      - name
      - id
    type: str
    required: yes

extends_documentation_fragment:
  - maxhoesel.proxmox.api_connection
"""

EXAMPLES = r"""
- name: Ensure that the user john@pbs exists
  maxhoesel.proxmox.pbs_user:
    api_user: root@pam
    api_password: secret
    api_host: helldorado
    userid: john@pbs
    firstname: John
    lastname: Smith
    password: johnsverysecretpassword
    email: john@example.org
    state: present

- name: Ensure that the user john@smith does not exist
  maxhoesel.proxmox.pbs_user:
    api_user: root@pam
    api_password: secret
    api_host: helldorado
    userid: john@pbs
    state: absent
"""

try:
    import proxmoxer
except ImportError:
    pass  # Handled in init()

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.api_connection import api_connection_argspec, init


def _make_user_params(module: AnsibleModule, include_password=True) -> dict:
    user_params = {
        "userid": module.params["userid"],
        "comment": module.params["comment"],
        "email": module.params["email"],
        "enable": module.params["enabled"],
        "expire": module.params["expire"],
        "firstname": module.params["firstname"],
        "lastname": module.params["lastname"],
    }
    user_params = {key: user_params[key] for key in user_params if user_params[key] is not None}
    if include_password:
        user_params["password"] = module.params["password"]
    return user_params


def add_user(module: AnsibleModule, proxmox, result: dict) -> dict:
    user = _make_user_params(module)

    try:
        proxmox.access.users.post(**user)
    except proxmoxer.ResourceException as e:
        result["msg"] = "Could not create user. Exception: {0}".format(e)
        module.fail_json(**result)
    result["changed"] = True
    return result


def update_user(module: AnsibleModule, proxmox, result: dict) -> dict:
    user = _make_user_params(module, include_password=module.params["password_update"])

    try:
        getattr(proxmox.access.users, module.params["userid"]).put(**user)
    except proxmoxer.ResourceException as e:
        result["msg"] = "Could not update user. Exception: {0}".format(e)
        module.fail_json(**result)
    result["changed"] = True

    return result


def delete_user(module: AnsibleModule, proxmox, result: dict) -> dict:
    try:
        getattr(proxmox.access.users, module.params["userid"]).delete()
    except proxmoxer.ResourceException as e:
        result["msg"] = "Could not delete user. Exception: {0}".format(e)
        module.fail_json(**result)
    result["changed"] = True
    return result


def main():
    module_args = dict(
        comment=dict(type="str"),
        email=dict(type="str"),
        enabled=dict(type="bool"),
        expire=dict(type="int"),
        firstname=dict(type="str"),
        lastname=dict(type="str"),
        password=dict(type="str", no_log=True),
        password_update=dict(type="bool", no_log=False, aliases=["update_password"], default=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        userid=dict(type="str", required=True, aliases=["name", "id"])
    )
    result = dict(changed=False, msg="")
    module = AnsibleModule(
        argument_spec={**module_args, **api_connection_argspec},
        supports_check_mode=True,
        required_if=[("password_update", True, ["password"])]
    )

    proxmox = init(module, result, "PBS")

    try:
        userlist = proxmox.access.users.get()
    except proxmoxer.ResourceException as e:
        result["msg"] = "Could not get list of current users. Exception: {0}".format(e)
        module.fail_json(**result)

    users_by_id = {user["userid"]: user for user in userlist}
    user_exists = module.params["userid"] in users_by_id

    action = None
    if not user_exists and module.params["state"] == "present":
        action = add_user
    elif user_exists and module.params["state"] == "absent":
        action = delete_user
    elif user_exists and module.params["state"] == "present":
        if module.params["password_update"]:
            action = update_user
        else:
            params = _make_user_params(module, include_password=False)
            for param in params:
                if users_by_id[module.params["userid"]].get(param, None) != params[param]:
                    action = update_user

    if action is not None:
        if module.check_mode:
            result["changed"] = True
        else:
            result = action(module, proxmox, result)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
