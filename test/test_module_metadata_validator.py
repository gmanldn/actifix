from actifix.modules.registry import validate_module_metadata


def test_validate_module_metadata_valid():
    metadata = {
        "name": "modules.example",
        "version": "1.2.3",
        "description": "Example module",
        "capabilities": {"gui": True},
        "data_access": {"state_dir": True},
        "network": {"external_requests": False},
        "permissions": ["logging"],
    }
    assert validate_module_metadata("example", metadata) == []


def test_validate_module_metadata_invalid():
    metadata = {
        "name": "",
        "version": "1.0",
        "description": "",
        "capabilities": [],
        "data_access": None,
        "network": "nope",
        "permissions": "logging",
    }
    errors = validate_module_metadata("example", metadata)
    assert "name_invalid" in errors
    assert "version_not_semver" in errors
    assert "description_invalid" in errors
    assert "capabilities_invalid" in errors
    assert "data_access_invalid" in errors
    assert "network_invalid" in errors
    assert "permissions_invalid" in errors
