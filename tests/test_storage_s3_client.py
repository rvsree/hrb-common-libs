from unittest.mock import MagicMock, patch

from hrb_common.storage.s3_client import delete_object, generate_presigned_download_url, generate_presigned_upload_url


def test_generate_presigned_upload_url_returns_expected_shape():
    fake_s3 = MagicMock()
    fake_s3.generate_presigned_url.return_value = "https://s3.example.com/upload"

    with patch("boto3.client", return_value=fake_s3):
        result = generate_presigned_upload_url("my-bucket", "doc-1/file.pdf", "application/pdf")

    assert result["upload_url"] == "https://s3.example.com/upload"
    assert result["key"] == "doc-1/file.pdf"
    fake_s3.generate_presigned_url.assert_called_once()


def test_generate_presigned_download_url_returns_expected_shape():
    fake_s3 = MagicMock()
    fake_s3.generate_presigned_url.return_value = "https://s3.example.com/download"

    with patch("boto3.client", return_value=fake_s3):
        result = generate_presigned_download_url("my-bucket", "doc-1/file.pdf")

    assert result["download_url"] == "https://s3.example.com/download"


def test_delete_object_calls_s3_delete():
    fake_s3 = MagicMock()

    with patch("boto3.client", return_value=fake_s3):
        delete_object("my-bucket", "doc-1/file.pdf")

    fake_s3.delete_object.assert_called_once_with(Bucket="my-bucket", Key="doc-1/file.pdf")
