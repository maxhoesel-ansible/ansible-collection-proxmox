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
        required: true
        type: str
      api_password:
        description:
          - Specify the password to authenticate with.
          - You can also use the C(PROXMOX_PASSWORD) environment variable.
        type: str
      validate_certs:
        description:
          - Validate SSL certificate of the PVE host upon connecting
        default: false
        type: bool
    '''
