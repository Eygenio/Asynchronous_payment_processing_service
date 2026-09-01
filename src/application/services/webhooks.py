import asyncio
import ipaddress
import json
import socket
from collections.abc import Callable
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt
from tenacity.wait import wait_exponential


class WebhookTransportError(RuntimeError):
    """A retryable webhook transport error."""


class WebhookNonRetryableError(RuntimeError):
    """A webhook failure that should not be retried by tenacity."""


class WebhookHttpClient(Protocol):
    def post(self, url: str, payload: dict[str, Any], timeout: int) -> None:
        pass


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


class UrllibWebhookHttpClient:
    def post(self, url: str, payload: dict[str, Any], timeout: int) -> None:
        request = Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            opener = build_opener(_NoRedirectHandler)
            with opener.open(request, timeout=timeout) as response:
                status_code = getattr(response, "status", response.getcode())
                self._raise_for_status(status_code)
        except WebhookNonRetryableError:
            raise
        except HTTPError as error:
            self._raise_for_status(error.code)
        except (URLError, TimeoutError, OSError) as error:
            raise WebhookTransportError(f"Webhook transport error: {error}") from error

    @staticmethod
    def _raise_for_status(status_code: int) -> None:
        if 400 <= status_code < 500 and status_code not in {408, 429}:
            raise WebhookNonRetryableError(f"Webhook returned HTTP {status_code}")
        if status_code >= 500:
            raise WebhookTransportError(f"Webhook returned HTTP {status_code}")


class PaymentWebhookSender:
    def __init__(
        self,
        timeout_seconds: int,
        max_attempts: int = 3,
        base_delay_seconds: int = 2,
        allow_private_networks: bool = False,
        http_client: WebhookHttpClient | None = None,
        resolve_host: Callable[..., Any] = socket.getaddrinfo,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds
        self.allow_private_networks = allow_private_networks
        self.http_client = http_client or UrllibWebhookHttpClient()
        self._resolve_host = resolve_host

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
                self._validate_target(target_url)
                await asyncio.to_thread(
                    self.http_client.post,
                    target_url,
                    payload,
                    self.timeout_seconds,
                )

    def _validate_target(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise WebhookNonRetryableError("Webhook URL must use http or https")
        if self.allow_private_networks:
            return

        addresses = {
            info[4][0]
            for info in self._resolve_host(
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
