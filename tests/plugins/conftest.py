# pylint: disable=redefined-outer-name
from dataclasses import dataclass
from typing import cast, Generator

import docker
from docker.models.containers import Container
from docker.models.networks import Network
from docker.errors import NotFound
import pytest

CADDY_NETWORK = "ansible-collection-caddy-test"
CADDY_CONTAINER_NAME = "ansible-collection-caddy-test-server"
CADDY_HOSTNAME = "caddy"


@pytest.fixture(scope="session")
def caddy_network() -> Generator[Network, None, None]:
    client = docker.from_env()
    try:
        net = client.networks.get(CADDY_NETWORK)
    except NotFound:
        net = client.networks.create(CADDY_NETWORK)
    net = cast(Network, net)
    yield net

    net.remove()


@dataclass
class CaddyContainerConfig:
    ct: Container
    ct_hostname: str
    ct_network: str
    caddy_url: str


@pytest.fixture(scope="session")
def remote_caddy_container(caddy_network) -> Generator[CaddyContainerConfig, None, None]:
    client = docker.from_env()
    try:
        # cleanup old container to ensure REMOTE_CA_HOSTNAME points to the right container
        ct = cast(Container, client.containers.get(CADDY_CONTAINER_NAME))
        ct.remove(force=True)
    except NotFound:
        pass

    ct = cast(Container, client.containers.run(
        "docker.io/library/caddy:2", detach=True, remove=True,
        name=CADDY_CONTAINER_NAME, hostname=CADDY_HOSTNAME,
        network=caddy_network.name,
        environment={
            "CADDY_ADMIN": "0.0.0.0:2019",
        },
    ))
    # Wait for Caddy to come online
    # pylint: disable=line-too-long
    rc = ct.exec_run(
        "sh -c 'for i in {1..10}; do wget -O /dev/null http://127.0.0.1:2019/config && exit 0 || sleep 1; done && exit 1'")[0]
    assert rc == 0

    yield CaddyContainerConfig(
        ct, ct_hostname=CADDY_HOSTNAME, ct_network=CADDY_NETWORK,
        caddy_url=f"http://{CADDY_HOSTNAME}:2019"
    )

    ct.remove(force=True)
