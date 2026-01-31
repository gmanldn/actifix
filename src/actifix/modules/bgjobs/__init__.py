"""Background Jobs Example Module - demonstrates safe persistence patterns."""

from __future__ import annotations

import json
import queue
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Union, List, Dict, Any

from actifix.modules.base import ModuleBase
from actifix.raise_af import TicketPriority
from actifix.log_utils import atomic_write

if TYPE_CHECKING:
    from flask import Blueprint

MODULE_DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8120,
    "max_workers": 2,
    "job_timeout": 30,
}

ACCESS_RULE = "local-only"

MODULE_METADATA = {
    "name": "modules.bgjobs",
    "version": "0.1.0",
    "description": "Example module demonstrating safe background job processing with persistence.",
    "capabilities": {"gui": True, "health": True, "background_workers": True},
    "data_access": {"state_dir": True},
    "network": {"external_requests": False},
    "permissions": ["logging", "fs_read", "fs_write"],
}

MODULE_DEPENDENCIES = [
    "modules.base",
    "modules.config",
    "runtime.state",
    "infra.logging",
    "core.raise_af",
    "runtime.api",
]


@dataclass
class BackgroundJob:
    """Represents a background job with safe persistence."""
    job_id: str
    task_type: str
    payload: Dict[str, Any]
    status: str  # pending, running, completed, failed
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None


