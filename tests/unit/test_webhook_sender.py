import pytest
from unittest.mock import Mock

from src.application.services.webhooks import (
    PaymentWebhookSender,
    WebhookNonRetryableError,
    WebhookTransportError,
)


async def test_webhook_sender_retries_transient_errors(monkeypatch) -> None:
    sender = PaymentWebhookSender(
        timeout_seconds=2,
        max_attempts=3,
        base_delay_seconds=0,
        allow_private_networks=True,
    )
    post = Mock(side_effect=[WebhookTransportError("temporary"), None])
    monkeypatch.setattr(sender, "_post", post)

    await sender.send("http://example.test/webhook", {"status": "succeeded"})

    assert post.call_count == 2


async def test_webhook_sender_does_not_retry_non_retryable_error(monkeypatch) -> None:
    sender = PaymentWebhookSender(
        timeout_seconds=2,
        max_attempts=3,
        base_delay_seconds=0,
        allow_private_networks=True,
    )
    post = Mock(side_effect=WebhookNonRetryableError("bad request"))
    monkeypatch.setattr(sender, "_post", post)

    with pytest.raises(WebhookNonRetryableError):
        await sender.send("http://example.test/webhook", {"status": "failed"})

    assert post.call_count == 1


def test_private_webhook_targets_are_blocked(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.application.services.webhooks.socket.getaddrinfo",
        lambda *args, **kwargs: [(2, 1, 6, "", ("127.0.0.1", 80))],
    )
    sender = PaymentWebhookSender(timeout_seconds=2)

    with pytest.raises(WebhookNonRetryableError, match="private or reserved"):
        sender._validate_target("http://internal.example/webhook")
