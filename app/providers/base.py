from __future__ import annotations

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx


logger = logging.getLogger("nop.providers")


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    slug: str
    name: str
    provider_type: str
    version: str = "1.0"
    environment: str = "production"
    capabilities: frozenset[str] = field(default_factory=frozenset)


class ProviderError(RuntimeError):
    """Base exception for provider operations."""


class ProviderConfigurationError(ProviderError):
    """Raised when required provider configuration is missing or invalid."""


class ProviderRequestError(ProviderError):
    """Raised when a provider request cannot be completed successfully."""


@dataclass(slots=True)
class ProviderHealth:
    slug: str
    name: str
    provider_type: str
    environment: str
    configured: bool
    status: str
    detail: str
    response_time_ms: int | None = None


class ProviderClient:
    """Shared asynchronous HTTP behavior for external provider integrations.

    Provider-specific clients supply authentication and endpoint methods while
    this class owns timeouts, retries, request identifiers, safe logging, and
    consistent error translation.
    """

    provider_slug = "provider"

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: int = 30,
        max_attempts: int = 3,
        backoff_seconds: float = 0.35,
        headers: dict[str, str] | None = None,
        auth: httpx.Auth | tuple[str, str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max(1, max_attempts)
        self.backoff_seconds = max(0.0, backoff_seconds)
        self.headers = headers or {}
        self.auth = auth

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        if not self.base_url:
            raise ProviderConfigurationError(
                f"{self.provider_slug} base URL is not configured."
            )
        if not path.strip():
            raise ProviderConfigurationError(
                f"{self.provider_slug} endpoint path is not configured."
            )

        normalized_path = path if path.startswith("/") else f"/{path}"
        correlation_id = str(uuid.uuid4())
        request_headers = {
            **self.headers,
            "X-NOP-Correlation-ID": correlation_id,
        }

        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            started = time.perf_counter()
            try:
                async with httpx.AsyncClient(
                    base_url=self.base_url,
                    timeout=self.timeout_seconds,
                    headers=request_headers,
                    auth=self.auth,
                ) as client:
                    response = await client.request(
                        method,
                        normalized_path,
                        params=params,
                        json=json,
                    )
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                logger.info(
                    "provider_request provider=%s method=%s path=%s status=%s "
                    "duration_ms=%s attempt=%s correlation_id=%s",
                    self.provider_slug,
                    method.upper(),
                    normalized_path,
                    response.status_code,
                    elapsed_ms,
                    attempt,
                    correlation_id,
                )

                if response.status_code in {408, 429, 500, 502, 503, 504}:
                    if attempt < self.max_attempts:
                        await asyncio.sleep(self.backoff_seconds * attempt)
                        continue

                if response.is_error:
                    detail = self._safe_error_detail(response)
                    request_id = response.headers.get("x-request-id", "")
                    suffix = f" Request ID: {request_id}." if request_id else ""
                    raise ProviderRequestError(
                        f"{self.provider_slug} returned HTTP "
                        f"{response.status_code}. {detail}{suffix}".strip()
                    )

                try:
                    return response.json()
                except ValueError as exc:
                    raise ProviderRequestError(
                        f"{self.provider_slug} returned invalid JSON."
                    ) from exc

            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    await asyncio.sleep(self.backoff_seconds * attempt)
                    continue
                raise ProviderRequestError(
                    f"{self.provider_slug} request timed out."
                ) from exc
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    await asyncio.sleep(self.backoff_seconds * attempt)
                    continue
                raise ProviderRequestError(
                    f"Unable to connect to {self.provider_slug}: {exc}"
                ) from exc

        raise ProviderRequestError(
            f"{self.provider_slug} request failed: {last_error or 'unknown error'}"
        )

    @staticmethod
    def _safe_error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
            if isinstance(payload, dict):
                return str(
                    payload.get("message")
                    or payload.get("detail")
                    or payload.get("error")
                    or "Request failed."
                )[:500]
        except ValueError:
            pass
        return response.text[:300].strip() or "Request failed."


class BaseProvider(ABC):
    """Contract implemented by every NOP external provider."""

    descriptor: ProviderDescriptor

    @abstractmethod
    def validate_configuration(self) -> tuple[bool, str]:
        """Return configuration state and a safe human-readable detail."""

    def supports(self, capability: str) -> bool:
        return capability in self.descriptor.capabilities

    async def check_health(self) -> ProviderHealth:
        valid, detail = self.validate_configuration()
        return ProviderHealth(
            slug=self.descriptor.slug,
            name=self.descriptor.name,
            provider_type=self.descriptor.provider_type,
            environment=self.descriptor.environment,
            configured=valid,
            status="configured" if valid else "not_configured",
            detail=detail,
        )

    def health(self) -> dict[str, Any]:
        valid, detail = self.validate_configuration()
        return {
            "slug": self.descriptor.slug,
            "name": self.descriptor.name,
            "type": self.descriptor.provider_type,
            "version": self.descriptor.version,
            "environment": self.descriptor.environment,
            "configured": valid,
            "detail": detail,
            "capabilities": sorted(self.descriptor.capabilities),
        }
