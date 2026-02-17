"""Simple helper to wait for Redis to become reachable.

Used by the worker container to avoid starting RQ before Redis is ready.
"""
import socket
import time
import os

def wait(host: str = 'redis', port: int = 6379, timeout: int = 60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=3):
                print(f"Connected to Redis at {host}:{port}")
                return True
        except Exception:
            print(f"Waiting for Redis at {host}:{port}...")
            time.sleep(1)
    raise RuntimeError(f"Timed out waiting for Redis at {host}:{port}")


if __name__ == '__main__':
    host = os.environ.get('VAANIVERSE_REDIS_HOST', 'redis')
    port = int(os.environ.get('VAANIVERSE_REDIS_PORT', '6379'))
    wait(host=host, port=port, timeout=int(os.environ.get('VAANIVERSE_WAIT_TIMEOUT', '60')))
