from __future__ import annotations
from datetime import datetime, timezone
import smtplib, ssl
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from app.config import get_settings
from app.database import SessionLocal
from app.database.communication_models import CommunicationProfile
from app.database.models import Organization
from app.modules.registry import PlatformModule, module_registry, register_builtin_modules
from app.security import context_from_request, require_permission
from app.services import AuditService
from app.services.communication_profile_service import CommunicationProfileService
from app.services.bandwidth_messaging_client import BandwidthMessagingClient
from app.services.greengeeks_imap_service import GreenGeeksIMAPService
from app.web import render

router=APIRouter(prefix="/admin/communication-profiles",tags=["Communication Profiles"])
settings=get_settings()
def checked(v): return v in {"1","true","yes","on"}
def redirect(message=""): return RedirectResponse(f"/admin/communication-profiles?message={message.replace(' ','+')}" ,status_code=303)

def options(db, context):
    orgs=list(db.scalars(select(Organization).where(Organization.active.is_(True)).order_by(Organization.name))) if context.is_staff else [context.organization]
    register_builtin_modules()
    modules=(PlatformModule("estimates","Estimates","fa-file-invoice-dollar",permission="estimates.read",staff_only=True),*module_registry.enabled())
    return orgs,modules

@router.get("",response_class=HTMLResponse)
@router.get("/",response_class=HTMLResponse)
def profile_list(request:Request,message:str=""):
    require_permission(request,"communication_profiles.read"); context=context_from_request(request)
    with SessionLocal() as db:
        profiles=CommunicationProfileService(db,context).manageable(); db.expunge_all()
    return render(request,"communication_profiles/list.html",profiles=profiles,message=message)

@router.get("/new",response_class=HTMLResponse)
def profile_new(request:Request,channel:str="email",module_slug:str=""):
    require_permission(request,"communication_profiles.manage"); context=context_from_request(request)
    with SessionLocal() as db: orgs,modules=options(db,context); db.expunge_all()
    valid_module_slugs={module.slug for module in modules}
    default_module_slug=module_slug if module_slug in valid_module_slugs else "support-tickets"
    return render(request,"communication_profiles/form.html",profile=None,channel=channel if channel in {"email","sms"} else "email",organizations=orgs,modules=modules,default_module_slug=default_module_slug)

def save_profile(request,profile_id,name,organization_id,channel,module_slug,from_name,sender_address,reply_to,
                 smtp_host,smtp_port,smtp_username,smtp_password,smtp_security,bandwidth_account_id,
                 bandwidth_username,bandwidth_password,bandwidth_application_id,bandwidth_campaign_id,
                 bandwidth_api_base,bandwidth_auth_mode,bandwidth_client_id,bandwidth_client_secret,
                 bandwidth_token_url,is_default,is_active,is_shareable,daily_limit,
                 inbound_email_enabled,imap_host,imap_port,imap_username,imap_password,imap_security,imap_folder):
    context=context_from_request(request)
    with SessionLocal() as db:
        service=CommunicationProfileService(db,context); profile=service.get_manageable(profile_id) if profile_id else None
        if profile_id and not profile: raise HTTPException(404,"Communication profile not found")
        profile=service.save(profile,organization_id=organization_id,channel=channel,name=name,module_slug=module_slug,
            from_name=from_name,sender_address=sender_address,reply_to=reply_to,smtp_host=smtp_host,smtp_port=smtp_port,
            smtp_username=smtp_username,smtp_password=smtp_password,smtp_security=smtp_security,
            bandwidth_account_id=bandwidth_account_id,bandwidth_username=bandwidth_username,
            bandwidth_password=bandwidth_password,bandwidth_application_id=bandwidth_application_id,
            bandwidth_campaign_id=bandwidth_campaign_id,bandwidth_api_base=bandwidth_api_base,
            bandwidth_auth_mode=bandwidth_auth_mode,bandwidth_client_id=bandwidth_client_id,
            bandwidth_client_secret=bandwidth_client_secret,bandwidth_token_url=bandwidth_token_url,
            inbound_email_enabled=checked(inbound_email_enabled),imap_host=imap_host,imap_port=imap_port,
            imap_username=imap_username,imap_password=imap_password,imap_security=imap_security,imap_folder=imap_folder,
            is_default=checked(is_default),is_active=checked(is_active),is_shareable=checked(is_shareable),
            daily_limit=daily_limit,actor_user_id=context.user_id)
        AuditService(db,request,context).record("communication_profiles.saved","communication_profile",profile.id,
            f"Saved {profile.channel.upper()} profile {profile.name}",module="support-tickets",organization_id=profile.organization_id)
        db.commit()
    return redirect("Communication profile saved.")

