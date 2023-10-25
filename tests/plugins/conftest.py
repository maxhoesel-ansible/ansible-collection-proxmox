# pylint: disable=redefined-outer-name
from typing import Optional

import pytest

from tests.conftest import TestEnv, GALAXY_YML


class AnsibleTestEnv(TestEnv):
    # pylint: disable=redefined-outer-name
    def __init__(self, virtualenv, collection_path, test_versions) -> None:
        self.cwd = collection_path / "ansible_collections" / GALAXY_YML["namespace"] / GALAXY_YML["name"]
        super().__init__(virtualenv)

        self.run(["pip", "install", test_versions.ansible_version_pip])

    def run(self, *args, **kwargs):
        kwargs["cwd"] = self.cwd
        return super().run(*args, **kwargs)


ANSIBLE_TEST_ENV: Optional[AnsibleTestEnv] = None


@pytest.fixture()
# This fixture should be session-scoped, but cannot be since it requires the function-scoped virtualenv fixture
# Use memoization for now.
# pylint: disable=redefined-outer-name
def ansible_test_env(virtualenv, collection_path, test_versions) -> AnsibleTestEnv:
    global ANSIBLE_TEST_ENV  # pylint: disable=global-statement
    if ANSIBLE_TEST_ENV is not None:
        return ANSIBLE_TEST_ENV

    ANSIBLE_TEST_ENV = AnsibleTestEnv(virtualenv, collection_path, test_versions)
    return ANSIBLE_TEST_ENV
