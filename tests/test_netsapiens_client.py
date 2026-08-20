import httpx
import pytest

from app.providers.netsapiens.client import NetSapiensClient, NetSapiensError


def _configured_client():
    client = NetSapiensClient()
    client.settings.netsapiens_api_url = "https://digicloud.invalid/ns-api/v2"
    client.settings.netsapiens_token = "test-token"
    return client


def test_request_rejects_login_html_with_http_200(monkeypatch):
    request = httpx.Request("POST", "https://digicloud.invalid/ns-api/v2/test")
    response = httpx.Response(
        200,
        headers={"content-type": "text/html; charset=UTF-8"},
        text="<!doctype html><html><title>Login</title></html>",
        request=request,
    )
    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: response)

    with pytest.raises(NetSapiensError, match="HTML page"):
        _configured_client().request("POST", "/test", json={"value": "safe"})


def test_request_accepts_json_with_http_200(monkeypatch):
    request = httpx.Request("GET", "https://digicloud.invalid/ns-api/v2/test")
    response = httpx.Response(
        200,
        headers={"content-type": "application/json"},
        json={"data": {"ok": True}},
        request=request,
    )
    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: response)

    assert _configured_client().request("GET", "/test") == {"data": {"ok": True}}
