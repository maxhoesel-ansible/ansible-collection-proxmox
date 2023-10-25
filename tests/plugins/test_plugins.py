# pylint: disable=redefined-outer-name

def test_plugins_sanity(ansible_test_env, test_versions):
    ansible_test_env.run([
        "ansible-test",
        "sanity", "--docker", "--color", "-v",
        "--python", test_versions.node_python_version,
        "--skip-test", "metaclass-boilerplate",
        "--skip-test", "future-import-boilerplate",
    ])
