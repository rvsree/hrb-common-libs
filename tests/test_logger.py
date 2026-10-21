import logging

from hrb_common.observability.logger import get_logger


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
