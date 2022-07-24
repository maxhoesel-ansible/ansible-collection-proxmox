# maxhoesel.proxmox.pve

A role to perform basic setup tasks on a PVE node, such as repository and CPU configuration.

The following features are available and can be enabled/disabled individually:

- Set a PVE repository (enterprise, no-subscription, test) (required)
- Set the PVE root password (required)
- Set the CPU governor to save power or improve performance
- Support PCIe Passthrough by enabling the required modules

## Requirements

- A PVE host accessible via SSH and a user with become privileges
- This role needs to be run with `become: true`

## Role Variables

##### `pve_root_password`
- Password for the root user
- Must be a string of at least 8 characters
- Required: `true`
- Default: undefined

##### `pve_repo_type`
- Selects which PVE repository is enabled for pulling updates
- Choices: `enterprise`, `no-subscription`, `test`
- Please note that this role does not configure your subscription key, you will have to do so yourself
- Default: `no-subscription`

### CPU Settings

##### `pve_set_cpu`
- Whether to modify the CPU configuration, such as the chosen governor.
- Default: `false`

##### `pve_cpu_governor`
- Which CPU governor to use for all CPU cores on each node
- You can check which CPU governors are available for your CPU and driver by running
  `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors` on one of your nodes.
  - The `intel_pstate` driver hands much of the CPU scaling off to the hardware and only supports two governors - `powersave` and `performance`.
    See the [kernel docs](https://www.kernel.org/doc/html/v4.19/admin-guide/pm/intel_pstate.html) for more information.
  - Older Intel CPUs under (`intel_cpufreq`) and AMD CPUs can use any [generic governor](https://www.kernel.org/doc/Documentation/cpu-freq/governors.txt).
  - Proxmox defaults to `performance` due to potential [BSODs in Windows guests when running with variable frequency](https://forum.proxmox.com/threads/windows-7-x64-vms-crashing-randomly-during-process-termination.18238/#post-93273)
  - `ondemand` and `schedutil` both scale CPU frequency dynamically and may improve power consumption.
- Default: `performance`. Set to `schedutil` if you want to save power and aware of the limitations mentioned above.

### PCIe Passthrough

##### `pve_enable_pcie_passthrough`
- Whether to enable and configure PCIe passthrough on the host
- If enabled, this will load the required kernel modules (and add intel_iommu=on to the kernel commandline on Intel CPUs)
- Default: `false`

##### `pve_pcie_reboot_for_kernel`
- Whether to automatically reboot the node to load the required kernel modules
- If set to `false`, you may have to manually reboot the node to enable PCIe passthrough
- This has no effect if `pve_enable_pcie_passthrough` is disabled
- Default: `true`
