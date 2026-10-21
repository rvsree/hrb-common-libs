"""Sends email via AWS SES - ported from hrb_chatbot_v2's email_client/ses_client.py.
Only change: `sender` is a parameter, not read from SES_SENDER_EMAIL directly - this
extra shouldn't assume one fixed sending identity across every consuming service."""

import mimetypes
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3
from botocore.exceptions import ClientError

from hrb_common.observability.call_logger import log_backend_call
from hrb_common.observability.logger import get_logger

logger = get_logger("ses_client")

DEFAULT_REGION = "us-east-1"
MAX_TOTAL_ATTACHMENT_BYTES = 7 * 1024 * 1024


def _build_raw_message(sender, recipient_email, subject, body_text, attachments, html_body=None, cc_addresses=None) -> bytes:
    message = MIMEMultipart("mixed")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient_email
    if cc_addresses:
        message["Cc"] = ", ".join(cc_addresses)
    message.attach(MIMEText(html_body, "html") if html_body else MIMEText(body_text, "plain"))

    for filename, content in attachments:
        content_type, _ = mimetypes.guess_type(filename)
        maintype, _, subtype = (content_type or "application/octet-stream").partition("/")
        part = MIMEApplication(content, _subtype=subtype or "octet-stream")
        part.add_header("Content-Disposition", "attachment", filename=filename)
        message.attach(part)

    return message.as_bytes()


def send_email(
    sender: str,
    recipient_email: str,
    subject: str,
    body_text: str,
    attachments: list[tuple[str, bytes]] | None = None,
    html_body: str | None = None,
    cc_addresses: list[str] | None = None,
    region: str = DEFAULT_REGION,
) -> dict:
    """Returns {"sent": bool, "message": str} - never raises."""
    if not sender:
        return {"sent": False, "message": "sender is required."}

    if attachments:
        total_bytes = sum(len(content) for _, content in attachments)
        if total_bytes > MAX_TOTAL_ATTACHMENT_BYTES:
            return {"sent": False, "message": f"Attachments are {total_bytes} bytes total, over the {MAX_TOTAL_ATTACHMENT_BYTES}-byte limit."}

    ses_client = boto3.client("ses", region_name=region)

    try:
        with log_backend_call(logger, "ses", "send_email", recipient=recipient_email):
            if attachments:
                raw_message = _build_raw_message(sender, recipient_email, subject, body_text, attachments, html_body, cc_addresses)
                ses_client.send_raw_email(Source=sender, Destinations=[recipient_email, *(cc_addresses or [])], RawMessage={"Data": raw_message})
            else:
                body = {"Text": {"Data": body_text}}
                if html_body:
                    body["Html"] = {"Data": html_body}
                destination = {"ToAddresses": [recipient_email]}
                if cc_addresses:
                    destination["CcAddresses"] = cc_addresses
                ses_client.send_email(Source=sender, Destination=destination, Message={"Subject": {"Data": subject}, "Body": body})
    except ClientError as error:
        logger.warning("SES send to %s failed: %s", recipient_email, error)
        return {"sent": False, "message": str(error)}

    return {"sent": True, "message": f"Email sent to {recipient_email}."}
