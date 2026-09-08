from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_satisfaction_note(job):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    styles = getSampleStyleSheet()

    SKY = colors.HexColor("#00BFFF")
    BORDER = colors.HexColor("#555555")
    LIGHT_BLUE = colors.HexColor("#b2ebff")
    LIGHT_GREY = colors.HexColor("#f5f5f5")

    company_style = ParagraphStyle(
        "Company",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        alignment=TA_CENTER,
        textColor=SKY,
    )

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        alignment=TA_CENTER,
    )

    normal = ParagraphStyle(
        "Normal",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=14,
    )

    bold = ParagraphStyle(
        "Bold",
        parent=normal,
        fontName="Helvetica-Bold",
    )

    elements = []

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------

    elements.append(
        Paragraph(
            "AUTOVEX",
            company_style,
        )
    )

    elements.append(
        Paragraph(
            "PROFESSIONAL AUTO REPAIR & VEHICLE SERVICES",
            ParagraphStyle(
                "Tag",
                parent=normal,
                alignment=TA_CENTER,
                textColor=colors.red,
                fontSize=8,
            ),
        )
    )

    elements.append(Spacer(1, 8))

    elements.append(
        Paragraph(
            "CUSTOMER SATISFACTION NOTE",
            title_style,
        )
    )

    elements.append(Spacer(1, 10))

    # --------------------------------------------------
    # DETAILS
    # --------------------------------------------------

    vehicle = job.vehicle

    details = [

        [
            Paragraph("<b>Job Card</b>", bold),
            Paragraph(str(job.id), normal),
            Paragraph("<b>Date</b>", bold),
            Paragraph(
                job.created_at.strftime("%d/%m/%Y"),
                normal,
            ),
        ],

        [
            Paragraph("<b>Customer</b>", bold),
            Paragraph(job.customer_name, normal),
            Paragraph("<b>Telephone</b>", bold),
            Paragraph(job.telno or "-", normal),
        ],

        [
            Paragraph("<b>Registration</b>", bold),
            Paragraph(job.vehicle, normal),
            Paragraph("<b>Vehicle</b>", bold),
            Paragraph(
                job.vehicle_model,
                normal,
            ),
        ],

        [
            Paragraph("<b>Mechanic</b>", bold),
            Paragraph(job.mechanic.username, normal),
            Paragraph("<b>Status</b>", bold),
            Paragraph(job.status, normal),
        ],

    ]

    table = Table(
        details,
        colWidths=[
            30 * mm,
            58 * mm,
            30 * mm,
            58 * mm,
        ],
    )

    table.setStyle(
        TableStyle([

            ("GRID", (0,0), (-1,-1), .5, BORDER),

            ("BACKGROUND",(0,0),(0,-1),LIGHT_GREY),
            ("BACKGROUND",(2,0),(2,-1),LIGHT_GREY),

            ("LEFTPADDING",(0,0),(-1,-1),5),
            ("RIGHTPADDING",(0,0),(-1,-1),5),

            ("TOPPADDING",(0,0),(-1,-1),5),
            ("BOTTOMPADDING",(0,0),(-1,-1),5),

        ])
    )

    elements.append(table)

    elements.append(Spacer(1, 15))

    # --------------------------------------------------
    # MESSAGE
    # --------------------------------------------------

    elements.append(
        Paragraph(
            (
                "I do confirm that I have been given the opportunity to inspect the vehicle and that I am satisfied with the work performed."
                "I further confirm that except for the work performed, the vehicle is in good condition and I have no further complaints."
                
            ),
            normal,
        )
    )

    elements.append(Spacer(1, 20))

    # --------------------------------------------------
    # SIGNATURE
    # --------------------------------------------------

    signature = Table(

        [

            ["Customer Name", ""],

            ["Signature", ""],

            ["Date", ""],

        ],

        colWidths=[45 * mm, 120 * mm],

    )

    signature.setStyle(
        TableStyle([

            ("GRID",(0,0),(-1,-1),.5,BORDER),

            ("BACKGROUND",(0,0),(0,-1),LIGHT_BLUE),

            ("LEFTPADDING",(0,0),(-1,-1),6),
            ("RIGHTPADDING",(0,0),(-1,-1),6),

            ("TOPPADDING",(0,0),(-1,-1),8),
            ("BOTTOMPADDING",(0,0),(-1,-1),8),

        ])
    )

    elements.append(signature)

    elements.append(Spacer(1, 25))

    elements.append(
        Paragraph(
            "Thank you for choosing AUTOVEX.",
            ParagraphStyle(
                "Footer",
                parent=normal,
                alignment=TA_CENTER,
            ),
        )
    )

    doc.build(elements)

    buffer.seek(0)

    return buffer