class BackgroundJobProcessor:
    """Thread-safe background job processor with persistence."""

    def __init__(self, helper: ModuleBase, max_workers: int = 2):
        self.helper = helper
        self.max_workers = max_workers
        self.job_queue: queue.Queue = queue.Queue()
        self.jobs: Dict[str, BackgroundJob] = {}
        self.workers: List[threading.Thread] = []
        self.shutdown_event = threading.Event()
        self.jobs_lock = threading.Lock()
        self._load_jobs()

    def _get_jobs_file(self) -> Path:
        """Get the jobs persistence file path."""
        paths = self.helper.get_paths()
        return paths.state_dir / "bgjobs_jobs.json"

    def _load_jobs(self) -> None:
        """Load jobs from persistence."""
        jobs_file = self._get_jobs_file()
        if not jobs_file.exists():
            return

        try:
            with open(jobs_file, "r") as f:
                data = json.load(f)
                with self.jobs_lock:
                    for job_data in data.get("jobs", []):
                        job = BackgroundJob(**job_data)
                        self.jobs[job.job_id] = job
                        # Requeue pending jobs
                        if job.status == "pending":
                            self.job_queue.put(job.job_id)
        except Exception as exc:
            self.helper.record_module_error(
                message=f"Failed to load jobs: {exc}",
                source="modules/bgjobs/__init__.py:_load_jobs",
                error_type=type(exc).__name__,
                priority=TicketPriority.P3,
            )

    def _save_jobs(self) -> None:
        """Save jobs to persistence atomically."""
        with self.jobs_lock:
            jobs_data = {"jobs": [asdict(job) for job in self.jobs.values()]}

        try:
            jobs_file = self._get_jobs_file()
            atomic_write(jobs_file, json.dumps(jobs_data, indent=2))
        except Exception as exc:
            self.helper.record_module_error(
                message=f"Failed to save jobs: {exc}",
                source="modules/bgjobs/__init__.py:_save_jobs",
                error_type=type(exc).__name__,
                priority=TicketPriority.P2,
            )

    def submit_job(self, task_type: str, payload: Dict[str, Any]) -> str:
        """Submit a new background job."""
        job_id = f"job-{int(time.time() * 1000)}"
        job = BackgroundJob(
            job_id=job_id,
            task_type=task_type,
            payload=payload,
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        with self.jobs_lock:
            self.jobs[job_id] = job

        self.job_queue.put(job_id)
        self._save_jobs()

        self.helper.record_module_info(
            f"Submitted job {job_id} of type {task_type}",
            extra={"job_id": job_id, "task_type": task_type},
        )

        return job_id

    def get_job(self, job_id: str) -> Optional[BackgroundJob]:
        """Get a job by ID."""
        with self.jobs_lock:
            return self.jobs.get(job_id)

    def list_jobs(self) -> List[BackgroundJob]:
        """List all jobs."""
        with self.jobs_lock:
            return list(self.jobs.values())

    def _process_job(self, job_id: str) -> None:
        """Process a single job (worker thread)."""
        with self.jobs_lock:
            job = self.jobs.get(job_id)
            if not job:
                return
            job.status = "running"
            job.started_at = datetime.now(timezone.utc).isoformat()

        self._save_jobs()

        try:
            # Simulate job processing based on task type
            if job.task_type == "sleep":
                duration = job.payload.get("duration", 1)
                time.sleep(min(duration, 10))  # Cap at 10s
                result = f"Slept for {duration}s"
            elif job.task_type == "compute":
                # Simulate computation
                count = sum(range(job.payload.get("count", 1000)))
                result = f"Computed sum: {count}"
            else:
                result = f"Processed {job.task_type}"

            with self.jobs_lock:
                job.status = "completed"
                job.result = result
                job.completed_at = datetime.now(timezone.utc).isoformat()

            self.helper.record_module_info(
                f"Completed job {job_id}",
                extra={"job_id": job_id, "result": result},
            )

        except Exception as exc:
            with self.jobs_lock:
                job.status = "failed"
                job.error = str(exc)
                job.completed_at = datetime.now(timezone.utc).isoformat()

            self.helper.record_module_error(
                message=f"Job {job_id} failed: {exc}",
                source="modules/bgjobs/__init__.py:_process_job",
                error_type=type(exc).__name__,
                priority=TicketPriority.P3,
            )

        finally:
            self._save_jobs()

    def _worker_loop(self) -> None:
        """Worker thread main loop."""
        while not self.shutdown_event.is_set():
            try:
                job_id = self.job_queue.get(timeout=1)
                self._process_job(job_id)
            except queue.Empty:
                continue
            except Exception as exc:
                self.helper.record_module_error(
                    message=f"Worker error: {exc}",
                    source="modules/bgjobs/__init__.py:_worker_loop",
                    error_type=type(exc).__name__,
                    priority=TicketPriority.P2,
                )

    def start_workers(self) -> None:
        """Start background worker threads."""
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"bgjobs-worker-{i}",
                daemon=True,
            )
            worker.start()
            self.workers.append(worker)

        self.helper.record_module_info(
            f"Started {self.max_workers} background workers",
            extra={"max_workers": self.max_workers},
        )

    def shutdown(self) -> None:
        """Shutdown workers gracefully."""
        self.shutdown_event.set()
        for worker in self.workers:
            worker.join(timeout=5)

    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics."""
        with self.jobs_lock:
            total = len(self.jobs)
            pending = sum(1 for j in self.jobs.values() if j.status == "pending")
            running = sum(1 for j in self.jobs.values() if j.status == "running")
            completed = sum(1 for j in self.jobs.values() if j.status == "completed")
            failed = sum(1 for j in self.jobs.values() if j.status == "failed")

        return {
            "total_jobs": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "workers": len(self.workers),
            "queue_size": self.job_queue.qsize(),
        }


# Global processor instance
_processor: Optional[BackgroundJobProcessor] = None


def _module_helper(project_root: Optional[Union[str, Path]] = None) -> ModuleBase:
    return ModuleBase(
        module_key="bgjobs",
        defaults=MODULE_DEFAULTS,
        metadata=MODULE_METADATA,
        project_root=project_root,
    )


def create_blueprint(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    url_prefix: Optional[str] = "/modules/bgjobs",
) -> "Blueprint":
    global _processor
    helper = _module_helper(project_root)

    try:
        from flask import Blueprint, jsonify, request

        resolved_host, resolved_port = helper.resolve_host_port(host, port)
        if url_prefix:
            blueprint = Blueprint("bgjobs", __name__, url_prefix=url_prefix)
        else:
            blueprint = Blueprint("bgjobs", __name__)

        # Initialize processor
        config = helper.module_defaults
        max_workers = int(config.get("max_workers", 2))
        _processor = BackgroundJobProcessor(helper, max_workers=max_workers)
        _processor.start_workers()

        @blueprint.route("/")
        @helper.error_boundary(source="modules/bgjobs/__init__.py:index")
        def index():
            return jsonify({
                "module": "bgjobs",
                "status": "ok",
                "description": "Background jobs example module",
                "endpoints": ["/health", "/jobs", "/jobs/submit", "/jobs/<job_id>"],
            })

        @blueprint.route("/health")
        def health():
            stats = _processor.get_stats() if _processor else {}
            return jsonify({
                "status": "ok",
                "module": "bgjobs",
                "stats": stats,
            })

        @blueprint.route("/jobs", methods=["GET"])
        @helper.error_boundary(source="modules/bgjobs/__init__.py:list_jobs")
        def list_jobs():
            if not _processor:
                return jsonify({"error": "Processor not initialized"}), 500
            jobs = _processor.list_jobs()
            return jsonify({
                "jobs": [asdict(job) for job in jobs],
                "count": len(jobs),
            })

        @blueprint.route("/jobs/submit", methods=["POST"])
        @helper.error_boundary(source="modules/bgjobs/__init__.py:submit_job")
        def submit_job():
            if not _processor:
                return jsonify({"error": "Processor not initialized"}), 500

            data = request.get_json() or {}
            task_type = data.get("task_type", "default")
            payload = data.get("payload", {})

            job_id = _processor.submit_job(task_type, payload)
            return jsonify({"job_id": job_id, "status": "submitted"}), 201

        @blueprint.route("/jobs/<job_id>", methods=["GET"])
        @helper.error_boundary(source="modules/bgjobs/__init__.py:get_job")
        def get_job(job_id: str):
            if not _processor:
                return jsonify({"error": "Processor not initialized"}), 500

            job = _processor.get_job(job_id)
            if not job:
                return jsonify({"error": "Job not found"}), 404

            return jsonify(asdict(job))

        helper.log_gui_init(resolved_host, resolved_port)
        return blueprint

    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to create bgjobs blueprint: {exc}",
            source="modules/bgjobs/__init__.py:create_blueprint",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def create_app(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> "Flask":
    try:
        from flask import Flask

        app = Flask(__name__)
        blueprint = create_blueprint(project_root=project_root, host=host, port=port, url_prefix=None)
        app.register_blueprint(blueprint)
        return app
    except Exception as exc:
        helper = _module_helper(project_root)
        helper.record_module_error(
            message=f"Failed to create bgjobs GUI app: {exc}",
            source="modules/bgjobs/__init__.py:create_app",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def run_gui(
    host: Optional[str] = None,
    port: Optional[int] = None,
    project_root: Optional[Union[str, Path]] = None,
    debug: bool = False,
) -> None:
    app = create_app(project_root=project_root, host=host, port=port)
    resolved_host = host or MODULE_DEFAULTS["host"]
    resolved_port = port or MODULE_DEFAULTS["port"]
    app.run(host=resolved_host, port=resolved_port, debug=debug)
