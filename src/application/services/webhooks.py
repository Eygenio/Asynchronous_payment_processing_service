import asyncio
import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from src.config.settings import settings
from src.core.enums import DeliveryStatus
from src.rabbit.producer import publish_payment_to_dlq

logger = logging.getLogger(__name__)

class PaymentWebhookSender:
    def __init__(
        self,
        max_attempts: int = settings.webhook_max_attempts,
        base_delay_seconds: int = settings.webhook_base_delay_seconds,
        timeout_seconds: int = settings.webhook_timeout_seconds,
    ) -> None:
        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds
        self.timeout_seconds = timeout_seconds

    async def send(
        self,
        payment_id: UUID,
        target_url: str | None,
        payload: dict[str, Any],
    ) -> DeliveryStatus:
        if not target_url:
            logger.info("Webhook URL is empty, skipping payment: %s", payment_id)
            return DeliveryStatus.SKIPPED

        try:
            await self._send_with_retry(target_url, payload)
            return DeliveryStatus.DELIVERED
        except Exception as webhook_error:
            logger.exception("Webhook delivery failed for payment %s", payment_id)
            dlq_payload = {
                "payment_id": str(payment_id),
                "reason": f"webhook_failed: {webhook_error}",
                "payload": payload,
            }
            try:
                await publish_payment_to_dlq(dlq_payload, message_id=str(payment_id))
                return DeliveryStatus.DLQ_PUBLISHED
            except Exception:
                logger.exception("DLQ publish failed for payment %s", payment_id)
                return DeliveryStatus.DLQ_PUBLISH_FAILED

    async def _send_with_retry(self, url: str, payload: dict[str, Any]) -> None:
        for attempt in range(1, self.max_attempts + 1):
            try:
                await self._post(url, payload)
                return
            except RuntimeError as error:
                if attempt >= self.max_attempts:
                    raise
                delay = self.base_delay_seconds * (2 ** (attempt - 1))
                logger.warning(
                    "Webhook attempt %s/%s failed. Retrying in %0.2fs. Error: %s",
                    attempt, self.max_attempts, delay, error,
                )
                await asyncio.sleep(delay)

    async def _post(self, url: str, payload: dict[str, Any]) -> None:
        def _request() -> None:
            request = Request(
                url=url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=self.timeout_seconds) as response:
                if response.status >= 400:
                    raise RuntimeError(f"Status: {response.status}")

        try:
            await asyncio.to_thread(_request)
        except (HTTPError, URLError, RuntimeError) as error:
            raise RuntimeError(f"Webhook transport error: {error}") from error
