#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Max Hösel <ansible@maxhoesel.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r"""
---
module: pbs_datastore
author: Max Hösel (@maxhoesel)
short_description: Manage datastores on PBS
version_added: '4.0.0'
description: Create, update and delete datastores on a Proxmox Backup Server
notes:
  - Check mode is supported.
options:
  comment:
    description: Comment for the datastore (visible in UI)
    type: str
  gc_schedule:
    description: Run garbace collection job at specified schedule. Must be a calendar event (i.e C(daily), C(Tue 04:27))
    type: str
  keep_last:
    description: Number of backups to keep
    type: int
  keep_hourly:
    description: Number of hourly backups to keep
    type: int
  keep_daily:
    description: Number of daily backups to keep
    type: int
  keep_weekly:
    description: Number of weekly backups to keep
    type: int
  keep_monthly:
    description: Number of monthly backups to keep
    type: int
  keep_yearly:
    description: Number of yearly backups to keep
    type: int
  name:
    description: Name of the datastore
    type: str
    required: yes
  notify:
    description: Datastore notification settings
    type: dict
    suboptions:
      gc:
        description: Garbage Collection notification setting
        type: str
        choices: ["always", "never", "errors"]
      sync:
        description: Sync Jobs notification setting
        type: str
        choices: ["always", "never", "errors"]
      verify:
        description: Verification notification setting
        type: str
        choices: ["always", "never", "errors"]
  notify_user:
    description: User ID to notify
    type: str
  path:
    description: Backing path for the datastore. Required when creating a new datastore
    type: str
  prune_schedule:
    description: Run prune job at specified schedule. Must be a calendar event (i.e C(daily), C(Tue 04:27))
    type: str
  state:
    description: Whether this datastore should be C(present) or C(absent)
    default: present
    type: str
    choices:
      - present
      - absent
  verify_new:
    description: If enabled, all new backups will be verified right after completion
    type: bool

extends_documentation_fragment:
  - maxhoesel.proxmox.api_connection
"""

EXAMPLES = r"""
- name: Create/Update a datastore
  maxhoesel.proxmox.pbs_datastore:
    api_user: root@pam
    api_password: secret
    api_host: helldorado
    name: test-datastore
    path: /mnt/somedisk/thisdirectory
    gc_schedule: daily
    prune_schedule: daily
    keep_daily: 7
    keep_weekly: 4
    keep_monthly: 6
    notify:
      gc: errors
      verify: errors
      sync: errors
    verify_new: yes
"""

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.api_connection import api_connection_argspec, init

try:
    import proxmoxer
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


def _make_datastore_params(module: AnsibleModule) -> dict:
    notify = ",".join([key + "=" + module.params["notify"][key] for key in module.params["notify"]])
    datastore_params = {
        "name": module.params["name"],
        "path": module.params["path"],
        "comment": module.params["comment"],
        "gc-schedule": module.params["gc_schedule"],
        "keep-last": module.params["keep_last"],
        "keep-hourly": module.params["keep_hourly"],
        "keep-daily": module.params["keep_daily"],
        "keep-weekly": module.params["keep_weekly"],
        "keep-monthly": module.params["keep_monthly"],
        "keep-yearly": module.params["keep_yearly"],
        "notify-user": module.params["notify_user"],
        "notify": notify,
        "prune_schedule": module.params["prune_schedule"],
        "verify-new": module.params["verify_new"]
    }
    datastore_params = {key: datastore_params[key]
                        for key in datastore_params if datastore_params[key] is not None}
    return datastore_params


def add_datastore(module: AnsibleModule, proxmox, result: dict) -> dict:
    datastore = _make_datastore_params(module)

    if "path" not in datastore:
        result["msg"] = "path is required to create a new datastore"
        module.fail_json(**result)

    try:
        proxmox.config.datastore.post(**datastore)
    except proxmoxer.ResourceException as e:
        result["msg"] = "Could not create datastore. Exception: {0}".format(e)
        module.fail_json(**result)
    result["changed"] = True
    return result


def update_datastore(module: AnsibleModule, proxmox, result: dict) -> dict:
    datastore = _make_datastore_params(module)

    try:
        getattr(proxmox.config.datastore, module.params["name"]).put(**datastore)
    except proxmoxer.ResourceException as e:
        result["msg"] = "Could not update datastore. Exception: {0}".format(e)
        module.fail_json(**result)
    result["changed"] = True

    return result


def delete_datastore(module: AnsibleModule, proxmox, result: dict) -> dict:
    datastore = _make_datastore_params(module)
    try:
        proxmox.access.acl.put(**datastore)
    except proxmoxer.ResourceException as e:
        result["msg"] = "Could not delete datastore. Exception: {0}".format(e)
        module.fail_json(**result)
    result["changed"] = True
    return result


def main():

    module_args = dict(
        comment=dict(type="str"),
        gc_schedule=dict(type="str"),
        keep_last=dict(type="int"),
        keep_hourly=dict(type="int"),
        keep_daily=dict(type="int"),
        keep_weekly=dict(type="int"),
        keep_monthly=dict(type="int"),
        keep_yearly=dict(type="int"),
        name=dict(type="str", required=True),
        notify=dict(type="dict", options=dict(
            gc=dict(type="str", choices=["always", "never", "errors"]),
            sync=dict(type="str", choices=["always", "never", "errors"]),
            verify=dict(type="str", choices=["always", "never", "errors"])
        )),
        notify_user=dict(type="str"),
        path=dict(type="str"),
        prune_schedule=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        verify_new=dict(type="bool")
    )
    result = dict(changed=False, msg="")
    module = AnsibleModule(
        argument_spec={**module_args, **api_connection_argspec},
        supports_check_mode=True
    )

    proxmox = init(module, result, "PBS")

    try:
        datastores = proxmox.config.datastore.get()
    except proxmoxer.ResourceException as e:
        result["msg"] = "Could not get list of datastores. Exception: {0}".format(e)
        module.fail_json(**result)

    datastores_by_name = {ds["name"]: ds for ds in datastores}
    datastore_exists = module.params["name"] in datastores_by_name

    action = None
    if not datastore_exists and module.params["state"] == "present":
        action = add_datastore
    elif datastore_exists and module.params["state"] == "absent":
        action = delete_datastore
    elif datastore_exists and module.params["state"] == "present":
        params = _make_datastore_params(module)
        for param in params:
            if datastores_by_name[module.params["name"]].get(param, None) != params[param]:
                action = update_datastore

    if action is not None:
        if module.check_mode:
            result["changed"] = True
        else:
            result = action(module, proxmox, result)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
