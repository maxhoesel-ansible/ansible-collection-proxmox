# maxhoesel.proxmox.pve

A role to perform basic setup tasks on a PVE node, such as repository and CPU configuration.

The following features are available and can be enabled/disabled individually:

- Set a PVE repository (enterprise, no-subscription, test) (required)
- Install CPU microcode for AMD/Intel from the `non-free` debian source component
- Set the PVE root password
- Optimize the CPU governor selection
- Support PCIe Passthrough by enabling the required modules

## Requirements

- A PVE host accessible via SSH and a user with become privileges
- This role needs to be run with `become: true`

## Role Variables

##### `pve_root_password`
- Password for the root user
- Must be a string of at least 8 characters
- Required: `false`
- Default: undefined

##### `pve_repo_type`
- Selects which PVE repository is enabled for pulling updates
- Choices: `enterprise`, `no-subscription`, `test`
- Please note that this role does not configure your subscription key, you will have to do so yourself
- Default: `no-subscription`


### CPU Settings

##### `pve_install_ucode`
- Whether to install the microcode packages for your appropriate CPU
- On PVE 7 and below, this will also enable the required `non-free` repository containing the ucode package
- On PVE 8, this will activate the `non-free-firmware` component instead
- On PVE 9 and above, this repository is already enabled, so only the CPU ucode package will be installed
- Default: `false`

##### `pve_reboot_for_ucode`
- Whether to reboot the host after microcode has been installed (if required)
- If set to `false`, you may have to manually reboot the node to load the microcode
- This has no effect if `pve_install_ucode` is disabled
- Default: `true`

##### `pve_set_cpu`
- Whether to modify the CPU configuration, such as the chosen governor.
- Default: `false`

##### `pve_cpu_governor`
- Which CPU governor to use for all CPU cores on each node
- You can check which CPU governors are available for your CPU and driver by running
  `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors` on one of your nodes.
- If you have an AMD CPU (Zen2 or newer) with a new Kernel (6.5 or newer, PVE8) or have an Intel CPU (Sandy Bridge or newer):
    - the system will use a hardware-backed scaling driver, either `intel_pstate` or `amd_pstate_(epp)`.
    - You can set a preference with either `powersave` or `performance`
- If you are on an older Kernel or have an older CPU:
  - You can use any [generic governor](https://www.kernel.org/doc/Documentation/cpu-freq/governors.txt).
- Proxmox defaults to `performance` due to potential [BSODs in Windows guests when running with variable frequency](https://forum.proxmox.com/threads/windows-7-x64-vms-crashing-randomly-during-process-termination.18238/#post-93273)
- More Information on the [Arch Wiki](https://wiki.archlinux.org/title/CPU_frequency_scaling#Scaling_drivers)
- Default: `performance`. To save power, set to `powersave` on modern systems with a hardware driver, or `schedutil` on systems without.

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
