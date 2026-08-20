from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from uuid import uuid4
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from sqlalchemy import select

from app.database import SessionLocal
from app.config import get_settings
from app.database.catalog_models import CatalogItem, EstimateDelivery, EstimateDocument, EstimateEmailTemplate, StoredDocument
from app.database.customer_models import CustomerContact
from app.security import context_from_request, require_permission
from app.services import AuditService, CommunicationProfileService, CustomerCommunicationService, JobService
from app.services.catalog_service import CatalogService, ESTIMATE_STATUSES, ITEM_TYPES
from app.services.estimate_document_service import estimate_pdf, merge_template
from app.services.estimate_acceptance_service import EstimateAcceptanceService, acceptance_token, decode_acceptance_token
from app.web import render, templates


router=APIRouter(tags=["Catalog, Estimates, and Job Materials"])
TYPE_LABELS={value:value.title() for value in ITEM_TYPES}
STATUS_LABELS={value:value.title() for value in ESTIMATE_STATUSES}
settings=get_settings()


def checked(value:str|None) -> bool: return str(value or "").lower() in {"1","true","on","yes"}
def optional_int(value:str) -> int|None: return int(value) if value.strip() else None
def redirect(path:str,message:str="") -> RedirectResponse:
    separator="&" if "?" in path else "?"
    return RedirectResponse(path+(f"{separator}message={quote(message)}" if message else ""),status_code=303)
def parse_date(value:str) -> date|None:
    try: return date.fromisoformat(value) if value.strip() else None
    except ValueError as exc: raise HTTPException(400,"Enter a valid date.") from exc


@router.get("/catalog",response_class=HTMLResponse)
def catalog_list(request:Request,q:str="",item_type:str="",show_inactive:bool=False,message:str=""):
    require_permission(request,"catalog.read"); context=context_from_request(request)
    with SessionLocal() as db:
        items=CatalogService(db,context).catalog(query=q,item_type=item_type,active_only=not show_inactive); db.expunge_all()
    return render(request,"catalog/list.html",items=items,q=q,item_type=item_type,show_inactive=show_inactive,message=message,type_labels=TYPE_LABELS)


@router.get("/catalog/new",response_class=HTMLResponse)
def catalog_new(request:Request):
    require_permission(request,"catalog.manage"); context=context_from_request(request)
    with SessionLocal() as db: categories=CatalogService(db,context).categories(); db.expunge_all()
    return render(request,"catalog/form.html",item=None,categories=categories,type_labels=TYPE_LABELS)


