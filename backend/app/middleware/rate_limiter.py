"""
Rate limiter singleton — imported by route modules and main.py.

Uses slowapi (in-memory, per-process). Suitable for single-worker deployment.
If scaling to multiple workers, swap `storage_uri` to a Redis URL:
  Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
