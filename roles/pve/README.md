# maxhoesel.proxmox.pve

Configure an existing Proxmox Virtual Environment hosts system.

Note that this role does not manage PVE settings itself (such as VMS and storage), but rather
the underlying system. Right now, it manages the root users password and configures the PVE repository

## Requirements

- A PVE host accessible via SSH and a user with become privileges

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