@router.get("/catalog/{item_id}/edit",response_class=HTMLResponse)
def catalog_edit(request:Request,item_id:int):
    require_permission(request,"catalog.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        item=CatalogService(db,context).catalog_item(item_id)
        if not item: raise HTTPException(404,"Catalog item not found")
        categories=CatalogService(db,context).categories(active_only=False); db.expunge_all()
    return render(request,"catalog/form.html",item=item,categories=categories,type_labels=TYPE_LABELS)


@router.post("/catalog/save")
def catalog_save(request:Request,item_id:str=Form(""),item_type:str=Form(...),category_id:int=Form(...),name:str=Form(...),brand:str=Form(""),model_number:str=Form(""),ordering_note:str=Form(""),ordering_url:str=Form(""),description:str=Form(""),unit:str=Form("each"),unit_cost:str=Form("0"),unit_price:str=Form("0"),taxable:str|None=Form(None),active:str|None=Form(None)):
    require_permission(request,"catalog.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        service=CatalogService(db,context); item=service.catalog_item(int(item_id)) if item_id.strip() else None
        if item_id.strip() and not item: raise HTTPException(404,"Catalog item not found")
        try:
            item=service.save_catalog_item(item,item_type=item_type,category_id=category_id,name=name,brand=brand,model_number=model_number,ordering_note=ordering_note,ordering_url=ordering_url,description=description,unit=unit,unit_cost=unit_cost,unit_price=unit_price,taxable=checked(taxable),active=checked(active))
            AuditService(db,request,context).record("catalog.saved","catalog_item",item.id,f"Saved catalog item {item.sku}",module="field-service",organization_id=item.organization_id); db.commit()
        except (ValueError,PermissionError) as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect("/catalog","Catalog item saved.")


@router.get("/catalog/categories",response_class=HTMLResponse)
def category_list(request:Request,message:str=""):
    require_permission(request,"catalog.manage"); context=context_from_request(request)
    with SessionLocal() as db: categories=CatalogService(db,context).categories(active_only=False); db.expunge_all()
    return render(request,"catalog/categories.html",categories=categories,message=message)


@router.post("/catalog/categories")
def category_create(request:Request,name:str=Form(...),description:str=Form(""),parent_id:str=Form("")):
    require_permission(request,"catalog.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        try:
            category=CatalogService(db,context).save_category(None,name=name,description=description,active=True,parent_id=optional_int(parent_id))
            AuditService(db,request,context).record("catalog.category_created","catalog_category",category.id,f"Created category {category.name}",module="field-service",organization_id=category.organization_id); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect("/catalog/categories","Category added.")


@router.post("/catalog/categories/{category_id}")
def category_update(request:Request,category_id:int,name:str=Form(...),description:str=Form(""),parent_id:str=Form(""),active:str|None=Form(None)):
    require_permission(request,"catalog.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        service=CatalogService(db,context); category=service.category(category_id)
        if not category: raise HTTPException(404,"Catalog category not found")
        try:
            category=service.save_category(category,name=name,description=description,active=checked(active),parent_id=optional_int(parent_id))
            AuditService(db,request,context).record("catalog.category_updated","catalog_category",category.id,f"Updated category {category.name}",module="field-service",organization_id=category.organization_id); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect("/catalog/categories","Category updated.")


@router.get("/estimates",response_class=HTMLResponse)
def estimate_list(request:Request,q:str="",status:str="",message:str=""):
    require_permission(request,"estimates.read"); context=context_from_request(request)
    with SessionLocal() as db:
        estimates=CatalogService(db,context).estimates(status=status,query=q); db.expunge_all()
    return render(request,"estimates/list.html",estimates=estimates,q=q,status=status,message=message,status_labels=STATUS_LABELS)


@router.get("/estimates/new",response_class=HTMLResponse)
def estimate_new(request:Request,customer_id:int|None=None):
    require_permission(request,"estimates.create"); context=context_from_request(request)
    with SessionLocal() as db:
        customers=CatalogService(db,context).customers()
        for customer in customers: _=tuple(customer.contacts); _=tuple(customer.locations)
        db.expunge_all()
    return render(request,"estimates/form.html",customers=customers,selected_customer_id=customer_id)


@router.post("/estimates")
def estimate_create(request:Request,customer_id:int=Form(...),contact_id:str=Form(""),location_id:int=Form(...),title:str=Form(...),valid_until:str=Form(""),tax_rate:str=Form("0"),internal_notes:str=Form(""),customer_notes:str=Form("")):
    require_permission(request,"estimates.create"); context=context_from_request(request)
    with SessionLocal() as db:
        try:
            estimate=CatalogService(db,context).create_estimate(customer_id=customer_id,contact_id=optional_int(contact_id),location_id=location_id,title=title,valid_until=parse_date(valid_until),tax_rate=tax_rate,internal_notes=internal_notes,customer_notes=customer_notes)
            AuditService(db,request,context).record("estimates.created","estimate",estimate.id,f"Created {estimate.estimate_number}",module="field-service",organization_id=estimate.organization_id); db.commit(); estimate_id=estimate.id
        except (ValueError,PermissionError) as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect(f"/estimates/{estimate_id}","Estimate created. Add catalog items below.")


@router.get("/estimates/{estimate_id}",response_class=HTMLResponse)
def estimate_detail(request:Request,estimate_id:int,option_id:int|None=None,message:str=""):
    require_permission(request,"estimates.read"); context=context_from_request(request)
    with SessionLocal() as db:
        service=CatalogService(db,context); estimate=service.estimate(estimate_id)
        if not estimate: raise HTTPException(404,"Estimate not found")
        if not estimate.options: raise HTTPException(500,"Estimate option migration has not been applied.")
        active_option=next((x for x in estimate.options if x.id==option_id),estimate.options[0])
        catalog=service.catalog(); jobs=service.customer_jobs(estimate); _=tuple(active_option.lines); templates_list=service.email_templates(); stored_documents=service.stored_documents(); _=tuple(estimate.documents); _=tuple(estimate.deliveries)
        # SKU is retained in storage only for backward-compatible snapshots.
        for item in catalog: item.sku=""
        for line in active_option.lines:
            line.sku=""
            line.quantity=f"{line.quantity:.1f}" if line.item_type=="labor" else f"{line.quantity:.0f}"
        contacts=[contact for contact in estimate.customer.contacts if contact.active and contact.email]
        try: won_option_ids={int(x) for x in json.loads(estimate.won_option_ids_json or "[]")}
        except (TypeError,ValueError): won_option_ids=set()
        db.expunge_all()
        estimate.__dict__["lines"]=list(active_option.lines)
        for field in ("subtotal","discount_total","taxable_subtotal","tax_total","total","estimated_cost","gross_profit","margin_percent"): estimate.__dict__[field]=getattr(active_option,field)
    return render(request,"estimates/detail.html",estimate=estimate,active_option=active_option,catalog=catalog,jobs=jobs,contacts=contacts,email_templates=templates_list,stored_documents=stored_documents,message=message,status_labels=STATUS_LABELS,type_labels=TYPE_LABELS,won_option_ids=won_option_ids)


@router.post("/estimates/{estimate_id}/options")
def estimate_option_add(request:Request,estimate_id:int,name:str=Form(...)):
    require_permission(request,"estimates.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        service=CatalogService(db,context); estimate=service.estimate(estimate_id)
        if not estimate: raise HTTPException(404,"Estimate not found")
        try: option=service.add_option(estimate,name); db.commit(); oid=option.id
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect(f"/estimates/{estimate_id}?option_id={oid}","Option added.")


@router.post("/estimates/{estimate_id}/options/{option_id}")
def estimate_option_update(request:Request,estimate_id:int,option_id:int,name:str=Form(...),customer_notes:str=Form("")):
    require_permission(request,"estimates.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        service=CatalogService(db,context); estimate=service.estimate(estimate_id)
        if not estimate: raise HTTPException(404,"Estimate not found")
        try: service.update_option(estimate,option_id,name=name,customer_notes=customer_notes); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect(f"/estimates/{estimate_id}?option_id={option_id}","Option saved.")


@router.get("/estimates/{estimate_id}/print",response_class=HTMLResponse)
def estimate_print(request:Request,estimate_id:int,option_ids:str=""):
    require_permission(request,"estimates.read"); context=context_from_request(request)
    with SessionLocal() as db:
        estimate=CatalogService(db,context).estimate(estimate_id)
        if not estimate: raise HTTPException(404,"Estimate not found")
        selected={int(x) for x in option_ids.split(",") if x.isdigit()}; options=[x for x in estimate.options if not selected or x.id in selected]
        for option in options:
            _=tuple(option.lines)
            for line in option.lines: line.quantity=f"{line.quantity:.1f}" if line.item_type=="labor" else f"{line.quantity:.0f}"
        db.expunge_all()
    return render(request,"documents/estimate_options_print.html",estimate=estimate,options=options)


@router.get("/estimates/{estimate_id}/pdf")
def estimate_pdf_download(request:Request,estimate_id:int,option_ids:str=""):
    require_permission(request,"estimates.read"); context=context_from_request(request)
    with SessionLocal() as db:
        estimate=CatalogService(db,context).estimate(estimate_id)
        if not estimate: raise HTTPException(404,"Estimate not found")
        selected={int(x) for x in option_ids.split(",") if x.isdigit()}; options=[x for x in estimate.options if not selected or x.id in selected]
        data=estimate_pdf(estimate,options)
    return Response(data,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="{estimate.estimate_number}.pdf"'})


@router.get("/estimates/{estimate_id}/email",response_class=HTMLResponse)
def estimate_email_compose(request:Request,estimate_id:int):
    require_permission(request,"estimates.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        service=CatalogService(db,context); estimate=service.estimate(estimate_id)
        if not estimate: raise HTTPException(404,"Estimate not found")
        contacts=[x for x in estimate.customer.contacts if x.active and x.email]; email_templates=service.email_templates(); email_profiles=CommunicationProfileService(db,context).available(estimate.organization_id,"email"); _=tuple(estimate.documents); _=tuple(estimate.options); db.expunge_all()
    default=email_templates[0] if email_templates else None
    return render(request,"estimates/email_compose.html",estimate=estimate,contacts=contacts,email_templates=email_templates,default_template=default,email_profiles=email_profiles)


@router.post("/estimates/{estimate_id}/email")
def estimate_email(request:Request,estimate_id:int,contact_ids:list[int]=Form(...),option_ids:list[int]=Form(...),document_ids:list[int]=Form([]),subject:str=Form(...),message_body:str=Form(...),profile_id:str=Form(""),attach_pdf:str|None=Form(None)):
    require_permission(request,"estimates.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        service=CatalogService(db,context); estimate=service.estimate(estimate_id)
        if not estimate: raise HTTPException(404,"Estimate not found")
        selected_options=[x for x in estimate.options if x.id in set(option_ids)]
        if not selected_options: raise HTTPException(400,"Select at least one estimate option.")
        contacts=list(db.scalars(select(CustomerContact).where(CustomerContact.id.in_(contact_ids),CustomerContact.customer_id==estimate.customer_id,CustomerContact.active.is_(True))).unique())
        if len(contacts)!=len(set(contact_ids)): raise HTTPException(400,"One or more selected contacts are invalid.")
        attached={x.document_id:x.document for x in estimate.documents}; selected_docs=[attached[x] for x in document_ids if x in attached]
        base_attachments=[]
        if attach_pdf is not None: base_attachments.append((f"{estimate.estimate_number}.pdf",estimate_pdf(estimate,selected_options),"application/pdf"))
        for doc in selected_docs:
            path=Path(settings.document_storage_dir)/doc.stored_filename
            if path.is_file(): base_attachments.append((doc.original_filename,path.read_bytes(),doc.content_type))
        sent=failed=0
        for contact in contacts:
            tokens={"customer_name":estimate.customer.name,"contact_name":contact.full_name,"estimate_number":estimate.estimate_number,"estimate_title":estimate.title,"option_names":", ".join(x.name for x in selected_options),"estimate_total":", ".join(f"{x.name}: ${x.total:.2f}" for x in selected_options),"sender_name":context.user.full_name}
            final_subject=merge_template(subject,tokens); final_body=merge_template(message_body,tokens)
            token=acceptance_token(estimate,contact.id,[x.id for x in selected_options]); acceptance_url=f"{settings.ticket_public_base_url.rstrip('/')}/estimate/accept/{token}"
            html=templates.env.get_template("documents/estimate_options_email.html").render(estimate=estimate,options=selected_options,contact=contact,message_body=final_body,acceptance_url=acceptance_url)
            record=CustomerCommunicationService(db).send(estimate.customer,contact_id=contact.id,channel="email",subject=final_subject,body=final_body,profile_id=int(profile_id) if profile_id.strip() else None,ticket_id=None,consent_override=False,override_reason="",actor_user_id=context.user_id,module_slug="estimates",html_body=html,email_attachments=base_attachments,estimate_id=estimate.id)
            db.add(EstimateDelivery(estimate_id=estimate.id,contact_id=contact.id,recipient_email=contact.email,subject=final_subject,message_body=final_body,option_ids_json=json.dumps(option_ids),document_ids_json=json.dumps(document_ids),pdf_attached=attach_pdf is not None,acceptance_token=token,status=record.status,error_message=record.error_message,sent_by_user_id=context.user_id))
            if record.status=="sent": sent+=1
            else: failed+=1
        if sent and estimate.status=="draft": estimate.status="sent"
        AuditService(db,request,context).record("estimates.emailed","estimate",estimate.id,f"Estimate delivered to {sent} contact(s); {failed} failed",module="field-service",organization_id=estimate.organization_id); db.commit()
    message=f"Estimate emailed to {sent} contact(s)."+(f" {failed} delivery attempt(s) failed." if failed else "")
    return redirect(f"/estimates/{estimate_id}",message)


@router.post("/estimates/{estimate_id}/documents")
def estimate_document_attach(request:Request,estimate_id:int,document_id:int=Form(...)):
    require_permission(request,"estimates.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        service=CatalogService(db,context); estimate=service.estimate(estimate_id); document=db.get(StoredDocument,document_id)
        if not estimate or not document or document.organization_id!=estimate.organization_id or not document.active: raise HTTPException(404,"Estimate or document not found")
        if not db.scalar(select(EstimateDocument.id).where(EstimateDocument.estimate_id==estimate.id,EstimateDocument.document_id==document.id)): db.add(EstimateDocument(estimate_id=estimate.id,document_id=document.id,attached_by_user_id=context.user_id))
        db.commit()
    return redirect(f"/estimates/{estimate_id}","Document attached.")


@router.get("/documents",response_class=HTMLResponse)
def document_storage(request:Request,message:str=""):
    require_permission(request,"estimates.manage"); context=context_from_request(request)
    with SessionLocal() as db: documents=CatalogService(db,context).stored_documents(); db.expunge_all()
    return render(request,"documents/storage.html",documents=documents,message=message)


@router.post("/documents")
async def document_upload(request:Request,name:str=Form(...),description:str=Form(""),document:UploadFile=File(...)):
    require_permission(request,"estimates.manage"); context=context_from_request(request); original=Path(document.filename or "").name; suffix=Path(original).suffix.lower()
    if suffix not in {".pdf",".doc",".docx",".xls",".xlsx",".png",".jpg",".jpeg"}: raise HTTPException(400,"Unsupported document type.")
    content=await document.read(settings.ticket_attachment_max_bytes+1)
    if len(content)>settings.ticket_attachment_max_bytes: raise HTTPException(413,"Document exceeds the 10 MB limit.")
    directory=Path(settings.document_storage_dir); directory.mkdir(parents=True,exist_ok=True); stored=f"{uuid4().hex}{suffix}"; path=directory/stored; path.write_bytes(content)
    try:
        with SessionLocal() as db:
            org=CatalogService(db,context)._staff_org(); db.add(StoredDocument(organization_id=org.id,name=name.strip() or original,description=description.strip(),original_filename=original,stored_filename=stored,content_type=document.content_type or "application/octet-stream",size_bytes=len(content),uploaded_by_user_id=context.user_id)); db.commit()
    except Exception: path.unlink(missing_ok=True); raise
    return redirect("/documents","Document uploaded.")


@router.get("/documents/{document_id}")
def document_download(request:Request,document_id:int):
    require_permission(request,"estimates.read"); context=context_from_request(request)
    with SessionLocal() as db:
        document=db.get(StoredDocument,document_id); org=CatalogService(db,context)._staff_org()
        if not document or document.organization_id!=org.id: raise HTTPException(404,"Document not found")
        path=Path(settings.document_storage_dir)/document.stored_filename; filename=document.original_filename; media=document.content_type
    if not path.is_file(): raise HTTPException(404,"Stored file is missing")
    return FileResponse(path,media_type=media,filename=filename)


@router.get("/estimate-email-templates",response_class=HTMLResponse)
def estimate_template_list(request:Request,message:str=""):
    require_permission(request,"estimates.manage"); context=context_from_request(request)
    with SessionLocal() as db: items=CatalogService(db,context).email_templates(active_only=False); db.expunge_all()
    return render(request,"estimates/email_templates.html",items=items,message=message)


@router.post("/estimate-email-templates")
def estimate_template_add(request:Request,name:str=Form(...),subject_template:str=Form(...),body_template:str=Form(...)):
    require_permission(request,"estimates.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        org=CatalogService(db,context)._staff_org()
        if db.scalar(select(EstimateEmailTemplate.id).where(EstimateEmailTemplate.organization_id==org.id,EstimateEmailTemplate.name==name.strip())): raise HTTPException(400,"That template name already exists.")
        db.add(EstimateEmailTemplate(organization_id=org.id,name=name.strip(),subject_template=subject_template.strip(),body_template=body_template.strip(),active=True,created_by_user_id=context.user_id,updated_by_user_id=context.user_id)); db.commit()
    return redirect("/estimate-email-templates","Email template created.")


@router.post("/estimate-email-templates/{template_id}")
def estimate_template_update(request:Request,template_id:int,name:str=Form(...),subject_template:str=Form(...),body_template:str=Form(...),active:str|None=Form(None)):
    require_permission(request,"estimates.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        org=CatalogService(db,context)._staff_org(); item=db.scalar(select(EstimateEmailTemplate).where(EstimateEmailTemplate.id==template_id,EstimateEmailTemplate.organization_id==org.id))
        if not item: raise HTTPException(404,"Email template not found")
        item.name=name.strip(); item.subject_template=subject_template.strip(); item.body_template=body_template.strip(); item.active=checked(active); item.updated_by_user_id=context.user_id; db.commit()
    return redirect("/estimate-email-templates","Email template updated.")


@router.post("/estimates/{estimate_id}/update")
def estimate_update(request:Request,estimate_id:int,title:str=Form(...),valid_until:str=Form(""),tax_rate:str=Form("0"),internal_notes:str=Form(""),customer_notes:str=Form(""),status:str=Form("draft")):
    require_permission(request,"estimates.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        service=CatalogService(db,context); estimate=service.estimate(estimate_id)
        if not estimate: raise HTTPException(404,"Estimate not found")
        try: service.update_estimate(estimate,title=title,valid_until=parse_date(valid_until),tax_rate=tax_rate,internal_notes=internal_notes,customer_notes=customer_notes,status=status); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect(f"/estimates/{estimate_id}","Estimate updated.")


@router.post("/estimates/{estimate_id}/lines")
def estimate_add_line(request:Request,estimate_id:int,catalog_item_id:int=Form(...),option_id:int=Form(...),quantity:str=Form("1"),discount_percent:str=Form("0"),unit_price:str=Form("")):
    require_permission(request,"estimates.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        service=CatalogService(db,context); estimate=service.estimate(estimate_id)
        if not estimate: raise HTTPException(404,"Estimate not found")
        try: service.add_estimate_line(estimate,catalog_item_id=catalog_item_id,option_id=option_id,quantity=quantity,discount_percent=discount_percent,unit_price=unit_price); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect(f"/estimates/{estimate_id}?option_id={option_id}","Estimate item added.")


@router.post("/estimates/{estimate_id}/lines/{line_id}/delete")
def estimate_delete_line(request:Request,estimate_id:int,line_id:int):
    require_permission(request,"estimates.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        service=CatalogService(db,context); estimate=service.estimate(estimate_id)
        if not estimate: raise HTTPException(404,"Estimate not found")
        try: service.delete_estimate_line(estimate,line_id); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect(f"/estimates/{estimate_id}","Estimate item removed.")


@router.post("/estimates/{estimate_id}/copy-to-job")
def estimate_copy_to_job(request:Request,estimate_id:int,job_id:int=Form(...),option_id:int|None=Form(None)):
    require_permission(request,"estimates.manage"); context=context_from_request(request)
    with SessionLocal() as db:
        service=CatalogService(db,context); estimate=service.estimate(estimate_id); job=JobService(db,context).get(job_id)
        if not estimate or not job: raise HTTPException(404,"Estimate or job not found")
        try: count=service.copy_estimate_to_job(estimate,job,option_id=option_id); AuditService(db,request,context).record("estimates.converted","estimate",estimate.id,f"Copied {count} items to {job.job_number}",module="field-service",organization_id=estimate.organization_id); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect(f"/jobs/{job_id}",f"{count} estimate items copied to this job.")


@router.get("/estimate/accept/{token}",response_class=HTMLResponse)
def estimate_accept_page(request:Request,token:str,error:str="",success:str=""):
    try:
        with SessionLocal() as db:
            payload=decode_acceptance_token(token); estimate,options=EstimateAcceptanceService(db).resolve(token); _=tuple(options)
            recipient_contact=next((x for x in estimate.customer.contacts if x.id==payload.get("contact_id")),estimate.contact)
            for option in options: _=tuple(option.lines)
            db.expunge_all()
        return render(request,"estimates/public_accept.html",estimate=estimate,options=options,recipient_contact=recipient_contact,token=token,error=error,success=success,public_page=True)
    except ValueError as exc:
        return render(request,"estimates/public_accept.html",estimate=None,options=[],recipient_contact=None,token=token,error=str(exc),public_page=True,status_code=400)


@router.post("/estimate/accept/{token}")
def estimate_accept(request:Request,token:str,option_ids:list[int]=Form(...),signer_name:str=Form(...),signer_email:str=Form(...),signature_data_value:str=Form(...)):
    try:
        with SessionLocal() as db:
            service=EstimateAcceptanceService(db); estimate=service.accept(token,option_ids=option_ids,signer_name=signer_name,signer_email=signer_email,signature=signature_data_value,ip_address=request.client.host if request.client else ""); db.commit()
        return RedirectResponse(f"/estimate/accept/{token}?success={quote(estimate.estimate_number+' accepted successfully.')}",status_code=303)
    except ValueError as exc:
        return RedirectResponse(f"/estimate/accept/{token}?error={quote(str(exc))}",status_code=303)


@router.post("/jobs/{job_id}/materials")
def job_add_material(request:Request,job_id:int,catalog_item_id:int=Form(...),estimated_quantity:str=Form("0"),actual_quantity:str=Form("1")):
    context=context_from_request(request)
    if not (context.can("job_materials.manage") or context.can("jobs.manage")): raise HTTPException(403,"Job material permission required")
    with SessionLocal() as db:
        job=JobService(db,context).get(job_id)
        if not job: raise HTTPException(404,"Job not found or not assigned to you")
        try: CatalogService(db,context).add_job_line(job,catalog_item_id=catalog_item_id,estimated_quantity=estimated_quantity,actual_quantity=actual_quantity); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect(f"/jobs/{job_id}","Job item added.")


@router.post("/jobs/{job_id}/materials/{line_id}/update")
def job_update_material(request:Request,job_id:int,line_id:int,actual_quantity:str=Form(...),actual_unit_cost:str=Form("0"),unit_price:str=Form("0"),discount_percent:str=Form("0"),billable:str|None=Form(None)):
    context=context_from_request(request)
    if not (context.can("job_materials.manage") or context.can("jobs.manage")): raise HTTPException(403,"Job material permission required")
    with SessionLocal() as db:
        job=JobService(db,context).get(job_id)
        if not job: raise HTTPException(404,"Job not found or not assigned to you")
        line=next((line for line in job.line_items if line.id==line_id),None)
        if not line: raise HTTPException(404,"Job item not found")
        try:
            cost=actual_unit_cost if context.can("job_costs.manage") else str(line.actual_unit_cost); price=unit_price if context.can("job_costs.manage") else str(line.unit_price); discount=discount_percent if context.can("job_costs.manage") else str(line.discount_percent); is_billable=checked(billable) if context.can("job_costs.manage") else line.billable
            CatalogService(db,context).update_job_line(job,line_id,actual_quantity=actual_quantity,actual_unit_cost=cost,unit_price=price,discount_percent=discount,billable=is_billable); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect(f"/jobs/{job_id}","Job item updated.")


@router.post("/jobs/{job_id}/materials/{line_id}/delete")
def job_delete_material(request:Request,job_id:int,line_id:int):
    context=context_from_request(request)
    if not (context.can("job_materials.manage") or context.can("jobs.manage")): raise HTTPException(403,"Job material permission required")
    with SessionLocal() as db:
        job=JobService(db,context).get(job_id)
        if not job: raise HTTPException(404,"Job not found or not assigned to you")
        try: CatalogService(db,context).delete_job_line(job,line_id); db.commit()
        except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc
    return redirect(f"/jobs/{job_id}","Job item removed.")
