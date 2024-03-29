from dataclasses import dataclass
import os
from pathlib import Path
import subprocess

from packaging import version
import pkg_resources
import pytest
from pytest_virtualenv import VirtualEnv
import yaml

NODE_PYTHON_DEFAULT_VERSION = "3.6"

with open("galaxy.yml", encoding="utf-8") as f:
    GALAXY_YML = yaml.safe_load(f)


class TestEnv():
    def __init__(self, virtualenv: VirtualEnv) -> None:
        self.virtualenv = virtualenv

    def run(self, *args, **kwargs):
        # Combine any passed in env with the virtualenv to ensure proper PATH
        if "env" in kwargs:
            kwargs["env"] = {**kwargs["env"], **self.virtualenv.env}
        self.virtualenv.run(*args, **kwargs)


def get_ansible_version():
    base_version = version.parse(pkg_resources.get_distribution("ansible-core").version)
    return f"{base_version.major}.{base_version.minor}"


def pytest_addoption(parser):
    parser.addoption("--ansible-version", action="store", default=get_ansible_version(),
                     help="Version of ansible to use for tests, in the format '2.xx'. Default: see requirements.txt")
    parser.addoption("--node-python-version", action="store", default=NODE_PYTHON_DEFAULT_VERSION,
                     help="Python version to test Ansible modules with, "
                     f"in the format '3.x'. Default: '{NODE_PYTHON_DEFAULT_VERSION}'")


@pytest.fixture(scope="session")
def collection_path(tmp_path_factory) -> Path:
    build_path: Path = tmp_path_factory.mktemp("build")
    collection_file = build_path / f"{GALAXY_YML['namespace']}-{GALAXY_YML['name']}-{GALAXY_YML['version']}.tar.gz"
    subprocess.run(
        ["ansible-galaxy", "collection", "build", "--output-path", build_path],
        check=True,
    )

    install_path: Path = tmp_path_factory.mktemp("collections")
    env = os.environ.copy()
    env["ANSIBLE_COLLECTIONS_PATH"] = install_path.resolve().as_posix()
    subprocess.run(
        ["ansible-galaxy", "collection", "install", collection_file],
        env=env, check=True,
    )
    return install_path


@dataclass
class TestVersions:
    ansible_version: str
    node_python_version: str

    @property
    def ansible_version_pip(self):
        major, minor = self.ansible_version.split(".")
        next_minor = int(minor) + 1
        return f"ansible-core>={self.ansible_version},<{major}.{next_minor}"


@pytest.fixture(scope="session")
def test_versions(request) -> TestVersions:
    return TestVersions(
        request.config.getoption("--ansible-version"),
        request.config.getoption("--node-python-version")
    )
