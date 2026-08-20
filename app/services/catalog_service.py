from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from uuid import uuid4

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.database.catalog_models import CatalogCategory, CatalogItem, Estimate, EstimateEmailTemplate, EstimateLineItem, EstimateOption, JobLineItem, StoredDocument
from app.database.customer_models import Customer, CustomerContact, CustomerLocation
from app.database.job_models import Job
from app.database.models import Organization
from app.security.context import SecurityContext


ITEM_TYPES={"product","service","material","labor","fee","discount"}
ESTIMATE_STATUSES={"draft","sent","won","declined","expired","converted"}
CENT=Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return Decimal(value or 0).quantize(CENT,rounding=ROUND_HALF_UP)


def decimal_value(value, *, minimum: Decimal | None=None, maximum: Decimal | None=None) -> Decimal:
    try: result=Decimal(str(value))
    except (InvalidOperation,ValueError,TypeError) as exc: raise ValueError("Enter a valid numeric value.") from exc
    if minimum is not None and result<minimum: raise ValueError(f"Value must be at least {minimum}.")
    if maximum is not None and result>maximum: raise ValueError(f"Value must not exceed {maximum}.")
    return result


def item_description(item: CatalogItem) -> str:
    identity=" ".join(part for part in (item.brand,item.model_number) if part)
    result=item.name+(f" ({identity})" if identity else "")
    return result+(f" — {item.description}" if item.description else "")


def catalog_quantity(item_type:str,value,*,allow_zero:bool=False) -> Decimal:
    minimum=Decimal("0") if allow_zero else (Decimal("0.5") if item_type=="labor" else Decimal("1"))
    quantity=decimal_value(value,minimum=minimum)
    if item_type=="labor":
        if quantity*2 != (quantity*2).to_integral_value(): raise ValueError("Labor quantity must use 0.5-hour increments.")
    elif quantity != quantity.to_integral_value(): raise ValueError("Product and non-labor quantities must be whole numbers.")
    return quantity


