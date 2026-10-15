# Copyright: (c) 2026, Miad Abdi <miad.abdi@sharifmind.ir>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""End-to-end authentication tests against a disposable PBS container.

Skips (rather than fails) when Docker or the image registry is unavailable;
a PBS instance that starts but misbehaves fails the test.
"""

import os
import socket
import ssl
import sys
import time
from pathlib import Path

import pytest

docker = pytest.importorskip("docker", reason="docker SDK not available")
pytest.importorskip("proxmoxer", reason="proxmoxer required by the modules")
pytest.importorskip("requests", reason="requests required by the modules")

# Real PBS image, pinned by tag AND digest (multi-arch manifest list).
PBS_IMAGE = ("ayufan/proxmox-backup-server:v4.2.0-1@"
             "sha256:01f685a010025233b649417a317cc175b27920cd64f0429abfdc46a0d8d2e88a")
PBS_API_PORT = 8007

PLAYBOOK = Path(__file__).parent / "files" / "api_token_auth.yml"


def _wait_readable(host, port, timeout=180):
    """Poll the HTTPS endpoint until PBS answers, or fail with container logs."""
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=5):
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with ctx.wrap_socket(socket.create_connection((host, port), timeout=5)):
                    return
        except OSError as e:  # not up yet
            last_error = e
            time.sleep(2)
    pytest.fail(f"PBS did not become ready within {timeout}s: {last_error}")


@pytest.fixture()
def pbs_server_host():
    try:
        client = docker.from_env()
        client.ping()
    except Exception as e:  # pylint: disable=broad-except
        pytest.skip(f"Docker daemon not available: {e}")
    # per-run named volumes keep PBS state disposable between runs without
    # accumulating anonymous leftovers; removed in teardown
    vol_names = [f"ansible-collection-pbs-test-{part}-{os.getpid()}"
                 for part in ("etc", "log", "lib")]
    vol_binds = {
        vol_names[0]: {"bind": "/etc/proxmox-backup", "mode": "rw"},
        vol_names[1]: {"bind": "/var/log/proxmox-backup", "mode": "rw"},
        vol_names[2]: {"bind": "/var/lib/proxmox-backup", "mode": "rw"},
    }
    for name in vol_names:
        try:
            client.volumes.create(name)
        except Exception as e:  # pylint: disable=broad-except
            pytest.skip(f"Could not create test volumes: {e}")
    try:
        ct = client.containers.run(
            PBS_IMAGE,
            detach=True,
            remove=False,
            volumes=vol_binds,
            # /run tmpfs, no host mounts, no privileged mode (users/tokens/ACLs
            # need none of it)
            tmpfs={"/run": "rw,size=64m"},
            mem_limit="2g",
            ports={str(PBS_API_PORT): ("127.0.0.1", 0)},  # loopback only, random host port
        )
    except Exception as e:  # pylint: disable=broad-except
        pytest.skip(f"Could not start PBS image (registry unreachable?): {e}")

    try:
        ct.reload()
        host_port = int(ct.attrs["NetworkSettings"]["Ports"][f"{PBS_API_PORT}/tcp"][0]["HostPort"])
        _wait_readable("127.0.0.1", host_port)
        yield f"127.0.0.1:{host_port}"
    finally:
        logs = ct.logs(tail=100).decode("utf-8", "replace")
        for line in logs.splitlines():
            print(line)  # surface startup issues on failure
        ct.remove(force=True, v=True)  # container + its volumes
        for name in vol_names:
            try:
                client.volumes.get(name).remove(force=True)
            except docker.errors.NotFound:
                pass


def test_api_token_auth(collection_test_env, pbs_server_host):  # pylint: disable=redefined-outer-name
    env = {k: v for k, v in os.environ.items() if k != "PROXMOX_PASSWORD"}
    collection_test_env.run(
        ["ansible-playbook", str(PLAYBOOK),
         "-e", f"pbs_api_host={pbs_server_host}",
         "-e", f"ansible_python_interpreter={sys.executable}"],
        env=env,
    )
