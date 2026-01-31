"""Tests for background jobs example module."""

import json
import time
from actifix.testing import create_module_test_client


def test_bgjobs_health():
    """Test bgjobs health endpoint."""
    client = create_module_test_client("bgjobs", url_prefix=None)
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "ok"
    assert data["module"] == "bgjobs"
    assert "stats" in data


def test_bgjobs_index():
    """Test bgjobs index endpoint."""
    client = create_module_test_client("bgjobs", url_prefix=None)
    response = client.get("/")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["module"] == "bgjobs"
    assert "endpoints" in data


def test_bgjobs_submit_and_get_job():
    """Test job submission and retrieval."""
    client = create_module_test_client("bgjobs", url_prefix=None)

    # Submit a job
    response = client.post(
        "/jobs/submit",
        data=json.dumps({"task_type": "sleep", "payload": {"duration": 0.1}}),
        content_type="application/json",
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert "job_id" in data
    job_id = data["job_id"]

    # Get the job
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    job_data = json.loads(response.data)
    assert job_data["job_id"] == job_id
    assert job_data["task_type"] == "sleep"
    assert job_data["status"] in ["pending", "running", "completed"]


def test_bgjobs_list_jobs():
    """Test listing jobs."""
    client = create_module_test_client("bgjobs", url_prefix=None)

    # Submit a job
    client.post(
        "/jobs/submit",
        data=json.dumps({"task_type": "compute", "payload": {"count": 100}}),
        content_type="application/json",
    )

    # List jobs
    response = client.get("/jobs")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "jobs" in data
    assert "count" in data
    assert data["count"] > 0


def test_bgjobs_job_completion():
    """Test that jobs complete successfully."""
    client = create_module_test_client("bgjobs", url_prefix=None)

    # Submit a quick job
    response = client.post(
        "/jobs/submit",
        data=json.dumps({"task_type": "sleep", "payload": {"duration": 0.1}}),
        content_type="application/json",
    )
    job_id = json.loads(response.data)["job_id"]

    # Wait for completion
    max_wait = 5
    start = time.time()
    while time.time() - start < max_wait:
        response = client.get(f"/jobs/{job_id}")
        job_data = json.loads(response.data)
        if job_data["status"] == "completed":
            assert job_data["result"] is not None
            break
        time.sleep(0.2)
    else:
        # Job should have completed by now
        assert False, f"Job {job_id} did not complete within {max_wait}s"


def test_bgjobs_persistence():
    """Test that jobs persist across module reloads."""
    # First client - submit job
    client1 = create_module_test_client("bgjobs", url_prefix=None)
    response = client1.post(
        "/jobs/submit",
        data=json.dumps({"task_type": "compute", "payload": {"count": 50}}),
        content_type="application/json",
    )
    job_id = json.loads(response.data)["job_id"]

    # Second client - should see the job (loaded from persistence)
    client2 = create_module_test_client("bgjobs", url_prefix=None)
    response = client2.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    job_data = json.loads(response.data)
    assert job_data["job_id"] == job_id
