import logging

from hrb_common.observability.logger import get_logger
from hrb_common.observability.request_context import set_request_id


def test_get_logger_returns_named_logger():
    logger = get_logger("my_service")
    assert logger.name == "my_service"
    assert logger.level == logging.INFO


def test_get_logger_does_not_duplicate_handlers_on_repeat_calls():
    logger_first = get_logger("repeat_test")
    handler_count_first = len(logger_first.handlers)

    logger_second = get_logger("repeat_test")

    assert logger_second is logger_first
    assert len(logger_second.handlers) == handler_count_first


def test_get_logger_does_not_propagate_to_root():
    logger = get_logger("no_propagate_test")
    assert logger.propagate is False


def test_logger_stamps_request_id_when_set(capsys):
    set_request_id("req-abc-123")
    logger = get_logger("request_id_test_set")

    logger.info("hello")

    captured = capsys.readouterr()
    assert "[req-abc-123]" in captured.out


def test_logger_stamps_dash_when_request_id_unset(capsys):
    set_request_id(None)
    logger = get_logger("request_id_test_unset")

    logger.info("hello")

    captured = capsys.readouterr()
    assert "[-]" in captured.out