@router.post("")
def profile_create(request:Request,name:str=Form(...),organization_id:int=Form(...),channel:str=Form(...),module_slug:str=Form(""),from_name:str=Form(""),sender_address:str=Form(""),reply_to:str=Form(""),smtp_host:str=Form(""),smtp_port:int=Form(465),smtp_username:str=Form(""),smtp_password:str=Form(""),smtp_security:str=Form("ssl"),bandwidth_account_id:str=Form(""),bandwidth_username:str=Form(""),bandwidth_password:str=Form(""),bandwidth_application_id:str=Form(""),bandwidth_campaign_id:str=Form(""),bandwidth_api_base:str=Form("https://messaging.bandwidth.com/api/v2"),bandwidth_auth_mode:str=Form("oauth2_system"),bandwidth_client_id:str=Form(""),bandwidth_client_secret:str=Form(""),bandwidth_token_url:str=Form("https://api.bandwidth.com/api/v1/oauth2/token"),is_default:str|None=Form(None),is_active:str|None=Form(None),is_shareable:str|None=Form(None),daily_limit:int=Form(0),inbound_email_enabled:str|None=Form(None),imap_host:str=Form(""),imap_port:int=Form(993),imap_username:str=Form(""),imap_password:str=Form(""),imap_security:str=Form("ssl"),imap_folder:str=Form("INBOX")):
    require_permission(request,"communication_profiles.manage")
    return save_profile(request,None,name,organization_id,channel,module_slug,from_name,sender_address,reply_to,smtp_host,smtp_port,smtp_username,smtp_password,smtp_security,bandwidth_account_id,bandwidth_username,bandwidth_password,bandwidth_application_id,bandwidth_campaign_id,bandwidth_api_base,bandwidth_auth_mode,bandwidth_client_id,bandwidth_client_secret,bandwidth_token_url,is_default,is_active,is_shareable,daily_limit,inbound_email_enabled,imap_host,imap_port,imap_username,imap_password,imap_security,imap_folder)

