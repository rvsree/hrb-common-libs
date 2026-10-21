import logging

import pytest

from hrb_common.observability.call_logger import log_backend_call


def test_log_backend_call_logs_success(caplog):
    logger = logging.getLogger("test_call_logger_success")
    logger.setLevel(logging.INFO)

    with caplog.at_level(logging.INFO, logger="test_call_logger_success"):
        with log_backend_call(logger, service="postgres", operation="select_rows"):
            pass

    assert any("select_rows" in record.message for record in caplog.records)
    assert any(record.status == "success" for record in caplog.records)


def test_log_backend_call_logs_and_reraises_on_failure(caplog):
    logger = logging.getLogger("test_call_logger_failure")
    logger.setLevel(logging.INFO)

    with caplog.at_level(logging.INFO, logger="test_call_logger_failure"):
        with pytest.raises(ValueError):
            with log_backend_call(logger, service="postgres", operation="select_rows"):
                raise ValueError("connection refused")

    assert any(record.status == "error" for record in caplog.records)
