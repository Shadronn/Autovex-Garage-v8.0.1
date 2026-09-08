from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

from io import BytesIO
import os


# ============================================================
# INVOICE PDF GENERATOR
# ============================================================

def generate_invoice_pdf(invoice, job, company=None):
    """
    Generate a professional invoice PDF.

    Parameters
    ----------
    invoice : Invoice
        SQLAlchemy Invoice object.

    job : Jobs
        SQLAlchemy Jobs object associated with the invoice.

    company : Company, optional
        SQLAlchemy Company object containing business information.

    Returns
    -------
    BytesIO
        PDF file stored in memory.
    """

    buffer = BytesIO()

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"Invoice {invoice.invoice_number}",
        author=(
            company.company_name
            if company
            else "Vehicle Service Centre"
        ),
    )

    # --------------------------------------------------------
    # STYLES
    # --------------------------------------------------------

    styles = getSampleStyleSheet()

    company_style = ParagraphStyle(
        "Company",
        parent=styles["Normal"],
        fontSize=18,
        leading=22,
        alignment=TA_LEFT,
        spaceAfter=3,
        fontName="Helvetica-Bold",
    )

    normal = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        fontName="Helvetica",
    )

    small = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica",
    )

    small_bold = ParagraphStyle(
        "SmallBold",
        parent=small,
        fontName="Helvetica-Bold",
    )

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Normal"],
        fontSize=20,
        leading=24,
        alignment=TA_RIGHT,
        fontName="Helvetica-Bold",
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        fontName="Helvetica-Bold",
        spaceAfter=5,
    )

    right = ParagraphStyle(
        "Right",
        parent=normal,
        alignment=TA_RIGHT,
    )

    right_bold = ParagraphStyle(
        "RightBold",
        parent=normal,
        alignment=TA_RIGHT,
        fontName="Helvetica-Bold",
    )

    center = ParagraphStyle(
        "Center",
        parent=normal,
        alignment=TA_CENTER,
    )

    # --------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------

    def money(value):
        try:
            return f"KES {float(value or 0):,.2f}"
        except (ValueError, TypeError):
            return "KES 0.00"

    def format_date(value):
        if not value:
            return "—"

        return value.strftime("%d %b %Y")

    def safe(value):
        if value is None or value == "":
            return "—"

        return str(value)

    # --------------------------------------------------------
    # STORY
    # --------------------------------------------------------

    story = []

    # ========================================================
    # HEADER
    # ========================================================

    company_name = (
        company.company_name
        if company
        else "Vehicle Service Centre"
    )

    company_info = []

    company_info.append(
        Paragraph(company_name, company_style)
    )

    if company and company.tagline:
        company_info.append(
            Paragraph(
                safe(company.tagline),
                normal
            )
        )

    if company and company.address:
        company_info.append(
            Paragraph(
                safe(company.address),
                small
            )
        )

    if company and company.city:
        company_info.append(
            Paragraph(
                safe(company.city),
                small
            )
        )

    if company and company.phone:
        company_info.append(
            Paragraph(
                f"Tel: {safe(company.phone)}",
                small
            )
        )

    if company and company.alternate_phone:
        company_info.append(
            Paragraph(
                f"Alt: {safe(company.alternate_phone)}",
                small
            )
        )

    if company and company.email:
        company_info.append(
            Paragraph(
                f"Email: {safe(company.email)}",
                small
            )
        )

    if company and company.website:
        company_info.append(
            Paragraph(
                safe(company.website),
                small
            )
        )

    invoice_heading = [
        Paragraph("INVOICE", title_style),
        Spacer(1, 3),
        Paragraph(
            f"<b>Invoice #:</b> {safe(invoice.invoice_number)}",
            right,
        ),
        Paragraph(
            f"<b>Issue Date:</b> {format_date(invoice.issue_date)}",
            right,
        ),
        Paragraph(
            f"<b>Due Date:</b> {format_date(invoice.due_date)}",
            right,
        ),
    ]

    header_table = Table(
        [
            [
                company_info,
                invoice_heading
            ]
        ],
        colWidths=[105 * mm, 70 * mm],
    )

    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.append(header_table)
    story.append(Spacer(1, 8 * mm))

    # ========================================================
    # CUSTOMER / VEHICLE INFORMATION
    # ========================================================

    customer_name = safe(
        getattr(job, "customer_name", None)
    )

    phone = safe(
        getattr(job, "telno", None)
    )

    vehicle = safe(
        getattr(job, "vehicle", None)
    )

    vehicle_model = safe(
        getattr(job, "vehicle_model", None)
    )

    customer_data = [
        [
            Paragraph("<b>BILL TO</b>", section_style),
            Paragraph("<b>VEHICLE / JOB</b>", section_style),
        ],
        [
            Paragraph(
                f"<b>Customer:</b> {customer_name}<br/>"
                f"<b>Phone:</b> {phone}",
                normal,
            ),
            Paragraph(
                f"<b>Registration:</b> {vehicle}<br/>"
                f"<b>Model:</b> {vehicle_model}<br/>"
                f"<b>Job ID:</b> {safe(job.id)}",
                normal,
            ),
        ],
    ]

    customer_table = Table(
        customer_data,
        colWidths=[87.5 * mm, 87.5 * mm],
    )

    customer_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#f1f5f9"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#d9dee7"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#d9dee7"),
                ),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(customer_table)
    story.append(Spacer(1, 8 * mm))

    # ========================================================
    # JOB DESCRIPTION
    # ========================================================

    description = safe(
        getattr(job, "description", None)
    )

    story.append(
        Paragraph(
            "JOB DESCRIPTION",
            section_style
        )
    )

    description_table = Table(
        [
            [
                Paragraph(
                    description,
                    normal
                )
            ]
        ],
        colWidths=[175 * mm],
    )

    description_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#d9dee7"),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.white,
                ),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(description_table)
    story.append(Spacer(1, 8 * mm))

    # ========================================================
    # INVOICE TOTALS
    # ========================================================

    subtotal = float(invoice.subtotal or 0)
    tax_rate = float(invoice.tax_rate or 0)
    tax_amount = float(invoice.tax_amount or 0)
    total_amount = float(invoice.total_amount or 0)

    totals_data = [
        [
            Paragraph("Description", small_bold),
            Paragraph("Amount", right_bold),
        ],
        [
            Paragraph("Service / Repair", normal),
            Paragraph(money(subtotal), right),
        ],
        [
            Paragraph(
                f"Tax ({tax_rate:.2f}%)",
                normal
            ),
            Paragraph(
                money(tax_amount),
                right
            ),
        ],
        [
            Paragraph("<b>Invoice Total</b>", normal),
            Paragraph(
                f"<b>{money(total_amount)}</b>",
                right_bold
            ),
        ],
    ]

    totals_table = Table(
        totals_data,
        colWidths=[115 * mm, 60 * mm],
        hAlign="RIGHT",
    )

    totals_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#f1f5f9"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#d9dee7"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#d9dee7"),
                ),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(totals_table)
    story.append(Spacer(1, 7 * mm))

    # ========================================================
    # PAYMENT SUMMARY
    # ========================================================

    total_paid = float(invoice.amount or 0)
    balance = float(invoice.Balance or 0)

    payment_status = safe(invoice.status)

    payment_data = [
        [
            Paragraph("<b>Payment Status</b>", normal),
            Paragraph(
                f"<b>{payment_status}</b>",
                right
            ),
        ],
        [
            Paragraph("Amount Paid", normal),
            Paragraph(
                money(total_paid),
                right
            ),
        ],
        [
            Paragraph("Outstanding Balance", normal),
            Paragraph(
                f"<b>{money(balance)}</b>",
                right_bold
            ),
        ],
    ]

    payment_table = Table(
        payment_data,
        colWidths=[115 * mm, 60 * mm],
        hAlign="RIGHT",
    )

    payment_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#d9dee7"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#d9dee7"),
                ),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(payment_table)

    # ========================================================
    # PAYMENT HISTORY
    # ========================================================

    payments = list(
        getattr(invoice, "payments", []) or []
    )

    if payments:

        story.append(Spacer(1, 8 * mm))

        story.append(
            Paragraph(
                "PAYMENT HISTORY",
                section_style
            )
        )

        payment_rows = [
            [
                Paragraph("Receipt #", small_bold),
                Paragraph("Date", small_bold),
                Paragraph("Method", small_bold),
                Paragraph("Reference", small_bold),
                Paragraph("Amount", right_bold),
            ]
        ]

        for payment in payments:

            payment_rows.append(
                [
                    Paragraph(
                        safe(payment.receipt_number),
                        small
                    ),
                    Paragraph(
                        format_date(payment.paid_at),
                        small
                    ),
                    Paragraph(
                        safe(payment.payment_method),
                        small
                    ),
                    Paragraph(
                        safe(payment.payment_reference),
                        small
                    ),
                    Paragraph(
                        money(payment.amount),
                        ParagraphStyle(
                            "PaymentAmount",
                            parent=small,
                            alignment=TA_RIGHT,
                        )
                    ),
                ]
            )

        payment_history_table = Table(
            payment_rows,
            colWidths=[
                38 * mm,
                32 * mm,
                30 * mm,
                38 * mm,
                37 * mm,
            ],
            repeatRows=1,
        )

        payment_history_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#f1f5f9"),
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        colors.HexColor("#d9dee7"),
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor("#d9dee7"),
                    ),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (4, 0), (4, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        story.append(payment_history_table)

    # ========================================================
    # NOTES
    # ========================================================

    if invoice.notes:

        story.append(Spacer(1, 8 * mm))

        story.append(
            Paragraph(
                "NOTES",
                section_style
            )
        )

        notes_table = Table(
            [
                [
                    Paragraph(
                        safe(invoice.notes),
                        normal
                    )
                ]
            ],
            colWidths=[175 * mm],
        )

        notes_table.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        colors.HexColor("#d9dee7"),
                    ),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )

        story.append(notes_table)

    # ========================================================
    # FOOTER
    # ========================================================

    story.append(Spacer(1, 12 * mm))

    footer_text = (
        "Thank you for choosing "
        f"{company_name}."
    )

    story.append(
        Paragraph(
            footer_text,
            center
        )
    )

    story.append(
        Paragraph(
            "This is a computer-generated invoice.",
            ParagraphStyle(
                "FooterSmall",
                parent=small,
                alignment=TA_CENTER,
            )
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    doc.build(story)

    buffer.seek(0)

    return buffer