@router.get("/{profile_id}/edit",response_class=HTMLResponse)
def profile_edit(request:Request,profile_id:int):
    require_permission(request,"communication_profiles.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        profile=CommunicationProfileService(db,context).get_manageable(profile_id)
        if not profile: raise HTTPException(404,"Communication profile not found")
        orgs,modules=options(db,context); channel=profile.channel; db.expunge_all()
    return render(request,"communication_profiles/form.html",profile=profile,channel=channel,organizations=orgs,modules=modules)

@router.post("/{profile_id}")
def profile_update(request:Request,profile_id:int,name:str=Form(...),organization_id:int=Form(...),channel:str=Form(...),module_slug:str=Form(""),from_name:str=Form(""),sender_address:str=Form(""),reply_to:str=Form(""),smtp_host:str=Form(""),smtp_port:int=Form(465),smtp_username:str=Form(""),smtp_password:str=Form(""),smtp_security:str=Form("ssl"),bandwidth_account_id:str=Form(""),bandwidth_username:str=Form(""),bandwidth_password:str=Form(""),bandwidth_application_id:str=Form(""),bandwidth_campaign_id:str=Form(""),bandwidth_api_base:str=Form("https://messaging.bandwidth.com/api/v2"),bandwidth_auth_mode:str=Form("oauth2_system"),bandwidth_client_id:str=Form(""),bandwidth_client_secret:str=Form(""),bandwidth_token_url:str=Form("https://api.bandwidth.com/api/v1/oauth2/token"),is_default:str|None=Form(None),is_active:str|None=Form(None),is_shareable:str|None=Form(None),daily_limit:int=Form(0),inbound_email_enabled:str|None=Form(None),imap_host:str=Form(""),imap_port:int=Form(993),imap_username:str=Form(""),imap_password:str=Form(""),imap_security:str=Form("ssl"),imap_folder:str=Form("INBOX")):
    require_permission(request,"communication_profiles.manage")
    return save_profile(request,profile_id,name,organization_id,channel,module_slug,from_name,sender_address,reply_to,smtp_host,smtp_port,smtp_username,smtp_password,smtp_security,bandwidth_account_id,bandwidth_username,bandwidth_password,bandwidth_application_id,bandwidth_campaign_id,bandwidth_api_base,bandwidth_auth_mode,bandwidth_client_id,bandwidth_client_secret,bandwidth_token_url,is_default,is_active,is_shareable,daily_limit,inbound_email_enabled,imap_host,imap_port,imap_username,imap_password,imap_security,imap_folder)

@router.post("/{profile_id}/test")
def profile_test(request:Request,profile_id:int):
    require_permission(request,"communication_profiles.test"); context=context_from_request(request)
    with SessionLocal() as db:
        service=CommunicationProfileService(db,context); profile=service.get_manageable(profile_id)
        if not profile: raise HTTPException(404,"Communication profile not found")
        ok=False; message=""
        try:
            if not profile.credential_configured: message="Required provider configuration is incomplete."
            elif profile.channel=="sms":
                message=BandwidthMessagingClient().test_auth(profile); ok=True
            elif settings.ticket_communication_test_mode:
                ok=profile.credential_configured
                message=("Safe test mode validation passed; no external message was sent." if ok
                         else "Required provider configuration is incomplete; no external message was sent.")
            else:
                context_ssl=ssl.create_default_context()
                server=smtplib.SMTP_SSL(profile.smtp_host,profile.smtp_port,timeout=20,context=context_ssl) if profile.smtp_security=="ssl" else smtplib.SMTP(profile.smtp_host,profile.smtp_port,timeout=20)
                if profile.smtp_security=="starttls": server.starttls(context=context_ssl)
                if profile.smtp_username: server.login(profile.smtp_username,service.password(profile))
                server.noop(); server.quit(); ok=True; message="SMTP connection and authentication succeeded."
            if ok and profile.channel == "email" and profile.inbound_email_enabled:
                message += " " + GreenGeeksIMAPService(db).test_connection(profile)
        except Exception as exc: message=str(exc)
        service.mark_test(profile,ok,message); AuditService(db,request,context).record("communication_profiles.tested","communication_profile",profile.id,message,module="support-tickets",organization_id=profile.organization_id); db.commit()
    return redirect(f"Profile test {'passed' if ok else 'failed'}: {message}")

@router.post("/{profile_id}/sync-inbound")
def profile_sync_inbound(request:Request,profile_id:int):
    require_permission(request,"communication_profiles.test"); context=context_from_request(request)
    with SessionLocal() as db:
        profile=CommunicationProfileService(db,context).get_manageable(profile_id)
        if not profile: raise HTTPException(404,"Communication profile not found")
        try:
            counts=GreenGeeksIMAPService(db).sync_profile(profile); db.commit()
            message="Inbound sync complete: " + ", ".join(f"{value} {key}" for key,value in counts.items())
        except Exception as exc:
            db.rollback(); message=f"Inbound sync failed: {exc}"
    return redirect(message)
