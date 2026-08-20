from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.models import OrganizationResource, Resource


class ResourceService:
    """Organization-scoped resource lookup and assignment service."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_organization(self, organization_id: int, *, provider_slug: str | None = None,
                              resource_type: str | None = None) -> list[Resource]:
        stmt = (
            select(Resource)
            .join(OrganizationResource, OrganizationResource.resource_id == Resource.id)
            .where(OrganizationResource.organization_id == organization_id)
        )
        if provider_slug:
            stmt = stmt.where(Resource.provider.has(slug=provider_slug))
        if resource_type:
            stmt = stmt.where(Resource.resource_type == resource_type)
        return list(self.db.scalars(stmt.order_by(Resource.display_name)).unique())

    def has_access(self, organization_id: int, resource_id: int) -> bool:
        stmt = select(OrganizationResource.id).where(
            OrganizationResource.organization_id == organization_id,
            OrganizationResource.resource_id == resource_id,
        )
        return self.db.scalar(stmt) is not None

    def assign(self, organization_id: int, resource_id: int, *, assigned_by: int | None = None,
               assignment_role: str = "owner") -> OrganizationResource:
        existing = self.db.scalar(select(OrganizationResource).where(
            OrganizationResource.organization_id == organization_id,
            OrganizationResource.resource_id == resource_id,
        ))
        if existing:
            return existing
        assignment = OrganizationResource(
            organization_id=organization_id,
            resource_id=resource_id,
            assigned_by=assigned_by,
            assignment_role=assignment_role,
        )
        self.db.add(assignment)
        self.db.flush()
        return assignment
