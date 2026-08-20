from __future__ import annotations

import html
from pathlib import Path

from app.config import get_settings


def signature_html(user) -> str:
    if not user:
        return ""
    settings=get_settings(); pieces=[]
    photo_filename=(getattr(user, "signature_photo_filename", "") or "").strip()
    if photo_filename:
        src=f"{settings.ticket_public_base_url.rstrip('/')}/user-signatures/{user.id}/photo"
        pieces.append(f'<img src="{html.escape(src)}" alt="{html.escape(user.full_name)}" width="96" style="display:block;max-width:96px;height:auto;margin:0 0 10px">')
    text=(getattr(user, "email_signature", "") or "").strip()
    if text:
        pieces.append(f'<div style="white-space:pre-line">{html.escape(text)}</div>')
    elif user.full_name:
        pieces.append(f'<div><strong>{html.escape(user.full_name)}</strong></div>')
    return ('<div style="margin-top:22px;padding-top:14px;border-top:1px solid #ddd;font-family:Arial,sans-serif">'
            +''.join(pieces)+'</div>') if pieces else ""


def append_signature(document:str,user) -> str:
    block=signature_html(user)
    if not block: return document
    lower=document.lower(); index=lower.rfind("</body>")
    return document[:index]+block+document[index:] if index>=0 else document+block


def signature_photo_path(user) -> Path:
    return Path(get_settings().user_signature_photo_dir)/(getattr(user, "signature_photo_filename", "") or "")
