from actifix.testing import create_module_test_client


def test_testmanifest_health():
    client = create_module_test_client("testmanifest", url_prefix=None)
    response = client.get("/health")
    assert response.status_code == 200
