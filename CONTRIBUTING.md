# Contribution Guide

Below you will find the information needed to contribute to this project.

Note that by contributing to this collection, you agree with the code of conduct you can find [here.](https://github.com/maxhoesel/ansible-collection-proxmox/blob/main/CODE_OF_CONDUCT.md)

## Requirements

To begin development on this collection, you need to have the following dependencies installed:

- Docker (for running `ansible-test`)
- Python **3.6** or higher (required for ansible>=5)

## Quick Start

1. Fork the repository and clone it to your local machine
2. Run `./scripts/setup.sh`. This will set up a virtualenv in `.venv` containing all the dev dependencies
3. **Every time you want to do work on this project, run `source .venv/bin/activate` to activate the venv**
4. You should now be able to run `tox -l` to see all available tests

## About commit messages and structure

Follow the guidelines below when committing your changes

- All commits **must** follow the [conventional-commits standard](https://www.conventionalcommits.org/en/v1.0.0/):
  `<type>(optional scope): <description>`
  - Valid scopes are all components of this collection, such as modules or roles
- Structure your changes so that they are separated into logical and independent commits whenever possible.
- The commit message should clearly state **what** your change does. The "why" and "how" belong into the commit body.

Some good examples:
- `fix(step_ca): don't install unneeded packages`
- `feat(step_ca_certificate): add support for RA flags`

Don't be afraid to rename/amend/rewrite your branch history to achieve these goals!
Take a look at the `git rebase -i` and `git commit --amend` commands if you are not sure how to do so.
As long as your make these changes on your feature branch, there is no harm in doing so.


## Hints for Development

For Modules:
- Make sure that you have read the [Ansible module conventions](https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_best_practices.html)
- Each module should typically wrap around one proxmox API call.
- Make sure to use the doc fragment and utils already present, specifically the connection fragments used for parameters like api_host/user/password.

## Testing Framework

We use the `ansible-test` suite to test modules. Calls to these are handled by `tox` and the [`tox-ansible` extension]( https://github.com/ansible-community/tox-ansible).
You can run all the required tests for this project with `./scripts/test.sh`. You can also open that file to view the individual test stages.

Note that you **can't** just run `tox`, as the `sanity` and `integration` environments need extra parameters passed to
`ansible-test`. Without these, they will fail. In addition, the `tox-ansible` plugin (which automatically generate scenario envs)
also adds a few unneeded environments to the list, such as `env`.

#### Creating new module tests

We currently only run sanity tests for our modules via `ansible-test`. Unit/Integration tests and molecule tests are TODO.

## Release Workflow

This project uses semantic versioning. Name versions accordingly.

To create a release, run the "Create Release" GitHub Action with the desired version number (e.g. "0.3.0").
This action will:

1. Bump the version number in `galaxy.yml`
2. Update the changelog
3. Commit the changes in a "Release" commit and push it
4. Create a GitHub release (which will also create a tag at that commit)
5. Build the collection and publish the new release on galaxy
