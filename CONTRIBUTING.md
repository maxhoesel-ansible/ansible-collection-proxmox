# Contribution Guide

Below you will find the information needed to contribute to this project.

Note that by contributing to this collection, you agree with the code of conduct you can find [here.](https://github.com/maxhoesel-ansible/ansible-collection-proxmox/blob/main/CODE_OF_CONDUCT.md)

## Requirements

To begin development on this collection, you need to have the following dependencies installed:

- Docker, accessible by your local user account
- Python 2.7 or 3.6+. CI tests run specifically against either 2.7 or 3.6, but to make things easier we just use whatever version is available locally

## Quick Start

1. Fork the repository and clone it to your local machine
2. Run `./scripts/setup.sh` to configure a local dev environment (virtualenv) with all required dependencies
3. Activate the virtualenv with `source .venv/bin/activate`
4. Make your changes and commit them to a new branch
5. Run the tests locally with `./scripts/test.sh`. This will run the full test suite that also runs in the CI
6. Once you're done, commit your changes (make sure that you are in the venv).
   Pre-commit will format your code and check for any obvious errors when you do so.

## Hints for Development

For Modules:
- Make sure that you have read the [Ansible module conventions](https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_best_practices.html)
- Make sure to use the doc fragment and utils already present when possible.
- If you need to troubleshoot inside the ansible-test container, add `--docker-terminate never` to the
  call inside the testing script. The container will then persist even on failure, and you can debug it

For Roles:
- None so far

In general:
- Don't be afraid to rewrite your local branch history to clean up your commit messages!
  You should familiarize yourself with `git rebase -i` if you haven't done so already.

## Testing Framework

We use `molecule` to test all roles and the `ansible-test` suite to test modules. Calls to these are handled by `tox` and the [`tox-ansible` extension]( https://github.com/ansible-community/tox-ansible).
You can run all the required tests for this project with `./scripts/test.sh`. You can also open that file to view the individual test stages.

Note that you **can't** just run `tox`, as the `sanity` and `integration` environments need extra parameters passed to
`ansible-test`. Without these, they will fail. In addition, the `tox-ansible` plugin (which automatically generate scenario envs)
also adds a few unneeded environments to the list, such as `env`.

#### Creating new module tests

We currently only run sanity tests for our modules via `ansible-test`.

## Information for maintainers

This project uses sematic versioning. Version numbers and  releases/changelogs are automatically generated using [release-drafter](https://github.com/release-drafter/release-drafter), utilizing pull request labels.

When merging a pull request, make sure to select an appropriate label (pr-bugfix, pr-feature, etc.).
release-drafter will automatically update the draft release changelog and the galaxy.yml version will be bumped if needed.

Once a draft release is published, collection packages will be added to the release and ansible-galaxy automatically.
