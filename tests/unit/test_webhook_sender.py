from unittest.mock import Mock

import pytest

from src.application.services.webhooks import (
    PaymentWebhookSender,
    WebhookNonRetryableError,
    WebhookTransportError,
)

pytestmark = pytest.mark.unit


def private_address_resolver(*args, **kwargs):
    return [(2, 1, 6, "", ("127.0.0.1", 80))]


async def test_webhook_sender_retries_transient_errors() -> None:
    http_client = Mock()
    http_client.post.side_effect = [WebhookTransportError("temporary"), None]
    sender = PaymentWebhookSender(
        timeout_seconds=2,
        max_attempts=3,
        base_delay_seconds=0,
        allow_private_networks=True,
        http_client=http_client,
    )

    await sender.send("http://example.test/webhook", {"status": "succeeded"})

    assert http_client.post.call_count == 2


async def test_webhook_sender_does_not_retry_non_retryable_error() -> None:
    http_client = Mock()
    http_client.post.side_effect = WebhookNonRetryableError("bad request")
    sender = PaymentWebhookSender(
        timeout_seconds=2,
        max_attempts=3,
        base_delay_seconds=0,
        allow_private_networks=True,
        http_client=http_client,
    )

    with pytest.raises(WebhookNonRetryableError):
        await sender.send("http://example.test/webhook", {"status": "failed"})

    assert http_client.post.call_count == 1


async def test_private_webhook_targets_are_blocked() -> None:
    sender = PaymentWebhookSender(
        timeout_seconds=2,
        resolve_host=private_address_resolver,
    )

    with pytest.raises(WebhookNonRetryableError, match="private or reserved"):
        await sender.send("http://internal.example/webhook", {"status": "failed"})
