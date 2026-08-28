import asyncio
import ipaddress
import json
import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt
from tenacity.wait import wait_exponential


class WebhookTransportError(RuntimeError):
    """A retryable webhook transport error."""


class WebhookNonRetryableError(RuntimeError):
    """A webhook failure that should not be retried by tenacity."""


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


class PaymentWebhookSender:
    def __init__(
        self,
        timeout_seconds: int,
        max_attempts: int = 3,
        base_delay_seconds: int = 2,
        allow_private_networks: bool = False,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds
        self.allow_private_networks = allow_private_networks

    async def send(self, target_url: str, payload: dict[str, Any]) -> None:
        retrying = AsyncRetrying(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(
                multiplier=self.base_delay_seconds,
                min=self.base_delay_seconds,
                max=30,
            ),
            retry=retry_if_exception_type(WebhookTransportError),
            reraise=True,
        )

        async for attempt in retrying:
            with attempt:
                await asyncio.to_thread(self._post, target_url, payload)

    def _post(self, url: str, payload: dict[str, Any]) -> None:
        self._validate_target(url)
        request = Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            opener = build_opener(_NoRedirectHandler)
            with opener.open(request, timeout=self.timeout_seconds) as response:
                status_code = getattr(response, "status", response.getcode())
                if 400 <= status_code < 500 and status_code not in {408, 429}:
                    raise WebhookNonRetryableError(
                        f"Webhook returned HTTP {status_code}",
                    )
                if status_code >= 500:
                    raise WebhookTransportError(
                        f"Webhook returned HTTP {status_code}",
                    )
        except WebhookNonRetryableError:
            raise
        except HTTPError as error:
            if 400 <= error.code < 500 and error.code not in {408, 429}:
                raise WebhookNonRetryableError(
                    f"Webhook returned HTTP {error.code}",
                ) from error
            raise WebhookTransportError(
                f"Webhook returned HTTP {error.code}",
            ) from error
        except (URLError, TimeoutError, OSError) as error:
            raise WebhookTransportError(
                f"Webhook transport error: {error}",
            ) from error

    def _validate_target(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise WebhookNonRetryableError("Webhook URL must use http or https")
        if self.allow_private_networks:
            return

        addresses = {
            info[4][0]
            for info in socket.getaddrinfo(
                parsed.hostname,
                parsed.port or 443,
                type=socket.SOCK_STREAM,
            )
        }
        for address in addresses:
            ip = ipaddress.ip_address(address)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
            ):
                raise WebhookNonRetryableError(
                    "Webhook target resolves to a private or reserved network",
                )