@dataclass(slots=True)
class CatalogService:
    db: Session
    context: SecurityContext

    def _staff_org(self) -> Organization:
        if not self.context.is_staff: raise PermissionError("Catalogs and estimates are restricted to NTInet staff.")
        organization=self.db.scalar(select(Organization).where(Organization.slug=="ntinet",Organization.active.is_(True)))
        if not organization: raise ValueError("The NTInet staff organization is not configured.")
        return organization

    def catalog(self, *, query:str="",item_type:str="",active_only:bool=True) -> list[CatalogItem]:
        org=self._staff_org(); statement=select(CatalogItem).options(
            selectinload(CatalogItem.category_record).selectinload(CatalogCategory.parent)
        ).where(CatalogItem.organization_id==org.id)
        if active_only: statement=statement.where(CatalogItem.active.is_(True))
        if item_type in ITEM_TYPES: statement=statement.where(CatalogItem.item_type==item_type)
        if query.strip():
            term=f"%{query.strip().lower()}%"; statement=statement.where(or_(func.lower(CatalogItem.name).like(term),func.lower(CatalogItem.category).like(term),func.lower(CatalogItem.brand).like(term),func.lower(CatalogItem.model_number).like(term)))
        return list(self.db.scalars(statement.order_by(CatalogItem.category,CatalogItem.name)).unique())

    def catalog_item(self,item_id:int) -> CatalogItem | None:
        org=self._staff_org(); return self.db.scalar(select(CatalogItem).where(CatalogItem.id==item_id,CatalogItem.organization_id==org.id))

    def categories(self, *, active_only:bool=True) -> list[CatalogCategory]:
        org=self._staff_org(); statement=select(CatalogCategory).options(
            selectinload(CatalogCategory.parent),selectinload(CatalogCategory.children),
            selectinload(CatalogCategory.items)
        ).where(CatalogCategory.organization_id==org.id)
        if active_only: statement=statement.where(CatalogCategory.active.is_(True))
        return list(self.db.scalars(statement.order_by(CatalogCategory.parent_id.nulls_first(),CatalogCategory.name)).unique())

    def category(self,category_id:int) -> CatalogCategory | None:
        org=self._staff_org(); return self.db.scalar(select(CatalogCategory).where(CatalogCategory.id==category_id,CatalogCategory.organization_id==org.id))

    def save_category(self,category:CatalogCategory|None,*,name:str,description:str,active:bool,parent_id:int|None=None) -> CatalogCategory:
        org=self._staff_org(); name=" ".join(name.split())
        if not name: raise ValueError("Category name is required.")
        duplicate=self.db.scalar(select(CatalogCategory.id).where(CatalogCategory.organization_id==org.id,func.lower(CatalogCategory.name)==name.lower(),CatalogCategory.id!=(category.id if category else -1)))
        if duplicate: raise ValueError("That catalog category already exists.")
        parent=self.category(parent_id) if parent_id else None
        if parent_id and not parent: raise ValueError("Select a valid parent category.")
        if parent and parent.parent_id: raise ValueError("Only one sub-category level is supported.")
        if category and parent and (parent.id==category.id or parent.parent_id==category.id): raise ValueError("A category cannot be its own parent.")
        if category and category.children and parent: raise ValueError("A category with sub-categories cannot become a sub-category.")
        if category and category.children and not active and any(child.active for child in category.children): raise ValueError("Deactivate this category's active sub-categories first.")
        if not category:
            category=CatalogCategory(organization_id=org.id,created_by_user_id=self.context.user_id); self.db.add(category)
        category.name=name; category.description=description.strip(); category.parent_id=parent.id if parent else None; category.active=active; category.updated_by_user_id=self.context.user_id
        self.db.flush()
        self.db.execute(update(CatalogItem).where(CatalogItem.category_id==category.id).values(category=name))
        return category

    def save_catalog_item(self,item:CatalogItem|None,*,item_type:str,category_id:int,name:str,brand:str,model_number:str,ordering_note:str,ordering_url:str,description:str,unit:str,unit_cost,unit_price,taxable:bool,active:bool) -> CatalogItem:
        org=self._staff_org(); name=name.strip()
        if not name: raise ValueError("Item name is required.")
        if item_type not in ITEM_TYPES: raise ValueError("Select a valid catalog item type.")
        category=self.category(category_id)
        if not category or (not category.active and (not item or item.category_id!=category.id)): raise ValueError("Select an active catalog category.")
        cost=decimal_value(unit_cost,minimum=Decimal("0")); price=decimal_value(unit_price)
        if item_type!="discount" and price<0: raise ValueError("Only discount catalog items may have a negative selling price.")
        ordering_url=ordering_url.strip()
        if ordering_url and not ordering_url.lower().startswith(("http://","https://")): raise ValueError("Ordering link must begin with http:// or https://.")
        if not item:
            item=CatalogItem(organization_id=org.id,sku=f"INTERNAL-{uuid4().hex}",created_by_user_id=self.context.user_id); self.db.add(item)
        item.item_type=item_type; item.category_id=category.id; item.category=category.name; item.name=name
        item.brand=brand.strip(); item.model_number=model_number.strip(); item.ordering_note=ordering_note.strip(); item.ordering_url=ordering_url
        item.description=description.strip(); item.unit=unit.strip() or "each"; item.unit_cost=cost; item.unit_price=price
        item.taxable=taxable; item.active=active; item.updated_by_user_id=self.context.user_id
        self.db.flush(); return item

    def customers(self) -> list[Customer]:
        self._staff_org(); return list(self.db.scalars(select(Customer).where(Customer.status=="active").order_by(Customer.name)).unique())

    def estimates(self,status:str="",query:str="") -> list[Estimate]:
        org=self._staff_org(); statement=select(Estimate).where(Estimate.organization_id==org.id)
        if status in ESTIMATE_STATUSES: statement=statement.where(Estimate.status==status)
        if query.strip():
            term=f"%{query.strip().lower()}%"; statement=statement.join(Customer).where(or_(func.lower(Estimate.estimate_number).like(term),func.lower(Estimate.title).like(term),func.lower(Customer.name).like(term)))
        return list(self.db.scalars(statement.order_by(Estimate.updated_at.desc())).unique())

    def estimate(self,estimate_id:int) -> Estimate | None:
        org=self._staff_org(); return self.db.scalar(select(Estimate).where(Estimate.id==estimate_id,Estimate.organization_id==org.id))

    def create_estimate(self,*,customer_id:int,contact_id:int|None,location_id:int,title:str,valid_until:date|None,tax_rate,internal_notes:str,customer_notes:str) -> Estimate:
        org=self._staff_org(); customer=self.db.get(Customer,customer_id)
        if not self.db.scalar(select(EstimateEmailTemplate.id).where(EstimateEmailTemplate.organization_id==org.id)):
            self.db.add(EstimateEmailTemplate(organization_id=org.id,name="Standard Estimate",subject_template="Sales Proposal from NTInet for {{customer_name}}",body_template="{{contact_name}},\n\nThank you for giving NTInet an opportunity to take care of your service needs.\n\nAttached is proposal {{estimate_number}} for {{estimate_title}}.\n\nSelected options: {{option_names}}\n\nShould you have questions, please contact us.\n\n{{sender_name}}",active=True,created_by_user_id=self.context.user_id,updated_by_user_id=self.context.user_id))
        if not customer or customer.status!="active": raise ValueError("Select an active customer.")
        location=self.db.scalar(select(CustomerLocation).where(CustomerLocation.id==location_id,CustomerLocation.customer_id==customer.id,CustomerLocation.active.is_(True)))
        if not location: raise ValueError("Select an active location for this customer.")
        if contact_id and not self.db.scalar(select(CustomerContact.id).where(CustomerContact.id==contact_id,CustomerContact.customer_id==customer.id,CustomerContact.active.is_(True))): raise ValueError("The selected contact does not belong to this customer.")
        if not title.strip(): raise ValueError("Estimate title is required.")
        rate=decimal_value(tax_rate,minimum=Decimal("0"),maximum=Decimal("100"))
        estimate=Estimate(estimate_number=f"PENDING-{self.context.user_id}",organization_id=org.id,customer_id=customer.id,contact_id=contact_id,location_id=location.id,status="draft",title=title.strip(),valid_until=valid_until,tax_rate=rate,internal_notes=internal_notes.strip(),customer_notes=customer_notes.strip(),created_by_user_id=self.context.user_id,updated_by_user_id=self.context.user_id)
        self.db.add(estimate); self.db.flush(); estimate.estimate_number=f"EST-{estimate.id:06d}"
        estimate.options.append(EstimateOption(name="Estimate",customer_notes=customer_notes.strip(),sort_order=1)); self.db.flush(); return estimate

    def update_estimate(self,estimate:Estimate,*,title:str,valid_until:date|None,tax_rate,internal_notes:str,customer_notes:str,status:str) -> Estimate:
        if status not in ESTIMATE_STATUSES: raise ValueError("Select a valid estimate status.")
        if not title.strip(): raise ValueError("Estimate title is required.")
        estimate.title=title.strip(); estimate.valid_until=valid_until; estimate.tax_rate=decimal_value(tax_rate,minimum=Decimal("0"),maximum=Decimal("100")); estimate.internal_notes=internal_notes.strip(); estimate.customer_notes=customer_notes.strip(); estimate.status=status; estimate.updated_by_user_id=self.context.user_id
        self.recalculate_estimate(estimate); return estimate

    def add_option(self,estimate:Estimate,name:str) -> EstimateOption:
        name=" ".join(name.split())
        if not name: raise ValueError("Option name is required.")
        if any(option.name.lower()==name.lower() for option in estimate.options): raise ValueError("That option name already exists on this estimate.")
        option=EstimateOption(estimate=estimate,name=name,sort_order=len(estimate.options)+1); self.db.add(option); self.db.flush(); return option

    def update_option(self,estimate:Estimate,option_id:int,*,name:str,customer_notes:str) -> EstimateOption:
        option=next((x for x in estimate.options if x.id==option_id),None)
        if not option: raise ValueError("Estimate option not found.")
        name=" ".join(name.split())
        if not name: raise ValueError("Option name is required.")
        if any(x.id!=option.id and x.name.lower()==name.lower() for x in estimate.options): raise ValueError("That option name already exists.")
        option.name=name; option.customer_notes=customer_notes.strip(); return option

    def delete_option(self,estimate:Estimate,option_id:int) -> None:
        if len(estimate.options)<=1: raise ValueError("An estimate must have at least one option.")
        option=next((x for x in estimate.options if x.id==option_id),None)
        if not option: raise ValueError("Estimate option not found.")
        self.db.delete(option); self.db.flush(); self.recalculate_estimate(estimate)

    def add_estimate_line(self,estimate:Estimate,*,catalog_item_id:int,quantity,discount_percent,unit_price=None,option_id:int|None=None) -> EstimateLineItem:
        item=self.catalog_item(catalog_item_id)
        if not item or not item.active: raise ValueError("Select an active catalog item.")
        qty=catalog_quantity(item.item_type,quantity)
        discount=decimal_value(discount_percent,minimum=Decimal("0"),maximum=Decimal("100")); price=item.unit_price if unit_price in (None,"") else decimal_value(unit_price)
        option=next((x for x in estimate.options if x.id==(option_id or estimate.options[0].id)),None)
        if not option: raise ValueError("Select a valid estimate option.")
        line=EstimateLineItem(estimate=estimate,option=option,catalog_item_id=item.id,sort_order=len(option.lines)+1,item_type=item.item_type,sku=item.sku,description=item_description(item),unit=item.unit,quantity=qty,unit_cost=item.unit_cost,unit_price=price,discount_percent=discount,taxable=item.taxable)
        self.db.add(line); self.db.flush(); self.recalculate_estimate(estimate); return line

    def delete_estimate_line(self,estimate:Estimate,line_id:int) -> None:
        line=next((line for line in estimate.lines if line.id==line_id),None); option=line.option if line else None
        if not line: raise ValueError("Estimate line item not found.")
        self.db.delete(line); self.db.flush(); self.db.expire(option,["lines"]); self.recalculate_estimate(estimate)

    def recalculate_estimate(self,estimate:Estimate) -> None:
        for option in estimate.options:
            subtotal=discount=taxable=cost=Decimal("0")
            for line in option.lines:
                line.line_cost=money(line.quantity*line.unit_cost); line.line_subtotal=money(line.quantity*line.unit_price); line.line_discount=money(line.line_subtotal*line.discount_percent/Decimal("100")); line.line_total=money(line.line_subtotal-line.line_discount)
                subtotal+=line.line_subtotal; discount+=line.line_discount; cost+=line.line_cost
                if line.taxable: taxable+=line.line_total
            option.subtotal=money(subtotal); option.discount_total=money(discount); option.taxable_subtotal=money(taxable); option.tax_total=money(taxable*estimate.tax_rate/Decimal("100")); option.total=money(subtotal-discount+option.tax_total); option.estimated_cost=money(cost); option.gross_profit=money(option.total-option.tax_total-cost)
            revenue=option.total-option.tax_total; option.margin_percent=money(option.gross_profit/revenue*Decimal("100")) if revenue else Decimal("0")
        primary=estimate.options[0] if estimate.options else None
        for field in ("subtotal","discount_total","taxable_subtotal","tax_total","total","estimated_cost","gross_profit","margin_percent"): setattr(estimate,field,getattr(primary,field) if primary else Decimal("0"))

    def email_templates(self,active_only:bool=True) -> list[EstimateEmailTemplate]:
        org=self._staff_org(); statement=select(EstimateEmailTemplate).where(EstimateEmailTemplate.organization_id==org.id)
        if active_only: statement=statement.where(EstimateEmailTemplate.active.is_(True))
        return list(self.db.scalars(statement.order_by(EstimateEmailTemplate.name)))

    def stored_documents(self) -> list[StoredDocument]:
        org=self._staff_org(); return list(self.db.scalars(select(StoredDocument).where(StoredDocument.organization_id==org.id,StoredDocument.active.is_(True)).order_by(StoredDocument.name)))

    def customer_jobs(self,estimate:Estimate) -> list[Job]:
        return list(self.db.scalars(select(Job).where(Job.customer_id==estimate.customer_id,Job.status.not_in({"cancelled"})).order_by(Job.created_at.desc())).unique())

    def copy_estimate_to_job(self,estimate:Estimate,job:Job,option_id:int|None=None) -> int:
        if estimate.status!="won": raise ValueError("Only an Estimate Won can be converted to a job.")
        if job.customer_id!=estimate.customer_id: raise ValueError("The job and estimate must belong to the same customer.")
        try: won_ids={int(x) for x in __import__("json").loads(estimate.won_option_ids_json or "[]")}
        except (TypeError,ValueError): won_ids=set()
        if option_id and won_ids and option_id not in won_ids: raise ValueError("Select an accepted estimate option.")
        option=next((item for item in estimate.options if item.id==(option_id or estimate.options[0].id)),None) if estimate.options else None
        if not option: raise ValueError("Select a valid estimate option.")
        existing=set(self.db.scalars(select(JobLineItem.estimate_line_item_id).where(
            JobLineItem.job_id==job.id,JobLineItem.estimate_line_item_id.is_not(None)))); added=0
        for source in option.lines:
            if source.id in existing: continue
            job.line_items.append(JobLineItem(catalog_item_id=source.catalog_item_id,estimate_line_item_id=source.id,sort_order=len(job.line_items)+1,item_type=source.item_type,sku=source.sku,description=source.description,unit=source.unit,estimated_quantity=source.quantity,actual_quantity=source.quantity,estimated_unit_cost=source.unit_cost,actual_unit_cost=source.unit_cost,unit_price=source.unit_price,discount_percent=source.discount_percent,taxable=source.taxable,billable=True,created_by_user_id=self.context.user_id,updated_by_user_id=self.context.user_id)); added+=1
        estimate.job_id=job.id; estimate.status="converted"; estimate.updated_by_user_id=self.context.user_id
        self.db.flush(); return added

    def add_job_line(self,job:Job,*,catalog_item_id:int,estimated_quantity,actual_quantity) -> JobLineItem:
        item=self.catalog_item(catalog_item_id)
        if not item or not item.active: raise ValueError("Select an active catalog item.")
        estimated=catalog_quantity(item.item_type,estimated_quantity,allow_zero=True); actual=catalog_quantity(item.item_type,actual_quantity,allow_zero=True)
        line=JobLineItem(job_id=job.id,catalog_item_id=item.id,sort_order=len(job.line_items)+1,item_type=item.item_type,sku=item.sku,description=item_description(item),unit=item.unit,estimated_quantity=estimated,actual_quantity=actual,estimated_unit_cost=item.unit_cost,actual_unit_cost=item.unit_cost,unit_price=item.unit_price,discount_percent=Decimal("0"),taxable=item.taxable,billable=True,created_by_user_id=self.context.user_id,updated_by_user_id=self.context.user_id)
        self.db.add(line); self.db.flush(); return line

    def update_job_line(self,job:Job,line_id:int,*,actual_quantity,actual_unit_cost,unit_price,discount_percent,billable:bool) -> JobLineItem:
        line=next((line for line in job.line_items if line.id==line_id),None)
        if not line: raise ValueError("Job line item not found.")
        line.actual_quantity=catalog_quantity(line.item_type,actual_quantity,allow_zero=True); line.actual_unit_cost=decimal_value(actual_unit_cost,minimum=Decimal("0")); line.unit_price=decimal_value(unit_price); line.discount_percent=decimal_value(discount_percent,minimum=Decimal("0"),maximum=Decimal("100")); line.billable=billable; line.updated_by_user_id=self.context.user_id; return line

    def delete_job_line(self,job:Job,line_id:int) -> None:
        line=next((line for line in job.line_items if line.id==line_id),None)
        if not line: raise ValueError("Job line item not found.")
        self.db.delete(line)

    @staticmethod
    def job_financials(job:Job) -> dict[str,Decimal]:
        estimated_cost=actual_cost=revenue=Decimal("0")
        for line in job.line_items:
            estimated_cost+=line.estimated_quantity*line.estimated_unit_cost; actual_cost+=line.actual_quantity*line.actual_unit_cost
            if line.billable: revenue+=line.actual_quantity*line.unit_price*(Decimal("1")-line.discount_percent/Decimal("100"))
        estimated_cost=money(estimated_cost); actual_cost=money(actual_cost); revenue=money(revenue); profit=money(revenue-actual_cost)
        return {"estimated_cost":estimated_cost,"actual_cost":actual_cost,"cost_variance":money(actual_cost-estimated_cost),"revenue":revenue,"gross_profit":profit,"margin_percent":money(profit/revenue*Decimal("100")) if revenue else Decimal("0")}
