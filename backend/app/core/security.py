import hmac
import hashlib
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def verify_github_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """
    Verify the X-Hub-Signature-256 header sent by GitHub.

    If DEBUG_SKIP_WEBHOOK_SIGNATURE_CHECK=true in .env the check is bypassed
    and a loud warning is printed. Never set this in production.
    """
    if settings.DEBUG_SKIP_WEBHOOK_SIGNATURE_CHECK:
        logger.warning(
            "⚠️  DEBUG_SKIP_WEBHOOK_SIGNATURE_CHECK=true — "
            "signature verification is DISABLED. Do not use in production."
        )
        return True

    if not signature_header:
        logger.warning("Webhook rejected: missing X-Hub-Signature-256 header.")
        return False

    if not signature_header.startswith("sha256="):
        logger.warning(
            "Webhook rejected: signature header does not start with 'sha256='. "
            "Got: %s", signature_header[:20]
        )
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
        logger.warning(
            "Webhook rejected: signature mismatch. "
            "Expected prefix: %s... Got prefix: %s...",
            computed_sig[:10], expected_sig[:10],
        )
    return is_valid
