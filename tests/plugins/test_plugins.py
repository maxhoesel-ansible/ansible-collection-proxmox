# pylint: disable=redefined-outer-name

def test_plugins_sanity(collection_test_env, test_versions):
    collection_test_env.run([
        "ansible-test",
        "sanity", "--docker", "--color", "-v",
        "--python", test_versions.node_python_version,
        "--skip-test", "metaclass-boilerplate",
        "--skip-test", "future-import-boilerplate",
    ])
