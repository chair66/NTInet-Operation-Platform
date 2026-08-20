from typing import Any


class BandwidthAPIError(RuntimeError):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        payload: Any = None,
        method: str | None = None,
        url: str | None = None,
        latency_ms: int | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload
        self.method = method
        self.url = url
        self.latency_ms = latency_ms

    @property
    def diagnostic(self) -> dict[str, Any]:
        return {
            "message": str(self),
            "status_code": self.status_code,
            "payload": self.payload,
            "method": self.method,
            "url": self.url,
            "latency_ms": self.latency_ms,
        }
