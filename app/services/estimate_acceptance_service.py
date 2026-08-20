from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone

from itsdangerous import BadSignature, URLSafeSerializer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.catalog_models import Estimate, EstimateDelivery
from app.database.models import NotificationEvent


def _serializer() -> URLSafeSerializer:
    return URLSafeSerializer(get_settings().app_secret_key,salt="estimate-acceptance-v1")


def acceptance_token(estimate:Estimate,contact_id:int,option_ids:list[int]) -> str:
    return _serializer().dumps({"estimate_id":estimate.id,"contact_id":contact_id,"option_ids":sorted(set(option_ids))})


def decode_acceptance_token(token:str) -> dict:
    try: payload=_serializer().loads(token)
    except BadSignature as exc: raise ValueError("This estimate link is invalid.") from exc
    if not isinstance(payload,dict) or not isinstance(payload.get("estimate_id"),int): raise ValueError("This estimate link is invalid.")
    return payload


def signature_data(value:str) -> str:
    match=re.fullmatch(r"data:image/png;base64,([A-Za-z0-9+/=]+)",value or "")
    if not match: raise ValueError("Please sign the estimate before accepting it.")
    try: raw=base64.b64decode(match.group(1),validate=True)
    except ValueError as exc: raise ValueError("The signature could not be read.") from exc
    if len(raw)<100 or len(raw)>1_000_000 or not raw.startswith(b"\x89PNG\r\n\x1a\n"): raise ValueError("The signature image is invalid.")
    return value


@dataclass(slots=True)
class EstimateAcceptanceService:
    db:Session

    def resolve(self,token:str) -> tuple[Estimate,list]:
        payload=decode_acceptance_token(token); estimate=self.db.get(Estimate,payload["estimate_id"])
        if not estimate: raise ValueError("This estimate is no longer available.")
        if estimate.status in {"expired","declined"}: raise ValueError("This estimate is no longer available for acceptance. Please contact NTInet if you would like it reviewed or updated.")
        allowed={int(x) for x in payload.get("option_ids",[]) if str(x).isdigit()}
        options=[x for x in estimate.options if x.id in allowed]
        if not options: raise ValueError("No estimate options are available through this link.")
        if estimate.valid_until and estimate.valid_until<date.today() and estimate.status!="won": raise ValueError("This estimate has expired. Please contact NTInet for an updated proposal.")
        return estimate,options

    def accept(self,token:str,*,option_ids:list[int],signer_name:str,signer_email:str,signature:str,ip_address:str) -> Estimate:
        estimate,allowed_options=self.resolve(token)
        if estimate.status=="converted": raise ValueError("This estimate has already been converted to a job.")
        if estimate.status=="won": raise ValueError("This estimate has already been accepted.")
        allowed={x.id for x in allowed_options}; selected=sorted({int(x) for x in option_ids if int(x) in allowed})
        if not selected: raise ValueError("Select at least one option to accept.")
        name=" ".join(signer_name.split()); email=signer_email.strip().lower()
        if len(name)<2: raise ValueError("Enter the name of the person accepting the estimate.")
        if "@" not in email or len(email)>255: raise ValueError("Enter a valid signer email address.")
        estimate.status="won"; estimate.won_option_ids_json=json.dumps(selected); estimate.accepted_by_name=name
        estimate.accepted_by_email=email; estimate.accepted_signature_data=signature_data(signature)
        estimate.accepted_ip_address=(ip_address or "")[:64]; estimate.accepted_at=datetime.now(timezone.utc)
        recipients=set(self.db.scalars(select(EstimateDelivery.sent_by_user_id).where(
            EstimateDelivery.estimate_id==estimate.id,EstimateDelivery.sent_by_user_id.is_not(None))))
        for user_id in recipients:
            marker=f'"estimate_id": {estimate.id}'
            exists=self.db.scalar(select(NotificationEvent.id).where(NotificationEvent.event_type=="estimates.accepted",NotificationEvent.recipient_user_id==user_id,NotificationEvent.payload.contains(marker)))
            if not exists:
                self.db.add(NotificationEvent(event_type="estimates.accepted",subject=f"Estimate Won: {estimate.estimate_number}",payload=json.dumps({"estimate_id":estimate.id,"option_ids":selected,"signer":name}),recipient_user_id=user_id,organization_id=estimate.organization_id,channel="internal",status="pending",target_url=f"/estimates/{estimate.id}"))
        return estimate
