# Contribution Guide

This document contains the information needed to contribute to this project.
In here you will find the basic steps for getting started, as well as an overview over our testing system.

Note that by contributing to this collection, you agree with the code of conduct you can find [here.](/CODE_OF_CONDUCT.md)

## Getting Started

Prerequisites:

- A recent version of Python supported by the current release of `ansible-core` (see [here](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#control-node-requirements))
- Docker (for running Tests)

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

Each role in this collection performs a complex task to bring a remote host into a desired state.
If you want to write a new role, look to the existing ones for inspiration.

Some general guidelines:

- Try to support most common Linux distributions (including Ubuntu, Debian, Fedora and Rockylinux)
    - You should test every supported distro in your `molecule.yml` see [here](#roles-2)
- Keep the configuration for the user simple and try to provide sensible defaults where possible
- Try to avoid using complex data structures as role variables/parameters, use simple values that can be composed easily instead.
- Make sure to document any role variables in both the `README.md` and in the `meta/argument_specs.yml` file.
  The latter is used to generate role documentation programmatically.

## Testing Changes

We aim to test every part of this collection as thoroughly as reasonable to ensure correct behavior.
We use `pytest` to run all of our tests, both for plugins and roles.
If you set up the test environment as described in [the Getting Started guide](#getting-started), you should be able to see all available tests:

`pytest --co`

You can run these tests using `pytest` and limit execution to specific test with `pytest -k 'test_pattern'` (or just use your editors testing plugin).
Please note that running the full test suite executes all molecule scenarios and may take **up to an hour** to complete.

### Testing different App Versions

When you run the collection tests using `ptytest`, they are executed with the current stable Ansible version in `requirements.txt`.
To ensure that this collection remains backwards-compatible, we also test against older versions of both ansible.
Our testing Matrix currently looks like this:

| Component | Module Tests | Role Tests | Versions |
|-----------|--------------|------------|----------|
| `ansible-core` | ✅ | ✅ | Three most recent releases (e.g. `2.13`, `2.14`, `2.15`) |
| Node Python Version | ✅ | ❌ | Collection-supported Python version (see [README](./README.md))

All possible permutations are automatically tested in CI.
You can change the tested versions locally by supplying additional arguments to `pytest`:

```
$ pytest --help
# truncated output
Custom options:
  --ansible-version=ANSIBLE_VERSION
                        Version of ansible to use for tests, in the format '2.xx'. Default: see requirements.txt
  --node-python-version=NODE_PYTHON_VERSION
                        Python version to test Ansible modules with, in the format '3.x'. Default: '3.6'
```

## Writing Tests

Any new new component or change to an existing one should be covered by tests to ensure that the code works, and that it keeps working into the future.
This section will help you in adding your own tests to this collection.

### Plugins

Plugin tests are currently not used in this collection, this section will be filled once the need for them arises.

### Roles

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
      verify.yml
    another-scenario/
      ...
  tasks
  ...
```

The [root molecule config](./.config/molecule/config.yml) contains the basic settings for molecule, such as driver setup.
In addition, your roles molecule scenario must define a set of platforms to test on, as well as any inventory configuration that you may need.
To get started you can copy the `molecule.yml` configuration from an existing role, then adjust it to suit your needs.

## Collection Docs

In addition to the `README.md`s, we use `antsibull-docs` to generate sphinx documentation for both plugins and roles (from the `meta/argument_specs.yml` file).
See [here](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections_documenting.html) for more information about the build process.

The CI also builds the docs to ensure they don't break silently.

## Maintainer information

### Updating Dependencies

While the *Ansible* collection itself doesn't have any dependencies outside of ansible itself, the tooling used to build and test the collection does.
We use [`pip-tools`](https://github.com/jazzband/pip-tools/) to lock these dependencies to a specific version for testing.
This prevents random CI failures because of [`requests` updates et. al.](https://github.com/docker/docker-py/pull/3257), but still gives us a simple `requirements.txt` that anyone can install.

The direct dependencies are stored in `requirements.in`, use `scripts/udate_requirements.sh` to generate a new `requirements.txt`.
Do **not** generate `requirements.txt` in another way or remove the header, else renovate [won't be able to resolve and update dependencies in CI!](https://docs.renovatebot.com/modules/manager/pip-compile/#assumption-of-header-with-a-command)

### Bumping supported ansible-core versions

1. Update the versions in the [CI config](./.circleci/config.yml)
2. Update the version in [`requirements.txt`](./requirements.txt)

### Bumping node python version

1. Update the version in [`tests/conftest.py`](./tests/conftest.py)
2. Update the version in the [CI config](./.circleci/config.yml)

### Versioning and Releases

- Releases are automatically drafted by `release-drafter`, with a changelog generated from PR labels
- When merging a pull request, make sure to select an appropriate label (pr-bugfix, pr-feature, etc.).
  Release-drafter will automatically update the draft release changelog and a PR will be opened with bumped collection versions.
- Once a draft release is actually published, collection packages will be published to the release and ansible-galaxy automatically.
- If you need to manually bump the collection version, run the `update-version` script
