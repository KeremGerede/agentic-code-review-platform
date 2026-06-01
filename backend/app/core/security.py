import hmac
import hashlib
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def verify_github_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """
    Verify the X-Hub-Signature-256 header sent by GitHub.
    Returns True if valid, False otherwise.
    """
    if not signature_header:
        logger.warning("Missing X-Hub-Signature-256 header.")
        return False

    if not signature_header.startswith("sha256="):
        logger.warning("Signature header does not start with 'sha256='.")
        return False

    expected_sig = signature_header[len("sha256="):]

    mac = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    )
    computed_sig = mac.hexdigest()

    is_valid = hmac.compare_digest(computed_sig, expected_sig)
    if not is_valid:
        logger.warning("GitHub webhook signature mismatch.")
    return is_valid
