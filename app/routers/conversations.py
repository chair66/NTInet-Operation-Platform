from __future__ import annotations

from urllib.parse import quote_plus

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from app.database import SessionLocal
from app.database.ticket_models import Ticket
from app.security import context_from_request, require_permission
from app.services import AuditService, CustomerCommunicationService, TicketService
from app.services.conversation_service import ConversationService
from app.web import render


router = APIRouter(prefix="/communications", tags=["Unified Communications Inbox"])


def redirect(message: str = "", anchor: str = ""):
    target = "/communications"
    if message:
        target += f"?message={quote_plus(message)}"
    if anchor:
        target += f"#conversation-{anchor}"
    return RedirectResponse(target, status_code=303)


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def inbox(request: Request, status: str = "", channel: str = "", assignment: str = "",
          q: str = "", message: str = ""):
    require_permission(request, "customer_communications.read")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = ConversationService(db, context)
        conversations = service.list(status=status, channel=channel, assignment=assignment, query=q)
        assignees = service.available_assignees()
        customer_ids = {item.customer_id for item in conversations}
        tickets = list(db.scalars(select(Ticket).where(
            Ticket.customer_id.in_(customer_ids) if customer_ids else Ticket.id == -1,
            Ticket.status.not_in({"closed"}),
        ).order_by(Ticket.updated_at.desc())).unique())
        tickets_by_customer: dict[int, list[Ticket]] = {}
        for ticket in tickets:
            tickets_by_customer.setdefault(ticket.customer_id, []).append(ticket)
        for conversation in conversations:
            _ = tuple(conversation.messages)
            _ = conversation.ticket
            _ = conversation.estimate
        db.expunge_all()
    return render(request, "communications/inbox.html", conversations=conversations,
                  assignees=assignees, tickets_by_customer=tickets_by_customer,
                  selected_status=status, selected_channel=channel,
                  selected_assignment=assignment, query=q, message=message)


@router.post("/{conversation_id}/read")
def mark_read(request: Request, conversation_id: int):
    require_permission(request, "customer_communications.read")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = ConversationService(db, context); conversation = service.get(conversation_id)
        if not conversation: raise HTTPException(404, "Conversation not found")
        service.mark_read(conversation); db.commit()
    return redirect("Conversation marked read.", str(conversation_id))


@router.post("/{conversation_id}/status")
def set_status(request: Request, conversation_id: int, status: str = Form(...)):
    require_permission(request, "customer_communications.send")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = ConversationService(db, context); conversation = service.get(conversation_id)
        if not conversation: raise HTTPException(404, "Conversation not found")
        service.set_status(conversation, status)
        AuditService(db, request, context).record("communications.status_changed", "communication_conversation",
            conversation.id, f"Conversation status changed to {status}", module="customer-management",
            organization_id=conversation.organization_id)
        db.commit()
    return redirect("Conversation status updated.", str(conversation_id))


@router.post("/{conversation_id}/assign")
def assign(request: Request, conversation_id: int, user_id: str = Form("")):
    require_permission(request, "customer_communications.send")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = ConversationService(db, context); conversation = service.get(conversation_id)
        if not conversation: raise HTTPException(404, "Conversation not found")
        service.assign(conversation, int(user_id) if user_id.strip() else None)
        AuditService(db, request, context).record("communications.assigned", "communication_conversation",
            conversation.id, "Conversation assignment updated", module="customer-management",
            organization_id=conversation.organization_id, event_data={"assigned_user_id": conversation.assigned_user_id})
        db.commit()
    return redirect("Conversation assignment updated.", str(conversation_id))


@router.post("/{conversation_id}/link-ticket")
def link_ticket(request: Request, conversation_id: int, ticket_id: str = Form("")):
    require_permission(request, "customer_communications.send")
    context = context_from_request(request)
    with SessionLocal() as db:
        service = ConversationService(db, context); conversation = service.get(conversation_id)
        if not conversation: raise HTTPException(404, "Conversation not found")
        selected = int(ticket_id) if ticket_id.strip() else None
        if selected and not db.scalar(select(Ticket.id).where(Ticket.id == selected, Ticket.customer_id == conversation.customer_id)):
            raise HTTPException(400, "Ticket does not belong to this customer")
        service.link_ticket(conversation, selected); db.commit()
    return redirect("Ticket link updated.", str(conversation_id))


@router.post("/{conversation_id}/create-ticket")
def create_ticket(request: Request, conversation_id: int):
    require_permission(request, "customer_communications.create_ticket")
    require_permission(request, "tickets.create")
    context = context_from_request(request)
    if not context.has_module_assignment("support-tickets"):
        raise HTTPException(403, "Your organization does not have access to Support Tickets.")
    with SessionLocal() as db:
        conversation_service = ConversationService(db, context); conversation = conversation_service.get(conversation_id)
        if not conversation: raise HTTPException(404, "Conversation not found")
        if conversation.ticket_id:
            return RedirectResponse(f"/tickets/{conversation.ticket_id}", status_code=303)
        ticket = TicketService(db, context).create(
            customer_id=conversation.customer_id,
            subject=conversation.subject or f"{conversation.channel.upper()} conversation with {conversation.contact.full_name if conversation.contact else 'customer'}",
            description="\n\n".join(message.body for message in conversation.messages[-5:]),
            contact_id=conversation.contact_id, location_id=None, service_id=None,
            ticket_type="support", priority="normal", assigned_user_id=conversation.assigned_user_id, due_at=None,
        )
        conversation_service.link_ticket(conversation, ticket.id)
        db.commit(); ticket_id = ticket.id
    return RedirectResponse(f"/tickets/{ticket_id}?message=Ticket+created+from+conversation.", status_code=303)


@router.post("/{conversation_id}/reply")
def reply(request: Request, conversation_id: int, body: str = Form(...),
          consent_override: str | None = Form(None), consent_override_reason: str = Form("")):
    require_permission(request, "customer_communications.send")
    context = context_from_request(request)
    with SessionLocal() as db:
        conversation_service = ConversationService(db, context); conversation = conversation_service.get(conversation_id)
        if not conversation: raise HTTPException(404, "Conversation not found")
        if not conversation.contact_id:
            raise HTTPException(400, "A customer contact is required before replying.")
        allow_override = bool(consent_override and context.can("tickets.communication_override"))
        try:
            communication = CustomerCommunicationService(db).send(
                conversation.customer, contact_id=conversation.contact_id,
                channel=conversation.channel,
                subject=(f"Re: {conversation.subject}" if conversation.channel == "email" else ""),
                body=body, profile_id=conversation.communication_profile_id,
                ticket_id=conversation.ticket_id, consent_override=allow_override,
                override_reason=consent_override_reason, actor_user_id=context.user_id,
                conversation_id=conversation.id,
            )
            conversation_service.mark_read(conversation)
            AuditService(db, request, context).record("communications.replied", "communication_conversation",
                conversation.id, f"{conversation.channel.upper()} reply: {communication.status}",
                module="customer-management", organization_id=conversation.organization_id)
            db.commit(); result = communication.status
        except ValueError as exc:
            db.rollback(); raise HTTPException(400, str(exc)) from exc
    return redirect(f"Reply recorded: {result}.", str(conversation_id))
