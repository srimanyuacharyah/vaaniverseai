"""Optional RQ (Redis Queue) adapter for background jobs.

This module provides helper functions to enqueue jobs into Redis-backed RQ.
It's optional: if `rq` or `redis` are not installed, imports will raise and
the CLI will show instructions to install and configure Redis.
"""
from typing import Any, Dict

def _ensure_rq():
    try:
        import redis  # type: ignore
        import rq  # type: ignore
        return redis, rq
    except Exception as e:
        raise ImportError("RQ/Redis not available. Install 'redis' and 'rq' and run a Redis server.") from e


def enqueue(job_func_path: str, args: tuple = (), kwargs: Dict[str, Any] = None, queue_name: str = 'default') -> str:
    """Enqueue a job by import path to RQ and return job id.

    `job_func_path` should be a string like 'vaaniverse.job_worker.process_synth'.
    The worker must import the same function path to execute it.
    """
    redis, rq = _ensure_rq()
    conn = redis.Redis()  # default localhost:6379
    q = rq.Queue(queue_name, connection=conn)
    if kwargs is None:
        kwargs = {}
    job = q.enqueue_call(func=job_func_path, args=args, kwargs=kwargs)
    return job.id


def instructions() -> str:
    return (
        "To use RQ enqueueing, install Redis and Python packages:\n"
        "  1) Install Redis and start the server (platform-specific).\n"
        "  2) pip install rq redis\n"
        "  3) Start an RQ worker: rq worker\n"
        "Then use the CLI 'rq-submit-*' commands to enqueue jobs."
    )
