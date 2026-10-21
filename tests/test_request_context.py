import pytest

from hrb_common.observability.request_context import _request_id_var, get_request_id, new_request_id, set_request_id


@pytest.fixture(autouse=True)
def reset_request_id():
    token = _request_id_var.set(None)
    yield
    _request_id_var.reset(token)


def test_get_request_id_is_none_when_unset():
    assert get_request_id() is None


def test_set_then_get_request_id_round_trips():
    set_request_id("abc-123")
    assert get_request_id() == "abc-123"


def test_new_request_id_generates_unique_values():
    first = new_request_id()
    second = new_request_id()
    assert first != second
    assert len(first) == 32  # uuid4().hex length
