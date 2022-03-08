#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Max Hösel < ansible at maxhoesel.de >
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
import re
import os
__metaclass__ = type


ANSIBLE_METADATA = {"metadata_version": "1.1",
                    "status": ["preview"],
                    "supported_by": "community"}


DOCUMENTATION = r"""
---
module: proxmox_ha
short_description: Manage HA in a Proxmox cluster
description:
  - Manage the HA status/membership of individual guests in a Proxmox VE cluster
version_added: "2.8"
author: "Max Hösel < ansible @ maxhoesel.de >"
options:
  comment:
    description:
      - Add a comment to the HA resource. This comment is not parsed and is only used for documentation.
  digest:
    description:
      - Specify if to prevent changes if current configuration file has different SHA1 digest.
      - This can be used to prevent concurrent modifications.
  group:
    description:
      - Specify the HA group that the guest should be a member of
  max_relocate:
    description:
      - Specify the maximum number of relocates to attempt before a service is considered "failed"
  max_restart:
    description:
      - Specify the maximum number of restarts to attempt before a service is considered "failed"
  name:
    description:
      - Specify the name of the guest whose HA resource will be modified. Automatically fetches the correct VMID. You can also specify the VMID directly using C(vmid).
  state:
    description:
      - C(present): Alias for C(started)
      - C(absent): Will remove the HA resource if present
      - C(started)/C(stopped)/C(disabled)/C(ignored): Will configure the resource and set the PVE HA state to the requested value
      - For more information on the individual states, please refer to the PVE documentaiton
    default: present
  vmid:
    description:
      - Specify the VMID of the guest whose HA resource will be modified. Will be fetched automatically if C(name) is set.

extends_documentation_fragment:
  - maxhoesel.proxmox.api_connection
"""

EXAMPLES = """
# Create a basic HA resource for a guest (and ensure that the guest is started)
- proxmox_ha:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : myvirtualmachine

# Create a HA resource for a VMID and set the state to "stopped"
- proxomx_ha:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    vmid        : 123
    state       : stopped

# Remove a HA resource by guest name
- proxomx_ha:
    api_user    : root@pam
    api_password: secret
    api_host    : helldorado
    name        : myvirtualmachine
    state       : absent
"""

from ..module_utils.api_connection import api_connection_argspec

try:
    import proxmoxer
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


