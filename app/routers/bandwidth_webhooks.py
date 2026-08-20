from __future__ import annotations

import hmac

from fastapi import APIRouter, HTTPException, Request, Response

from app.config import get_settings
from app.database import SessionLocal
from app.services.bandwidth_webhook_service import BandwidthWebhookService


router = APIRouter(prefix="/api/webhooks/bandwidth", tags=["Bandwidth Messaging Webhooks"])
settings = get_settings()


async def _messaging_callback(request: Request, webhook_secret: str) -> Response:
    configured = settings.bandwidth_messaging_webhook_secret.strip()
    if not configured:
        raise HTTPException(status_code=503, detail="Bandwidth Messaging webhook secret is not configured.")
    if not hmac.compare_digest(webhook_secret, configured):
        raise HTTPException(status_code=404, detail="Not found")
    try:
        payload = await request.json()
        with SessionLocal() as db:
            BandwidthWebhookService(db).process_batch(payload)
            db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(status_code=204)


@router.post("/messaging/inbound/{webhook_secret}", status_code=204)
async def messaging_inbound_callback(request: Request, webhook_secret: str) -> Response:
    return await _messaging_callback(request, webhook_secret)


@router.post("/messaging/outbound/{webhook_secret}", status_code=204)
async def messaging_outbound_callback(request: Request, webhook_secret: str) -> Response:
    return await _messaging_callback(request, webhook_secret)


@router.post("/messaging/{webhook_secret}", status_code=204)
async def messaging_combined_callback(request: Request, webhook_secret: str) -> Response:
    """Compatibility endpoint when an application only supports one callback URL."""
    return await _messaging_callback(request, webhook_secret)
