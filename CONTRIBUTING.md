# Contribution Guide

This document contains the information needed to contribute to this project.
In here you will find the basic steps for getting started, as well as an overview over our testing system.

Note that by contributing to this collection, you agree with the code of conduct you can find [here.](/CODE_OF_CONDUCT.md)

## Getting Started

Prerequisites:

- A recent version of Python supported by `ansible-core` (see [here](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#control-node-requirements))
- For role tests: `podman` 4 or newer set up as shown [below](#setting-up-podman) (note that Docker will *not* work for role tests!)
- For plugin tests: A recent version of Docker

Steps:

1. Clone the repository (or your fork) to your local machine
2. Run `./scripts/setup.sh`. This will set up a virtual environment with all required dependencies for development
3. Activate the virtualenv with `source .venv/bin/activate`
4. Make your changes
5. Run the relevant tests using the instructions in [here](#testing-changes)
6. Once you're done, commit your changes and open a PR

## Developing Content

### Plugins (and Modules)

The plugins in this collection focus on providing access to the Proxmox VE and Backup API
In general, each module exposes one endpoint of the API so that it can be accessed from Ansible.
Feel free to add new modules for endpoints not yet covered by this collection, but try to prevent
overlap with the existing modules in `community.general` (such as `proxmox` and `proxmox_kvm`, see [here](https://docs.ansible.com/ansible/latest/collections/community/general/index.html#plugin-index) for a complete list).

Here are some general hints for module development:

- All plugins should target Python 3.6 as the minimum supported version
- Read the [Ansible module conventions](https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_best_practices.html)
- Use the pre-existing `doc_fragments` and `module_utils` python modules where applicable. Feel free to use an existing plugin/module as a base
- Try to make the calls idempotent where possible.
- Modules should always support check mode

### Roles

Roles included in this collection mainly configure a host into a desired state, or perform a complex set of operations
not feasible with modules.
If you want to write a new role, look to the existing ones for inspiration.

Some general guidelines:

- Try to support most common Linux distributions (including Ubuntu, Debian, Fedora and Rockylinux)
    - You should test every supported distro in your `molecule.yml` see [here](#roles-2)
- Keep the configuration for the user simple and try to provide sensible defaults where possible
- Try to avoid using complex data structures as role variables/parameters, use simple values that can be composed easily instead.
- Make sure to document any role variables in both the `README.md` and in the `meta/argument_specs.yml` file.
  Te latter is used to generate role documentation programmatically.

## Testing Changes

We aim to test all of the components in this collection as thoroughly as possible.
We currently test all components using the following testing matrix:

- Ansible version: The three most recent major releases (such as 6,7,8), with a compatible host Python
- Node Python: The minimum supported Python version (see `tox.ini`)
- Proxmox version: The most recent stable version.
- For each entry in this matrix, we test all roles on all of their supported platforms, as well as all modules/plugins

To make testing all these permutations easier, we use `tox`to manage test scenarios.
If you set up the test environment as described in [the Getting Started guide](#getting-started), you should be able to run `tox -l` from the collection root:

This should print a list of test environments (scenarios) that you can run.
To run a specific environment, just use `tox -e {environment}`.
You can also use substitution syntax to run multiple environments at once:

```bash
# Will run the py3-ansible7-roles-pbs environment
tox -e py3-ansible7-roles-pbs

# Will run XXX-roles-pbs environment with ansible versions 6,7 and 8
# Note the single quotes around the string!
tox -e 'py3-ansible{6,7,8}-roles-pbs'
```

### Plugins (and Modules)

Modules (and plugins in general) are verified using `ansible-test`, specifically sanity, unit (TBD) and integration (TBD) tests, all run from tox, using docker-compose.
We use a special `ansible-test` container to initiate the various tests (sanity, unit, integration) from a docker-compose file so that we can easily add additional runtime dependencies such as extra containers.

You should always run the plugin tests after making changes to one (sanity, unit (TBD), integration (TBD)):

```bash
tox -e 'py3-ansible215-test-{sanity,#add other environments here}'
```

### Roles

We use the `tox-ansible` plugin (v1) to integrate molecule scenarios into tox.
You can run these scenarios using `tox -e`, just like for module tests.

Molecule itself runs the subject role against several containers to verify its functionality across target systems.
Since some roles involve the management of systemd services, we need a container runtime with good systemd support,
something which `docker` sadly doesn't offer on [modern linux distros](https://gist.github.com/pinkeen/bba0a6790fec96d6c8de84bd824ad933).

Instead, we use `podman`, a daemonless, rootless container runtime developed by RedHat to be (mostly) compatible to docker, but with better support for certain features such as systemd.
See below for setup instructions.
Once podman is installed and running, you can use `tox` to run the molecule scenarios.

#### Setting up Podman

1. Ensure that you have the following packages installed:
    - `podman` version 4+ (as it comes with the new netvark networking stack)
    - `aardvark-dns`, a plugin for netvark which provides DNS between containers in the same network
    - **NOTE:** If you previously used an older (`<=3.x`) version of `podman`, you will have to migrate to the new networking stack fist. This can be done with `podman system reset`
2. Ensure that your user has a subuid/subguid configuration associated with them so that you can run rootless containers
    - Check the `/etc/subuid` and `/etc/subgid` files for entries corresponding to your username.
    - If there is nothing, you can add them like so: `sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 <USERNAME>` (make sure that the range is not  already taken by another user in `/etc/subuid`/`/etc/subgid`).
3. Once you have applied your changes, run `podman system migrate` to force `podman` to pick up the new configuration.

That's it! Podman should now be working! To test it, you can run a container just like with docker: `podman run --rm -it ubuntu bash`

## Writing Tests

Any new new component or change to an existing one should be covered by tests to ensure that the code works, and that it keeps working into the future.
This section will help you in adding your own tests to this collection.

#### Plugins

Unit and integration tests are currently not used in this collection, though at least integration tests would be desireable.

#### Roles

There are tons of good guides online for how to write tests using molecule.
Alternatively, you can always look at the existing molecule scenarios in this collection

When creating a new molecule scenario, your directory structure should look like this:

```
some_role/
  defaults/
  meta/
  molecule/
    default/
      converge.yml
      molecule.yml
      prepare.yml
      requirements.txt # --> symlink to /tests/roles/requirements.txt
      verify.yml
    another-scenario/
      ...
  tasks
  ...
```

The `requirements.txt` symlink is used by `tox-ansible` when running tests via `tox` to install a specific, known-good version of `molecule` and the `molecule-podman` driver.
That way, all roles and scenarios in this collection can use the same version of `molecule`.

The [root molecule config](./.config/molecule/config.yml) contains the basic settings for molecule, such as driver setup.
In addition, your roles molecule scenario must define a set of platforms to test on, as well as any inventory configuration that you may need.
To get started you can copy the `molecule.yml` configuration from an existing role, then adjust it to suit your needs.

## Collection Docs

In addition to the `README.md`s, we use `antsibull-docs` to generate sphinx documentation for both plugins and roles (from the `meta/argument_specs.yml` file).
See [here](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections_documenting.html) for more information about the build process.

The CI also builds the docs to ensure they don't break silently.

## Maintainer information

### Updating Tested Versions

- Node Python: Bump the values in `tox.ini` (`consts` section)
- ansible-core (for plugins): Add the new core version to the following places in `tox.ini`:
    - The `envlist` in `tox.ini`
    - each `testenv:xxx` section header that deals with plugin tests
    - Set the correct environment variable in the main `testenv` section
- ansible (for roles): Change the version string in the `ansible` section in `tox.ini`

### Versioning and Releases

- This project uses sematic versioning.
  Version numbers and releases/changelogs are automatically generated using [release-drafter](https://github.com/release-drafter/release-drafter), utilizing pull request labels.
- When merging a pull request, make sure to select an appropriate label (pr-bugfix, pr-feature, etc.).
  Release-drafter will automatically update the draft release changelog and the galaxy.yml version will be bumped if needed.
- Once a draft release is actually published, collection packages will be added to the release and ansible-galaxy automatically.
- If you need to manually bump the collection version, run the `update-version` script and adjust the test versions if required.
