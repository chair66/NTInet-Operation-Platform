from __future__ import annotations
from io import BytesIO
import base64
from string import Template
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image


def merge_template(value:str,context:dict[str,str]) -> str:
    # Support the friendly {{field}} tokens shown in the UI.
    result=value
    for key,replacement in context.items(): result=result.replace("{{"+key+"}}",replacement)
    return result


def quantity_text(line) -> str:
    return f"{line.quantity:.1f}" if line.item_type=="labor" else f"{line.quantity:.0f}"


def estimate_pdf(estimate,options) -> bytes:
    stream=BytesIO(); doc=SimpleDocTemplate(stream,pagesize=letter,rightMargin=.55*inch,leftMargin=.55*inch,topMargin=.55*inch,bottomMargin=.55*inch)
    styles=getSampleStyleSheet(); story=[Paragraph("NTInet Sales Proposal",styles["Title"]),Paragraph(f"{estimate.estimate_number} · {estimate.title}",styles["Heading2"]),Paragraph(f"Prepared for <b>{estimate.customer.name}</b>",styles["Normal"]),Spacer(1,14)]
    for index,option in enumerate(options):
        if index: story.append(PageBreak())
        story.extend([Paragraph(option.name,styles["Heading1"]),Paragraph("This option is priced independently from every other option in this proposal.",styles["Italic"]),Spacer(1,10)])
        data=[["Description","Qty","Rate","Total"]]
        for line in option.lines: data.append([Paragraph(line.description,styles["BodyText"]),f"{quantity_text(line)} {line.unit}",f"${line.unit_price:.2f}",f"${line.line_total:.2f}"])
        table=Table(data,colWidths=[3.8*inch,1*inch,1*inch,1*inch],repeatRows=1); table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#eeeeee")),("GRID",(0,0),(-1,-1),.5,colors.HexColor("#bbbbbb")),("ALIGN",(1,1),(-1,-1),"RIGHT"),("VALIGN",(0,0),(-1,-1),"TOP"),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("PADDING",(0,0),(-1,-1),7)])); story.extend([table,Spacer(1,12)])
        totals=[["Subtotal",f"${option.subtotal:.2f}"],["Discount",f"-${option.discount_total:.2f}"],["Tax",f"${option.tax_total:.2f}"],["Option Total",f"${option.total:.2f}"]]; t=Table(totals,colWidths=[5.8*inch,1*inch]); t.setStyle(TableStyle([("ALIGN",(1,0),(-1,-1),"RIGHT"),("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"),("LINEABOVE",(0,-1),(-1,-1),1,colors.black),("PADDING",(0,0),(-1,-1),5)])); story.append(t)
        if option.customer_notes: story.extend([Spacer(1,12),Paragraph("Option Notes",styles["Heading3"]),Paragraph(option.customer_notes.replace("\n","<br/>"),styles["BodyText"])])
    if estimate.customer_notes: story.extend([Spacer(1,16),Paragraph("Estimate Notes",styles["Heading3"]),Paragraph(estimate.customer_notes.replace("\n","<br/>"),styles["BodyText"])])
    if estimate.status in {"won","converted"} and estimate.accepted_by_name:
        story.extend([Spacer(1,16),Paragraph("Accepted Online",styles["Heading3"]),Paragraph(f"Signed by {estimate.accepted_by_name} ({estimate.accepted_by_email})",styles["BodyText"])])
        if estimate.accepted_signature_data and "," in estimate.accepted_signature_data:
            try: story.append(Image(BytesIO(base64.b64decode(estimate.accepted_signature_data.split(",",1)[1])),width=2.4*inch,height=.9*inch,kind="proportional"))
            except Exception: pass
    doc.build(story); return stream.getvalue()
