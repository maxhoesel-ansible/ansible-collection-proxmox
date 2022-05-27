# Copyright: (c) 2022, Max Hösel <ansible@maxhoesel.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import os

api_connection_argspec = dict(
    api_host=dict(type="str", required=True),
    api_user=dict(type="str", required=True),
    api_password=dict(type="str", no_log=True),
    validate_certs=dict(type="bool", default=False)
)

try:
    import proxmoxer
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


def init(module, result, service):
    """Connect to a Proxmox API server and return an API connection object

    Args:
        module (AnsibleModule): The calling module object
        result (dict): The result dict
        service (str): Service to connect to. Options are "PVE", "PBS", "PMG"
    """
    if not HAS_PROXMOXER:
        result["msg"] = "This module requires proxmoxer >=1.2. Please install it with pip"
        module.fail_json(**result)

    if not module.params["api_password"]:
        try:
            module.params["api_password"] = os.environ["PROXMOX_PASSWORD"]
        except KeyError:
            result["msg"] = (
                "Neither api_password nor the PROXMOX_PASSWORD environment variable are set. "
                "Please specify a password for connecting to the PVE cluster"
            )
            module.fail_json(**result)

    try:
        proxmox = proxmoxer.ProxmoxAPI(module.params["api_host"],
                                       user=module.params["api_user"],
                                       password=module.params["api_password"],
                                       verify_ssl=module.params["validate_certs"],
                                       service=service)
    except Exception as e:  # pylint: disable=broad-except
        result["msg"] = f"Could not connect to {service} host. Exception: {e}"
        module.fail_json(**result)
    return proxmox
