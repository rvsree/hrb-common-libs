import pytest

from hrb_common.observability.retry import with_retry


def test_with_retry_succeeds_without_retrying_on_first_try():
    call_count = {"n": 0}

    @with_retry(max_attempts=3, backoff_base_seconds=0.01)
    def flaky():
        call_count["n"] += 1
        return "ok"

    assert flaky() == "ok"
    assert call_count["n"] == 1


def test_with_retry_retries_up_to_max_attempts_then_raises():
    call_count = {"n": 0}

    @with_retry(max_attempts=3, backoff_base_seconds=0.01)
    def always_fails():
        call_count["n"] += 1
        raise ConnectionError("boom")

    with pytest.raises(ConnectionError):
        always_fails()

    assert call_count["n"] == 3


def test_with_retry_succeeds_after_a_transient_failure():
    call_count = {"n": 0}

    @with_retry(max_attempts=3, backoff_base_seconds=0.01)
    def fails_once_then_succeeds():
        call_count["n"] += 1
        if call_count["n"] < 2:
            raise ConnectionError("transient")
        return "recovered"

    assert fails_once_then_succeeds() == "recovered"
    assert call_count["n"] == 2
