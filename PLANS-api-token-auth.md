# Plan: API token authentication for the maxhoesel.proxmox modules

## Problem

Every module in this collection authenticates with `api_user` + `api_password`
only (`plugins/module_utils/api_connection.py`). Proxmox VE and PBS both
support API-token authentication, which is the recommended non-interactive
credential: tokens are privilege-separated, independently revocable, and avoid
sending (or storing in Ansible vaults) the root password of the PVE/PBS host.

Real-world impact (our deployment): we manage a Proxmox Backup Server whose
`root@pam` password is *locked* by fleet hardening policy — password auth is
impossible by design, and the only config-plane credential is a
`root@pam!ansible` API token. Today that forces users to bypass this
collection and talk to the API directly (custom modules), because
`api_connection.init()` rejects anything without `api_password`.

## Goal

Add token auth as a first-class alternative in the shared connection helper:

```yaml
- name: Create a PBS user with a token
  maxhoesel.proxmox.pbs_user:
    api_host: pbs.example.com
    api_user: root@pam
    api_token_name: ansible
    api_token_secret: "{{ pbs_token_secret }}"
    userid: john@pbs
    state: present
```

## Design

### 1. `plugins/module_utils/api_connection.py`

Extend `api_connection_argspec`:

```python
api_connection_argspec = dict(
    api_host=dict(type="str", required=True),
    api_user=dict(type="str", required=True),
    api_password=dict(type="str", no_log=True),
    api_token_name=dict(type="str"),
    api_token_secret=dict(type="str", no_log=True),
    validate_certs=dict(type="bool", default=False)
)
```

`init()` auth resolution — exactly one method must be supplied:

1. `api_password` set (or `PROXMOX_PASSWORD` env, unchanged) → password auth
   (current behavior, byte-for-byte).
2. else `api_token_name` AND `api_token_secret` set → token auth:

```python
proxmox = proxmoxer.ProxmoxAPI(
    module.params["api_host"],
    user=module.params["api_user"],
    token_name=module.params["api_token_name"],
    token_value=module.params["api_token_secret"],
    verify_ssl=module.params["validate_certs"],
    service=service,
)
```

`token_name`/`token_value` are native kwargs of proxmoxer's https backend
(`ProxmoxHTTPApiTokenAuth`, proxmoxer >= 1.2 — already the collection's
declared floor), so no new dependency.

3. neither (or only one of the two token params) → fail with a message naming
   the three valid combinations. Replace the current password-only error.

`api_token_secret` is `no_log: true`. `api_token_name` is not sensitive
(it appears in ACLs and log lines as `user@realm!name`).

### 2. `plugins/doc_fragments/api_connection.py`

Document the two new options; note mutual exclusivity with `api_password`
and that `api_user` remains the token's *owner* (`root@pam` +
`api_token_name: ansible` = `root@pam!ansible`). All modules already
`extends_documentation_fragment: maxhoesel.proxmox.api_connection`, so docs
propagate without touching each module.

### 3. No module-file changes

Modules pass `**api_connection_argspec` into `argument_spec` and call
`init()`; both are shared. `pbs_user`, `pbs_token`, `pbs_acl`, `pbs_datastore`,
`pbs_directory`, and the PVE-side modules (`proxmox_ha`, ...) get token auth
for free. `required=True` stays ONLY on `api_host`/`api_user`.

One caveat to verify per module: none of them read `api_password` directly
outside `init()` (grep confirms: all go through the helper).

### 4. Tests

Tests are part of the deliverable, not an afterthought — the PR ships with
unit tests AND runnable integration tests, all runnable without a real
Proxmox host.

#### 4a. Unit tests (no docker, no network)

New file `tests/unit/plugins/module_utils/test_api_connection.py` following
ansible-core's unit-test conventions. `init()` is pure glue around
`proxmoxer.ProxmoxAPI`, so we monkeypatch `ProxmoxAPI` and assert the exact
kwargs passed for every parameter combination:

```python
import pytest
from ansible_collections.maxhoesel.proxmox.plugins.module_utils import api_connection

PARAMS_PASSWORD = dict(api_host="h", api_user="root@pam", api_password="pw",
                       api_token_name=None, api_token_secret=None, validate_certs=False)
PARAMS_TOKEN = dict(api_host="h", api_user="root@pam", api_password=None,
                    api_token_name="ansible", api_token_secret="secret",
                    validate_certs=False)


def _run_init(monkeypatch, params):
    calls = {}

    class FakeProxmoxAPI:
        def __init__(self, host, **kwargs):
            calls["host"] = host
            calls.update(kwargs)

    monkeypatch.setattr(api_connection.proxmoxer, "ProxmoxAPI", FakeProxmoxAPI)
    module = types.SimpleNamespace(params=params)          # minimal AnsibleModule stand-in
    api_connection.init(module, {}, "PBS")
    return calls


def test_password_auth_unchanged(monkeypatch):
    """Regression guard: password path must pass exactly the old kwargs."""
    calls = _run_init(monkeypatch, PARAMS_PASSWORD)
    assert calls == dict(host="h", user="root@pam", password="pw",
                         verify_ssl=False, service="PBS")


def test_token_auth_uses_token_kwargs(monkeypatch):
    calls = _run_init(monkeypatch, PARAMS_TOKEN)
    assert calls["token_name"] == "ansible"
    assert calls["token_value"] == "secret"
    assert "password" not in calls


def test_token_and_password_is_rejected(monkeypatch):
    with pytest.raises(AnsibleFailJson) as exc:
        _run_init(monkeypatch, {**PARAMS_PASSWORD, "api_token_name": "x",
                                "api_token_secret": "y"})
    assert "either" in str(exc.value)  # exclusivity message


def test_neither_credential_is_rejected(monkeypatch):
    with pytest.raises(AnsibleFailJson):
        _run_init(monkeypatch, {**PARAMS_TOKEN, "api_token_name": None,
                                "api_token_secret": None})


def test_half_supplied_token_is_rejected(monkeypatch):
    """name without secret (or vice versa) is a config error, not a fallback."""
    with pytest.raises(AnsibleFailJson):
        _run_init(monkeypatch, {**PARAMS_TOKEN, "api_token_secret": None})


def test_proxmox_password_env_fallback(monkeypatch):
    monkeypatch.setenv("PROXMOX_PASSWORD", "from-env")
    calls = _run_init(monkeypatch, {**PARAMS_PASSWORD, "api_password": None})
    assert calls.get("password") == "from-env"
```

(`AnsibleFailJson` handling: `init()` calls `module.fail_json`; the stand-in
module object raises a sentinel exception the test catches. Exact scaffolding
to match the collection's existing test utilities during implementation.)

#### 4b. Integration tests (docker, existing harness)

Extend the PBS integration tests in `tests/plugins/` (same docker-fixture
pattern the collection already uses for its caddy/pbs tests):

1. **Regression**: one existing password-auth PBS test must stay green.
2. **Token end-to-end**: with password auth, `pbs_user` + `pbs_token` create
   a `automation@pbs` user with token → subsequent `pbs_acl` / `pbs_user`
   calls switch to `api_token_name`/`api_token_secret` → assert they still
   reconcile (changed on first, ok/unchanged on second — idempotency).
3. **Error contracts**: both credentials supplied → module fails with the
   exclusivity message; neither → the "specify one" message.

#### 4c. Sanity

`ansible-test sanity --docker` (validate-modules, pylint) must stay clean —
the new argspec keys are plain `str`/`no_log` options, no exotic shapes.

#### 4d. Real-world check (report on the PR)

One run against our production PBS 4.2 (`root@pam!ansible` token, root
password locked): users/ACLs reconcile via token auth end-to-end. Results
posted to the PR.

### 5. Versioning / changelog

- Bump minor: token auth is additive. `version_added` for the two new module
  options: next minor release (follow the collection's existing
  changelog/changelog-fragment process if present; otherwise note it in the
  PR description).

## Scope guardrails

- No behavior change for existing password users — the password path's
  kwargs are pinned by a regression unit test.
- No new dependencies (proxmoxer >= 1.2 already provides token auth).
- Out of scope: token *management* via tokens is already covered by
  `pbs_token`; this change is connection auth only.
- Extends functionality only — no module signatures, defaults, or behaviors
  change; `api_host`/`api_user` remain the sole required params.

## Validation checklist

- [ ] `init()` unit tests for all 5 param combinations (password, token,
      both, neither, half-token) — green
- [ ] `PROXMOX_PASSWORD` env fallback still honored (unit test)
- [ ] docker integration: password regression + token end-to-end green
- [ ] error-contract integration tests (both/neither) fail with the
      authored messages
- [ ] sanity/validate-modules clean
- [ ] one real-world run against a PBS 4.2 host with `root@pam!ansible`
      (we will run this in our fleet and report back on the PR)
