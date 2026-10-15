# Copyright: (c) 2022, Max Hösel <ansible@maxhoesel.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import os

api_connection_argspec = dict(
    api_host=dict(type="str", required=True),
    api_user=dict(type="str", required=True),
    api_password=dict(type="str", no_log=True),
    api_token_name=dict(type="str"),
    api_token_secret=dict(type="str", no_log=True),
    api_auth_method=dict(type="str", choices=["token", "password"], default=None),
    validate_certs=dict(type="bool", default=False)
)

try:
    import proxmoxer
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


def _resolve_auth_method(module, result):
    """Validate and select the authentication method.

    Returns "password" or "token" and (for password auth) assigns the
    PROXMOX_PASSWORD environment variable to module.params["api_password"].
    """
    auth_method = module.params["api_auth_method"]
    has_password = bool(module.params["api_password"])
    has_token = bool(module.params["api_token_name"]) and bool(module.params["api_token_secret"])

    if auth_method == "token":
        if module.params["api_password"] or "PROXMOX_PASSWORD" in os.environ:
            result["msg"] = "api_auth_method: token cannot be combined with password credentials"
            module.fail_json(**result)
        if not has_token:
            result["msg"] = (
                "api_auth_method is set to token, but api_token_name and api_token_secret "
                "are not both set. Please specify a complete API token")
            module.fail_json(**result)
        return "token"

    if auth_method == "password":
        if module.params["api_token_name"] or module.params["api_token_secret"]:
            result["msg"] = "api_auth_method: password cannot be combined with token credentials"
            module.fail_json(**result)
        if has_password:
            return "password"
        try:
            module.params["api_password"] = os.environ["PROXMOX_PASSWORD"]
        except KeyError:
            result["msg"] = (
                "api_auth_method is set to password, but neither api_password nor the "
                "PROXMOX_PASSWORD environment variable are set")
            module.fail_json(**result)
        return "password"

    if has_token:
        if has_password:
            result["msg"] = "ambiguous credentials: supply only one method or set api_auth_method"
            module.fail_json(**result)
        return "token"

    if bool(module.params["api_token_name"]) or bool(module.params["api_token_secret"]):
        result["msg"] = (
            "Incomplete API token: api_token_name and api_token_secret must be set together")
        module.fail_json(**result)

    if has_password:
        return "password"
    try:
        module.params["api_password"] = os.environ["PROXMOX_PASSWORD"]
    except KeyError:
        result["msg"] = (
            "No authentication credentials found. Please specify either api_password (or the "
            "PROXMOX_PASSWORD environment variable) or a complete API token "
            "(api_token_name and api_token_secret), or set api_auth_method")
        module.fail_json(**result)
    return "password"


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

    auth_method = _resolve_auth_method(module, result)

    try:
        if auth_method == "token":
            proxmox = proxmoxer.ProxmoxAPI(module.params["api_host"],
                                           user=module.params["api_user"],
                                           token_name=module.params["api_token_name"],
                                           token_value=module.params["api_token_secret"],
                                           verify_ssl=module.params["validate_certs"],
                                           service=service)
        else:
            proxmox = proxmoxer.ProxmoxAPI(module.params["api_host"],
                                           user=module.params["api_user"],
                                           password=module.params["api_password"],
                                           verify_ssl=module.params["validate_certs"],
                                           service=service)
    except Exception as e:  # pylint: disable=broad-except
        result["msg"] = f"Could not connect to {service} host. Exception: {e}"
        module.fail_json(**result)
    return proxmox
