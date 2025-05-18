#!/usr/bin/python

# Copyright: (c) 2022, Max Hösel <ansible@maxhoesel.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# pylint: disable=duplicate-code
DOCUMENTATION = r"""
---
module: pbs_token
author: Max Hösel (@maxhoesel)
short_description: Manage user tokens on a Proxmox Backup Server
version_added: '4.0.0'
description: Create, update and delete user API tokens on a Proxmox backup Server instance.
notes:
  - Check mode is supported.
options:
  comment:
    description: Comment for the token
    type: str
  enabled:
    description: Whether to enable the token. false means disabled.
    type: bool
  expire:
    description: Token expiration data (seconds since UNIX epoch). 0 means no expiration date
    type: int
  name:
    description: "Name of the token that will be part of the authid. Example: C(token1) results in the authid C(user@pbs!token1)"
    aliases:
      - token_name
    required: yes
    type: str
  state:
    description: C(present) makes sure the user exists, C(absent) makes sure the user is removed.
    default: present
    type: str
    choices:
      - present
      - absent
  userid:
    description: User that the token will be created for. Must be in C(user@realm) format (e.g. C(john@pbs))
    required: yes
    type: str

extends_documentation_fragment:
  - maxhoesel.proxmox.api_connection
"""

EXAMPLES = r"""
- name: Create an API token for a user
  maxhoesel.proxmox.pbs_token:
    api_user: root@pam
    api_password: secret
    api_host: helldorado
    name: mytoken
    userid: john@pbs
"""

RETURN = r"""
tokenid:
  description: API Token identifier
  returned: always
  type: str
secret:
  description: API Token secret
  returned: When the token is created
  type: str
"""
try:
    import proxmoxer
except ImportError:
    pass  # Handled in init()

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.api_connection import api_connection_argspec, init


def _make_token_params(module: AnsibleModule) -> dict:
    token_params = {
        "comment": module.params["comment"],
        "enable": module.params["enabled"],
        "expire": module.params["expire"],
    }
    token_params = {key: token_params[key] for key in token_params if token_params[key] is not None}
    return token_params


def add_token(module: AnsibleModule, proxmox, result: dict) -> dict:
    token = _make_token_params(module)

    try:
        r = getattr(getattr(proxmox.access.users, module.params["userid"]).token,
                    module.params["name"]).post(**token)
    except proxmoxer.ResourceException as e:
        result["msg"] = f"Could not create token. Exception: {e}"
        module.fail_json(**result)
    result["tokenid"] = r["tokenid"]
    result["secret"] = r["value"]

    result["changed"] = True
    return result


def update_token(module: AnsibleModule, proxmox, result: dict) -> dict:
    token = _make_token_params(module)

    try:
        getattr(getattr(proxmox.access.users, module.params["userid"]).token,
                module.params["name"]).put(**token)
    except proxmoxer.ResourceException as e:
        result["msg"] = f"Could not update token. Exception: {e}"
        module.fail_json(**result)

    result["changed"] = True
    return result


def delete_token(module: AnsibleModule, proxmox, result: dict) -> dict:
    try:
        getattr(getattr(proxmox.access.users, module.params["userid"]).token,
                module.params["name"]).delete()
    except proxmoxer.ResourceException as e:
        result["msg"] = f"Could not delete token. Exception: {e}"
        module.fail_json(**result)

    result["changed"] = True
    return result


def main():
    module_args = dict(
        comment=dict(type="str"),
        enabled=dict(type="bool"),
        expire=dict(type="int"),
        name=dict(type="str", required=True, aliases=["token_name"]),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        userid=dict(type="str", required=True)
    )
    result = dict(changed=False, msg="")
    module = AnsibleModule(
        argument_spec={**module_args, **api_connection_argspec},
        supports_check_mode=True
    )

    proxmox = init(module, result, "PBS")

    try:
        tokenlist = getattr(proxmox.access.users, module.params["userid"]).token.get()
    except proxmoxer.ResourceException as e:
        result["msg"] = f"Could not get list tokens for user {module.params['userid']}. Exception: {e}"
        module.fail_json(**result)

    tokens_by_name = {token["token-name"]: token for token in tokenlist}
    token_exists = module.params["name"] in tokens_by_name

    action = None
    if not token_exists and module.params["state"] == "present":
        action = add_token
    elif token_exists and module.params["state"] == "absent":
        action = delete_token
    elif token_exists and module.params["state"] == "present":
        params = _make_token_params(module)
        for param in params:
            if tokens_by_name[module.params["userid"]].get(param, None) != params[param]:
                action = update_token

    if action is not None:
        if module.check_mode:
            result["changed"] = True
        else:
            result = action(module, proxmox, result)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