def main():
    m = AnsibleModule(
        argument_spec={**dict(
            comment=dict(),
            digest=dict(),
            group=dict(),
            max_relocate=dict(type="int"),
            max_restart=dict(type="int"),
            name=dict(),
            state=dict(choices=["present", "absent", "started",
                                "stopped", "disabled", "ignored"], default="started"),
            vmid=dict(),
        ), **api_connection_argspec},
        required_one_of=[("name", "vmid",)],
        supports_check_mode=True
    )

    if not HAS_PROXMOXER:
        m.fail_json(
            msg="This module requires proxmoxer. Please install it with pip")

    if not m.params["api_password"]:
        try:
            m.params["api_password"] = os.environ["PROXMOX_PASSWORD"]
        except KeyError:
            m.fail_json(msg="Neither api_password nor the PROXMOX_PASSWORD enviroment variable are set."
                        "Please specify a password for connecting to the PVE cluster")
    # Initialize Proxmox API
    PVE_MAJOR_VERSION = None
    try:
        proxmox = proxmoxer.ProxmoxAPI(m.params["api_host"],
                                       user=m.params["api_user"],
                                       password=m.params["api_password"],
                                       verify_ssl=m.params["validate_certs"])
        PVE_MAJOR_VERSION = int(proxmox.version.get()["version"].split(".")[0])
    except Exception as e:  # pylint: disable=broad-except
        m.fail_json(
            msg="Could not connect to PVE cluster. Exception: {0}".format(e))

    if PVE_MAJOR_VERSION <= 3:
        m.fail_json(
            msg="This module only supports the new HA stack introduced in Proxmox PVE 4.0")

    vmid = m.params["vmid"]
    # Convert "name" to a VMID if needed
    if not vmid:
        try:
            vmid = str([vm["vmid"] for vm in proxmox.cluster.resources.get(type="vm")
                        if vm["name"] == m.params["name"]][0])
        except IndexError:
            m.fail_json(msg="Could not VMID for name {0} in cluster resources".format(
                m.params["name"]))
        except proxmoxer.ResourceException:
            m.fail_json(msg="Could not get PVE resource information")

    # Check if a resource already exists in the cluster config.
    try:
        _resources_list = proxmox.cluster.ha.resources.get()
    except proxmoxer.ResourceException as e:
        m.fail_json(msg="Could not get HA resource list from pve cluster."
                    "Is your cluster healthy? Exception: {0}".format(e))
    _resources = [res for res in _resources_list
                  if re.match("^[a-z]+:{0}$".format(vmid), res["sid"])]
    if _resources:
        # Remove the "ct/vm" prefix from sid - Proxmox can just use the VMID itself
        _resources[0]["sid"] = _resources[0]["sid"].split(":")[1]
        # max_restart and max_reloacte have a default of 1 set in PVE, but the api doesn't
        # expose this. We thus manually assign max_restart/max_value = 1 to ensure idemoptency
        # between runs if these keys are not exported by the api
        _resources[0]["max_restart"] = _resources[0].get("max_restart", 1)
        _resources[0]["max_relocate"] = _resources[0].get("max_relocate", 1)
        _resources[0]["state"] = _resources[0].get("state", "started")
        try:
            # No need for this key as we don't expose it
            _resources[0].pop("type")
        except KeyError:
            pass
        current_config = _resources[0]
    else:
        current_config = {}

    if m.params["state"] == "absent":
        if not current_config:
            m.exit_json(changed=False,
                        msg="Resource {0} does not exist".format(vmid))
        else:
            # Remove the resource
            if not m.check_mode:
                try:
                    getattr(proxmox.cluster.ha.resources, vmid).delete()
                except proxmoxer.ResourceException as e:
                    m.fail_json(msg="Could not remove HA resource {0}. Exception: {1}".format(
                        m.params["vmid]"], e))
            m.exit_json(changed=True, msg="Resource {0} removed".format(vmid))
    else:
        # Create our desired config from the passed parameters
        desired_config = {
            "sid": vmid,  # We can just use vmid without the need to check for ct/vm
            "state": m.params["state"],
            "comment": m.params["comment"],
            "digest": m.params["digest"],
            "group": m.params["group"],
            "max_relocate": m.params["max_relocate"],
            "max_restart": m.params["max_restart"],
        }

        # Any keys that are not explicitly passed to us can be ignored safely
        # and will not be considered when comparing the resources
        # list() creates a copy of the dict keys so that we can iterate
        for key in list(desired_config):
            if not desired_config[key]:
                try:
                    current_config.pop(key)
                except KeyError:
                    pass
                desired_config.pop(key)

        if not current_config:
            # No remote resource, so we can just create one
            if not m.check_mode:
                try:
                    proxmox.cluster.ha.resources.post(**desired_config)
                except proxmoxer.ResourceException as e:
                    m.fail_json(
                        msg="Could not add HA resource {0}. Exception: {1}".format(vmid, e))
            m.exit_json(changed=True, msg="Added resource {0}".format(
                vmid), resource=desired_config)
        else:
            # Remote resource exists, compare and update if required
            if desired_config == current_config:
                m.exit_json(changed=False)
            else:
                if not m.check_mode:
                    # Get rid of sid in the API call, it's already in the URI
                    _t = desired_config
                    _t.pop("sid")
                    try:
                        getattr(proxmox.cluster.ha.resources, vmid).put(**_t)
                    except proxmoxer.ResourceException as e:
                        m.fail_json(
                            msg="Could not change HA resource {0}. Exception: {1}".format(vmid, e))
                m.exit_json(changed=True, msg="Changed resource {0}".format(vmid),
                            old=current_config, new=desired_config)


if __name__ == "__main__":
    main()
