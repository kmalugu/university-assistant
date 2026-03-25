"""
Caching Module
Caches frequently accessed, slowly-changing data like course catalog,
timetables, fee rules, and campus policies to reduce tool-calling overhead.
"""
import time
import hashlib
import logging
from typing import Any, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class TTLCache:
    """
    Simple in-memory TTL (Time-To-Live) cache.
    Suitable for data that rarely changes (courses, fees, policies).
    """

    def __init__(self):
        self._store: dict = {}

    def _make_key(self, namespace: str, *args, **kwargs) -> str:
        raw = f"{namespace}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            value, expiry = self._store[key]
            if expiry is None or time.time() < expiry:
                logger.debug(f"Cache HIT for key: {key[:16]}...")
                return value
            else:
                del self._store[key]
                logger.debug(f"Cache EXPIRED for key: {key[:16]}...")
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        expiry = time.time() + ttl_seconds if ttl_seconds else None
        self._store[key] = (value, expiry)
        logger.debug(f"Cache SET for key: {key[:16]}... (TTL={ttl_seconds}s)")

    def delete(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()
        logger.info("Cache cleared.")

    def stats(self) -> dict:
        now = time.time()
        active = sum(1 for _, (_, exp) in self._store.items() if exp is None or exp > now)
        return {"total_keys": len(self._store), "active_keys": active}


# ── Global cache instance ────────────────────────────────────────────────────
_cache = TTLCache()

# TTL constants (seconds)
TTL_COURSE_CATALOG = 86400        # 24 hours — courses rarely change
TTL_TIMETABLE = 86400             # 24 hours
TTL_FEE_RULES = 86400 * 7        # 1 week — fees change per semester
TTL_CAMPUS_POLICY = 86400 * 30   # 30 days — policies are very stable
TTL_CALENDAR = 3600               # 1 hour — upcoming deadlines need freshness
TTL_FACULTY = 86400               # 24 hours
TTL_LLM_RESPONSE = 300            # 5 minutes — for identical repeated queries


def cached(namespace: str, ttl: int = 3600):
    """
    Decorator that caches the return value of a function.

    Usage:
        @cached("course_lookup", ttl=TTL_COURSE_CATALOG)
        def get_course_by_code(code): ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = _cache._make_key(namespace, *args, **kwargs)
            result = _cache.get(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            if result is not None:
                _cache.set(key, result, ttl_seconds=ttl)
            return result
        return wrapper
    return decorator


# ── Cache-aware wrappers for tools ───────────────────────────────────────────

def cache_course_lookup(course_code: str):
    from backend.tools.course_lookup import get_course_by_code
    key = _cache._make_key("course", course_code.upper())
    result = _cache.get(key)
    if result is None:
        result = get_course_by_code(course_code)
        if result:
            _cache.set(key, result, ttl_seconds=TTL_COURSE_CATALOG)
    return result


def cache_timetable(program: str, year: int):
    from backend.tools.timetable import get_timetable
    key = _cache._make_key("timetable", program, year)
    result = _cache.get(key)
    if result is None:
        result = get_timetable(program, year)
        _cache.set(key, result, ttl_seconds=TTL_TIMETABLE)
    return result


def cache_fee_breakdown(program: str, nationality: str, include_hostel: bool = True):
    from backend.tools.fees import get_fee_breakdown
    key = _cache._make_key("fees", program, nationality, include_hostel)
    result = _cache.get(key)
    if result is None:
        result = get_fee_breakdown(program, nationality, include_hostel)
        _cache.set(key, result, ttl_seconds=TTL_FEE_RULES)
    return result


def cache_faculty_by_department(department: str):
    from backend.tools.faculty import get_faculty_by_department
    key = _cache._make_key("faculty_dept", department)
    result = _cache.get(key)
    if result is None:
        result = get_faculty_by_department(department)
        _cache.set(key, result, ttl_seconds=TTL_FACULTY)
    return result


def cache_llm_response(prompt_hash: str, response: str):
    """Cache an LLM response for an identical prompt."""
    _cache.set(f"llm:{prompt_hash}", response, ttl_seconds=TTL_LLM_RESPONSE)


def get_cached_llm_response(prompt: str) -> Optional[str]:
    """Check if an identical prompt has a cached response."""
    key = hashlib.md5(prompt.encode()).hexdigest()
    return _cache.get(f"llm:{key}")


def get_cache_stats() -> dict:
    return _cache.stats()


def invalidate_cache(namespace: str = None):
    """Invalidate cache (full or by namespace prefix)."""
    if namespace is None:
        _cache.clear()
    else:
        keys_to_delete = [k for k in _cache._store if k.startswith(namespace)]
        for k in keys_to_delete:
            _cache.delete(k)
        logger.info(f"Invalidated {len(keys_to_delete)} cache entries for namespace '{namespace}'.")
