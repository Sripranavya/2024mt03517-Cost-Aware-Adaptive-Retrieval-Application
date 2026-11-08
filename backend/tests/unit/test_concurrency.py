"""Unit tests for the per-user concurrency limiter."""

import pytest
from fastapi import HTTPException

from app.security.concurrency import user_slot


def test_allows_up_to_limit_then_rejects():
    held = [user_slot("u_limit", 2) for _ in range(2)]
    for cm in held:
        cm.__enter__()
    try:
        with pytest.raises(HTTPException) as exc:
            with user_slot("u_limit", 2):
                pass
        assert exc.value.status_code == 429
    finally:
        for cm in held:
            cm.__exit__(None, None, None)


def test_slot_is_released_after_use():
    for _ in range(3):
        with user_slot("u_release", 1):
            pass  # each acquire must be released so the next succeeds


def test_users_are_independent():
    with user_slot("u_a", 1):
        # A different user is unaffected by u_a holding its only slot.
        with user_slot("u_b", 1):
            pass
