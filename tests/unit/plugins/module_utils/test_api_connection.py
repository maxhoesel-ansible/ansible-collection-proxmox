# Copyright: (c) 2026, Miad Abdi <miad.abdi@sharifmind.ir>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import sys
import types
from pathlib import Path

import pytest
import yaml

# Pylint runs from the repo root without the collection on sys.path; pytest
# inserts the rootdir for us at runtime. Make the layout importable for both.
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from plugins.doc_fragments.api_connection import ModuleDocFragment  # noqa: E402
from plugins.module_utils import api_connection  # noqa: E402

PARAMS_BASE = dict(
    api_host="h",
    api_user="root@pam",
    api_password=None,
    api_token_name=None,
    api_token_secret=None,
    api_auth_method=None,
    validate_certs=False,
)
PARAMS_PASSWORD = {**PARAMS_BASE, "api_password": "pw"}
PARAMS_TOKEN = {**PARAMS_BASE, "api_token_name": "ansible", "api_token_secret": "secret"}

PASSWORD_KWARGS = dict(user="root@pam", password="pw", verify_ssl=False, service="PBS")
TOKEN_KWARGS = dict(user="root@pam", token_name="ansible", token_value="secret",
                    verify_ssl=False, service="PBS")


class FailJsonSentinel(Exception):
    def __init__(self, result):
        self.result = result
        super().__init__(result.get("msg", ""))


class FakeAnsibleModule:
    def __init__(self, params):
        self.params = params
        self.check_mode = False

    def fail_json(self, **kwargs):
        raise FailJsonSentinel(kwargs)


@pytest.fixture(autouse=True)
def _no_proxmox_password(monkeypatch):
    monkeypatch.delenv("PROXMOX_PASSWORD", raising=False)


@pytest.fixture(autouse=True)
def _fake_proxmoxer(monkeypatch):
    calls = {}

    class FakeProxmoxAPI:
        def __init__(self, host, **kwargs):
            calls["host"] = host
            calls.update(kwargs)

    monkeypatch.setattr(api_connection, "HAS_PROXMOXER", True)
    monkeypatch.setattr(api_connection, "proxmoxer",
                        types.SimpleNamespace(ProxmoxAPI=FakeProxmoxAPI), raising=False)
    return calls


def _run_init(params, service="PBS"):
    module = FakeAnsibleModule(dict(params))
    return api_connection.init(module, {}, service), module


def test_password_auth_unchanged(_fake_proxmoxer):
    """Regression guard: password path must pass exactly the old kwargs."""
    _run_init(PARAMS_PASSWORD)
    assert _fake_proxmoxer == dict(host="h", **PASSWORD_KWARGS)


def test_token_auth_uses_token_kwargs(_fake_proxmoxer):
    calls = _fake_proxmoxer
    _run_init(PARAMS_TOKEN)
    assert _fake_proxmoxer == dict(host="h", **TOKEN_KWARGS)
    assert "password" not in calls


def test_token_and_password_is_rejected():
    with pytest.raises(FailJsonSentinel) as exc:
        _run_init({**PARAMS_PASSWORD, "api_token_name": "x",
                   "api_token_secret": "y"})
    assert "ambiguous credentials" in str(exc.value)


def test_neither_credential_is_rejected():
    with pytest.raises(FailJsonSentinel):
        _run_init(PARAMS_BASE)


def test_half_supplied_token_is_rejected():
    """name without secret (or vice versa) is a config error, not a fallback."""
    for params in ({**PARAMS_TOKEN, "api_token_secret": None},
                   {**PARAMS_TOKEN, "api_token_name": None}):
        with pytest.raises(FailJsonSentinel):
            _run_init(params)


def test_proxmox_password_env_fallback(monkeypatch, _fake_proxmoxer):
    monkeypatch.setenv("PROXMOX_PASSWORD", "from-env")
    module_params = dict(PARAMS_PASSWORD)
    _run_init({**module_params, "api_password": None})
    assert _fake_proxmoxer.get("password") == "from-env"


def test_token_and_env_password_without_selector_uses_token(monkeypatch, _fake_proxmoxer):
    """Explicit token beats ambient PROXMOX_PASSWORD when api_auth_method is unset."""
    monkeypatch.setenv("PROXMOX_PASSWORD", "from-env")
    _run_init(PARAMS_TOKEN)
    assert _fake_proxmoxer == dict(host="h", **TOKEN_KWARGS)


def test_explicit_password_and_token_without_selector_is_ambiguous():
    with pytest.raises(FailJsonSentinel) as exc:
        _run_init({**PARAMS_TOKEN, "api_password": "pw"})
    assert str(exc.value.result["msg"]) == (
        "ambiguous credentials: supply only one method or set api_auth_method")


