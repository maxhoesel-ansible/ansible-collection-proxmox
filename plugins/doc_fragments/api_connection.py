# Copyright: (c) 2022, Max Hösel <ansible@maxhoesel.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment:
    DOCUMENTATION = r'''
    requirements:
      - "proxmoxer >=1.2"
      - "requests"
    options:
      api_host:
        description:
          - Specify the target host of the Proxmox VE cluster.
        required: true
        type: str
      api_user:
        description:
          - Specify the user to authenticate with.
          - When authenticating with a token, this is the owner of the token
            (C(root@pam) with O(api_token_name=ansible) refers to the token ID C(root@pam!ansible)).
        required: true
        type: str
      api_password:
        description:
          - Specify the password to authenticate with.
          - You can also use the C(PROXMOX_PASSWORD) environment variable.
        type: str
      api_token_name:
        description:
          - Name of the API token to authenticate with. The token belongs to O(api_user)
            (C(root@pam) with O(api_token_name=ansible) is the token C(root@pam!ansible)).
          - Mutually exclusive with O(api_password). Must be set together with O(api_token_secret).
          - If O(api_auth_method) is unset and both token parameters are set, the
            C(PROXMOX_PASSWORD) environment variable is ignored.
          - 'Note: the modules M(maxhoesel.proxmox.proxmox_ha) and M(maxhoesel.proxmox.ha)
            currently only support password authentication.'
        type: str
        version_added: 8.1.0
      api_token_secret:
        description:
          - Secret value of the API token specified in O(api_token_name).
          - Mutually exclusive with O(api_password). Must be set together with O(api_token_name).
        type: str
        version_added: 8.1.0
      api_auth_method:
        description:
          - Explicitly select the authentication method.
          - If unset, authentication is determined automatically. A complete token
            (O(api_token_name) and O(api_token_secret)) takes precedence, then O(api_password),
            then the C(PROXMOX_PASSWORD) environment variable.
          - When set to V(token), no password credentials (O(api_password) or
            C(PROXMOX_PASSWORD)) may be present.
          - When set to V(password), no token parameters may be present.
        type: str
        choices:
          - token
          - password
        version_added: 8.1.0
      validate_certs:
        description:
          - Validate SSL certificate of the PVE host upon connecting
        default: false
        type: bool
    '''
