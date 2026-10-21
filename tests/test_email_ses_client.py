from unittest.mock import MagicMock, patch

from hrb_common.email.ses_client import send_email


def test_send_email_requires_sender():
    result = send_email(sender="", recipient_email="a@example.com", subject="Hi", body_text="body")
    assert result["sent"] is False
    assert "sender is required" in result["message"]


def test_send_email_sends_simple_message():
    fake_ses = MagicMock()

    with patch("boto3.client", return_value=fake_ses):
        result = send_email(sender="noreply@example.com", recipient_email="a@example.com", subject="Hi", body_text="body")

    assert result["sent"] is True
    fake_ses.send_email.assert_called_once()


def test_send_email_rejects_oversized_attachments():
    huge_attachment = [("big.bin", b"x" * (8 * 1024 * 1024))]
    result = send_email(sender="noreply@example.com", recipient_email="a@example.com", subject="Hi", body_text="body", attachments=huge_attachment)
    assert result["sent"] is False
    assert "over the" in result["message"]


def test_send_email_with_attachments_uses_raw_send():
    fake_ses = MagicMock()
    small_attachment = [("note.txt", b"hello")]

    with patch("boto3.client", return_value=fake_ses):
        result = send_email(sender="noreply@example.com", recipient_email="a@example.com", subject="Hi", body_text="body", attachments=small_attachment)

    assert result["sent"] is True
    fake_ses.send_raw_email.assert_called_once()