def test_selector_token_uses_token_kwargs(_fake_proxmoxer):
    _run_init({**PARAMS_TOKEN, "api_auth_method": "token"})
    assert _fake_proxmoxer == dict(host="h", **TOKEN_KWARGS)


def test_selector_token_with_password_is_rejected():
    with pytest.raises(FailJsonSentinel) as exc:
        _run_init({**PARAMS_TOKEN, "api_password": "pw", "api_auth_method": "token"})
    assert str(exc.value.result["msg"]) == (
        "api_auth_method: token cannot be combined with password credentials")


def test_selector_token_with_env_password_is_rejected(monkeypatch):
    monkeypatch.setenv("PROXMOX_PASSWORD", "from-env")
    with pytest.raises(FailJsonSentinel) as exc:
        _run_init({**PARAMS_TOKEN, "api_auth_method": "token"})
    assert str(exc.value.result["msg"]) == (
        "api_auth_method: token cannot be combined with password credentials")


def test_selector_password_with_token_is_rejected():
    for params in ({**PARAMS_PASSWORD, "api_token_name": "x", "api_auth_method": "password"},
                   {**PARAMS_BASE, "api_token_secret": "y", "api_auth_method": "password"}):
        with pytest.raises(FailJsonSentinel) as exc:
            _run_init(params)
        assert str(exc.value.result["msg"]) == (
            "api_auth_method: password cannot be combined with token credentials")


def test_selector_password_uses_password_kwargs(_fake_proxmoxer):
    _run_init({**PARAMS_PASSWORD, "api_auth_method": "password"})
    assert _fake_proxmoxer == dict(host="h", **PASSWORD_KWARGS)


def test_selector_password_env_fallback(monkeypatch, _fake_proxmoxer):
    monkeypatch.setenv("PROXMOX_PASSWORD", "from-env")
    _run_init({**PARAMS_BASE, "api_auth_method": "password"})
    assert _fake_proxmoxer.get("password") == "from-env"


@pytest.mark.parametrize("params", [
    {**PARAMS_BASE, "api_auth_method": "token"},
    {**PARAMS_TOKEN, "api_token_secret": None, "api_auth_method": "token"},
    {**PARAMS_BASE, "api_auth_method": "password"},
    {**PARAMS_TOKEN, "api_token_name": None, "api_password": "pw"},
    {**PARAMS_TOKEN, "api_token_secret": None},
])
def test_missing_or_partial_credentials_fail_without_connection(_fake_proxmoxer, params):
    with pytest.raises(FailJsonSentinel):
        _run_init(params)
    assert _fake_proxmoxer == {}


@pytest.mark.parametrize("service", ["PBS", "PVE"])
def test_token_kwargs_for_service(_fake_proxmoxer, service):
    _run_init(PARAMS_TOKEN, service=service)
    assert _fake_proxmoxer == dict(host="h", **{**TOKEN_KWARGS, "service": service})


def test_missing_proxmoxer_fails():
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(api_connection, "HAS_PROXMOXER", False)
    try:
        with pytest.raises(FailJsonSentinel):
            _run_init(PARAMS_PASSWORD)
    finally:
        monkeypatch.undo()


def test_connection_exception_is_wrapped(monkeypatch):
    class ExplodingProxmoxAPI:
        def __init__(self, host, **kwargs):
            raise ValueError("boom")

    monkeypatch.setattr(
        api_connection.proxmoxer, "ProxmoxAPI",
        ExplodingProxmoxAPI)
    with pytest.raises(FailJsonSentinel) as exc:
        _run_init(PARAMS_PASSWORD)
    assert "Could not connect to PBS host" in str(exc.value)


def test_env_password_is_assigned_to_module_params(monkeypatch):
    monkeypatch.setenv("PROXMOX_PASSWORD", "from-env")
    result_proxmox, module = _run_init({**PARAMS_BASE})
    assert result_proxmox is not None
    assert module.params["api_password"] == "from-env"


def test_argspec_and_docs():
    spec = api_connection.api_connection_argspec
    assert spec["api_token_name"] == dict(type="str")
    assert spec["api_token_secret"] == dict(type="str", no_log=True)
    assert spec["api_auth_method"] == dict(
        type="str", choices=["token", "password"], default=None)
    assert spec["api_password"] == dict(type="str", no_log=True)
    assert spec["api_host"]["required"] is True
    assert spec["api_user"]["required"] is True

    docs = yaml.safe_load(ModuleDocFragment.DOCUMENTATION)
    for name in ("api_token_name", "api_token_secret", "api_auth_method"):
        assert docs["options"][name]["version_added"] == "8.1.0"
    assert docs["options"]["api_token_secret"]["type"] == "str"
    assert docs["options"]["api_auth_method"]["choices"] == ["token", "password"]
