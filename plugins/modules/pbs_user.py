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
    no_log: yes
  password_update:
    description: Whether to force update the password of an existing user
    type: bool
    default: no
    no_log: no
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
    userid: john@pbs
    firstname: John
    lastname: Smith
    password: johnsverysecretpassword
    email: john@example.org
    state: present

- name: Ensure that the user john@smith does not exist
  maxhoesel.proxmox.pbs_user:
    userid: john@pbs
    state: absent
"""
import os

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.api_connection import api_connection_argspec

try:
    import proxmoxer
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


def add_user(module: AnsibleModule, proxmox, result: dict) -> dict:
    user_params = {
        "userid": module.params["userid"],
        "comment": module.params["comment"],
        "email": module.params["email"],
        "enable": module.params["enabled"],
        "expire": module.params["expire"],
        "firstname": module.params["firstname"],
        "lastname": module.params["lastname"],
        "password": module.params["password"]
    }
    user_params = {key: user_params[key] for key in user_params if user_params[key]}
    try:
        proxmox.access.users.post(**user_params)
    except proxmoxer.ResourceException as e:
        result["msg"] = "Could not create user. Exception: {0}".format(e)
        module.fail_json(**result)
    result["changed"] = True
    return result


def update_user(module: AnsibleModule, proxmox, result: dict) -> dict:
    user_params = {
        "comment": module.params["comment"],
        "email": module.params["email"],
        "enable": module.params["enabled"],
        "expire": module.params["expire"],
        "firstname": module.params["firstname"],
        "lastname": module.params["lastname"],
    }
    user_params = {key: user_params[key] for key in user_params if user_params[key]}
    if module.params["password_update"]:
        user_params["password"] = module.params["password"]

    try:
        getattr(proxmox.access.users, module.params["userid"]).put(**user_params)
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

    if not HAS_PROXMOXER:
        result["msg"] = "This module requires proxmoxer >=1.2. Please install it with pip"
        module.fail_json(**result)

    if not module.params["api_password"]:
        try:
            module.params["api_password"] = os.environ["PROXMOX_PASSWORD"]
        except KeyError:
            result["msg"] = (
                "Neither api_password nor the PROXMOX_PASSWORD enviroment variable are set. "
                "Please specify a password for connecting to the PVE cluster"
            )
            module.fail_json(**result)

    try:
        proxmox = proxmoxer.ProxmoxAPI(module.params["api_host"],
                                       user=module.params["api_user"],
                                       password=module.params["api_password"],
                                       verify_ssl=module.params["validate_certs"],
                                       service="PBS")
    except Exception as e:  # pylint: disable=broad-except
        result["msg"] = "Could not connect to PVE cluster. Exception: {0}".format(e)
        module.fail_json(**result)

    try:
        userlist = proxmox.access.users.get()
    except proxmoxer.ResourceException as e:
        result["msg"] = "Could not get list of current users. Exception: {0}".format(e)
        module.fail_json(**result)

    users_by_id = {user["userid"]: user for user in userlist}
    user_exists = module.params["userid"] in users_by_id

    if not user_exists and module.params["state"] == "present":
        action = add_user
    elif user_exists and module.params["state"] == "absent":
        action = delete_user
    elif user_exists and module.params["state"] == "present":
        action = None
        if module.params["password_update"]:
            action = update_user
        else:
            user_params = {
                "userid": module.params["userid"],
                "comment": module.params["comment"],
                "email": module.params["email"],
                "enable": module.params["enabled"],
                "expire": module.params["expire"],
                "firstname": module.params["firstname"],
                "lastname": module.params["lastname"],
            }
            for param in user_params:
                if (
                    user_params[param] and
                    users_by_id[module.params["userid"]].get(param, None) != user_params[param]
                ):
                    action = update_user

    else:
        action = None

    if action is not None:
        if module.check_mode:
            result["changed"] = True
        else:
            result = action(module, proxmox, result)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
