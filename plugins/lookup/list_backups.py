from ansible.plugins.lookup import LookupBase

try:
    import proxmoxer

    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


DOCUMENTATION = """
    name: list_backups
    author: Julian Vanden Broeck
    version_added: "5.0.2"

    short_description: retrieve list of backups for a VM or CT
    description:
      - Returns a list of backup realted to a promox node and storage. We can
        also use this to get all backup related to a VM or CT.
    options:
      _terms:
        description: list of files to template
      api_host:
        description: host exposing the Proxmox API
        default: localhost
        version_added: '5.0.2'
        type: str
      api_user:
        description: User to consume the Proxmox API
        default: user
        version_added: '5.0.2'
        type: str
      api_password:
        description: Password of the user to consume the Proxmox API
        default: password
        version_added: '5.0.2'
        type: str
      validate_certs:
        description: Boolean to define if we need to verify the TLS certificate
        default: false
        version_added: '5.0.2'
        type: bool
      node:
        description: Name of the node we want to query
        default: node0
        version_added: '5.0.2'
        type: str
      storage:
        description: Name of the storage we want to analyse
        default: datastore
        version_added: '5.0.2'
        type: str
      vmid:
        description: VM/CT ID we want to list of backup (if none return all)
        required: False
        version_added: '5.0.2'
        type: int
"""


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)

        # connect to our proxmox node / cluster
        proxmox = proxmoxer.ProxmoxAPI(
            self.get_option("api_host"),
            user=self.get_option("api_user"),
            password=self.get_option("api_password"),
            verify_ssl=self.get_option("validate_certs"),
        )

        # build list of param (mainly vmid)
        req_params = []
        if self.get_option("vmid") is not None:
            req_params.append("vmid=" + str(self.get_option("vmid")))

        # Then query the proxmox API
        return (
            proxmox.nodes(self.get_option("node"))
            .storage(self.get_option("storage"))
            .content.get("?" + "&".join(req_params))
        )
