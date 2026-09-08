from io import BytesIO
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)


def generate_inspection_pdf(inspection, job):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    # ==================================================
    # COLORS
    # ==================================================

    DARK_GREEN = colors.HexColor("#006B3C")
    DEEP_SKY_BLUE = colors.HexColor("#00BFFF")
    LIGHT_SKY_BLUE = colors.HexColor("#b2ebff")
    BORDER = colors.HexColor("#555555")
    LIGHT_GREY = colors.HexColor("#F4F4F4")
    RED = colors.HexColor("#FF0000")

    # ==================================================
    # STYLES
    # ==================================================

    styles = getSampleStyleSheet()

    company_style = ParagraphStyle(
        "CompanyStyle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=22,
        alignment=TA_CENTER,
        textColor=DEEP_SKY_BLUE,
    )

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.black,
    )

    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        alignment=TA_LEFT,
        textColor=colors.black,
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
    )
    tag_style = ParagraphStyle(
            "TagStyle",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=8,
            alignment=TA_CENTER,
            textColor=RED,
        )
    
    small_style = ParagraphStyle(
        "SmallStyle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7,
        leading=8,
    )

    bold_style = ParagraphStyle(
        "BoldStyle",
        parent=normal_style,
        fontName="Helvetica-Bold",
    )

    elements = []

    # ==================================================
    # HELPER FUNCTIONS
    # ==================================================

    def value(value):
        return str(value) if value not in [None, ""] else "-"

    def condition(value):
        return value if value else "-"

    def boolean_status(value):
        return "Present" if value else "Missing"

    def make_item_table(title, items):

        data = [
            [
                Paragraph(
                    f"<b>{title}</b>",
                    section_style
                ),
                Paragraph(
                    "<b>Condition / Remarks</b>",
                    section_style
                ),
            ]
        ]

        for item_name, item_value in items:

            data.append(
                [
                    Paragraph(
                        item_name,
                        small_style
                    ),
                    Paragraph(
                        condition(item_value),
                        small_style
                    ),
                ]
            )

        table = Table(
            data,
            colWidths=[
                40 * mm,
                45 * mm,
            ],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [

                    # Header
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        LIGHT_SKY_BLUE,
                    ),

                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),

                    # Borders
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        BORDER,
                    ),

                    # Body
                    (
                        "BACKGROUND",
                        (0, 1),
                        (-1, -1),
                        colors.white,
                    ),

                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        3,
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        3,
                    ),

                ]
            )
        )

        return table

    # ==================================================
    # COMPANY HEADER
    # ==================================================

    elements.append(
        Paragraph(
            "AUTOVEX",
            company_style
        )
    )

    elements.append(
        Paragraph(
            "PROFESSIONAL AUTO REPAIR & VEHICLE SERVICES",
            tag_style
        )
    )

    elements.append(
        Spacer(
            1,
            4
        )
    )

    elements.append(
        Paragraph(
            "VEHICLE CHECK-IN / CHECK-OUT LIST",
            title_style
        )
    )

    elements.append(
        Spacer(
            1,
            8
        )
    )

    # ==================================================
    # JOB / VEHICLE DETAILS
    # ==================================================

    vehicle = inspection.vehicle

    details_data = [

        [
            Paragraph("<b>JOB CARD NO.</b>", small_style),
            Paragraph(
                value(job.id),
                small_style
            ),

            Paragraph("<b>DATE</b>", small_style),
            Paragraph(
                value(
                    job.created_at.strftime("%d/%m/%Y")
                    if job.created_at
                    else "-"
                ),
                small_style
            ),
        ],

        [
            Paragraph("<b>REG. NO.</b>", small_style),
            Paragraph(
                value(vehicle.registration_no),
                small_style
            ),

            Paragraph("<b>MAKE</b>", small_style),
            Paragraph(
                value(vehicle.model),
                small_style
            ),
        ],

        [
            Paragraph("<b>MODEL</b>", small_style),
            Paragraph(
                value(vehicle.model),
                small_style
            ),

            Paragraph("<b>COLOR</b>", small_style),
            Paragraph(
                value(vehicle.color),
                small_style
            ),
        ],

        [
            Paragraph("<b>CUSTOMER</b>", small_style),
            Paragraph(
                value(
                    vehicle.customer.customer_name
                ),
                small_style
            ),

        
        Paragraph("<b>TEL NO.</b>", small_style),
            Paragraph(
                value(
                    vehicle.customer.telno
                ),
                small_style
            ),

        ],

    ]

    details_table = Table(
        details_data,
        colWidths=[
            25 * mm,
            60 * mm,
            25 * mm,
            60 * mm,
        ],
    )

    details_table.setStyle(
        TableStyle(
            [

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER,
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    LIGHT_GREY,
                ),

                (
                    "BACKGROUND",
                    (2, 0),
                    (2, -1),
                    LIGHT_GREY,
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),

            ]
        )
    )

    elements.append(
        details_table
    )

    elements.append(
        Spacer(
            1,
            8
        )
    )

    # ==================================================
    # RELEASED FROM / TO
    # ==================================================

    released_data = [

        [
            Paragraph(
                "<b>RELEASED FROM:</b>",
                small_style
            ),

            Paragraph(
                "____________________________",
                small_style
            ),

            Paragraph(
                "<b>TO:</b>",
                small_style
            ),

            Paragraph(
                "____________________________",
                small_style
            ),

        ]

    ]

    released_table = Table(
        released_data,
        colWidths=[
            35 * mm,
            55 * mm,
            15 * mm,
            65 * mm,
        ],
    )

    released_table.setStyle(
        TableStyle(
            [

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),

            ]
        )
    )

    elements.append(
        released_table
    )

    elements.append(
        Spacer(
            1,
            8
        )
    )

    # ==================================================
    # EXTERIOR AND INTERIOR
    # ==================================================

    exterior_items = [

        (
            "Front Bumper",
            inspection.front_bumper
        ),

        (
            "Rear Bumper",
            inspection.rear_bumper
        ),

        (
            "Bonnet",
            inspection.bonnet
        ),

        (
            "Roof",
            inspection.roof
        ),

        (
            "Boot",
            inspection.boot
        ),

        (
            "Left Front Door",
            inspection.left_front_door
        ),

        (
            "Right Front Door",
            inspection.right_front_door
        ),

        (
            "Left Rear Door",
            inspection.left_rear_door
        ),

        (
            "Right Rear Door",
            inspection.right_rear_door
        ),

        (
            "Left Front Fender",
            inspection.left_front_fender
        ),

        (
            "Right Front Fender",
            inspection.right_front_fender
        ),

        (
            "Left Rear Fender",
            inspection.left_rear_fender
        ),

        (
            "Right Rear Fender",
            inspection.right_rear_fender
        ),

        (
            "Windscreen",
            inspection.windscreen
        ),

        (
            "Rear Screen",
            inspection.rear_screen
        ),

        (
            "Mirrors",
            inspection.mirrors
        ),

        (
            "Headlights",
            inspection.headlights
        ),

        (
            "Tail Lights",
            inspection.tail_lights
        ),

        (
            "Tyres",
            inspection.tyres
        ),

    ]

    interior_items = [

        (
            "Seats",
            inspection.seats
        ),

        (
            "Dashboard",
            inspection.dashboard
        ),

        (
            "Steering Wheel",
            inspection.steering_wheel
        ),

        (
            "Radio",
            inspection.radio
        ),

        (
            "Infotainment",
            inspection.infotainment
        ),

        (
            "Air Conditioning",
            inspection.aircon
        ),

        (
            "Horn",
            inspection.horn
        ),

        (
            "Interior Lights",
            inspection.interior_lights
        ),

        (
            "Fuel Level",
            inspection.fuel_level
        ),

    ]

    # ==================================================
    # ENGINE COMPARTMENT
    # ==================================================

    engine_items = [

        (
            "Engine Oil",
            inspection.engine_oil
        ),

        (
            "Coolant",
            inspection.coolant
        ),

        (
            "Brake Fluid",
            inspection.brake_fluid
        ),

        (
            "Power Steering Fluid",
            inspection.steering_fluid
        ),

        (
            "Battery",
            inspection.battery
        ),

        (
            "Belts",
            inspection.belts
        ),

        (
            "Oil Leaks",
            inspection.oil_leaks
        ),

        (
            "Coolant Leaks",
            inspection.coolant_leaks
        ),

    ]

    # ==================================================
    # EXTRAS
    # ==================================================

    extras_items = [

        (
            "Spare Wheel",
            boolean_status(
                inspection.spare_wheel
            )
        ),

        (
            "Jack",
            boolean_status(
                inspection.jack
            )
        ),

        (
            "Wheel Spanner",
            boolean_status(
                inspection.wheel_spanner
            )
        ),

        (
            "Toolkit",
            boolean_status(
                inspection.toolkit
            )
        ),

        (
            "Warning Triangle",
            boolean_status(
                inspection.warning_triangle
            )
        ),

        (
            "First Aid Kit",
            boolean_status(
                inspection.first_aid_kit
            )
        ),

        (
            "Fire Extinguisher",
            boolean_status(
                inspection.fire_extinguisher
            )
        ),

    ]

    exterior_table = make_item_table(
        "EXTERIOR",
        exterior_items
    )

    engine_table = make_item_table(
        "ENGINE COMPARTMENT",
        engine_items
    )

    interior_table = make_item_table(
        "INTERIOR",
        interior_items
    )

    extras_table = make_item_table(
        "EXTRAS",
        extras_items
    )

    # Left column: Exterior then Engine
    left_column = Table(
        [
            [exterior_table],
            [Spacer(1, 6)],
            [engine_table],
        ]
    )

    left_column.setStyle(
        TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    # Right column: Interior then Extras
    right_column = Table(
        [
            [interior_table],
            [Spacer(1, 6)],
            [extras_table],
        ]
    )

    right_column.setStyle(
        TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    # Parent table
    main_inspection_table = Table(
        [
            [left_column, right_column]
        ],
        colWidths=[
            88 * mm,
            88 * mm,
        ]
    )

    main_inspection_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ])
    )

    elements.append(main_inspection_table)
    elements.append(Spacer(1, 8))

    # ==================================================
    # COMMENTS
    # ==================================================

    comments_data = [

        [
            Paragraph(
                "<b>GENERAL COMMENTS</b>",
                small_style
            )
        ],

        [
            Paragraph(
                value(
                    inspection.outside_comments
                    or
                    inspection.engine_comments
                    or
                    inspection.interior_comments
                ),
                small_style
            )
        ],

    ]

    comments_table = Table(
        comments_data,
        colWidths=[
            176 * mm
        ],
    )

    comments_table.setStyle(
        TableStyle(
            [

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER,
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    LIGHT_SKY_BLUE,
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),

            ]
        )
    )

    elements.append(
        comments_table
    )

    elements.append(
        Spacer(
            1,
            12
        )
    )

    # ==================================================
    # SIGNATURES
    # ==================================================

    signatures_data = [

        [

            Paragraph(
                "<b>RELEASED BY</b>",
                small_style
            ),

            Paragraph(
                "<b>RECEIVED BY</b>",
                small_style
            ),

        ],

        [

            Paragraph(
                "<br/><br/>"
                "Name: __________________________"
                "<br/>"
                "Tel No: _________________________"
                "<br/>"
                "Date: ___________________________"
                "<br/>"
                "Signature: ______________________",
                small_style
            ),

            Paragraph(
                "<br/><br/>"
                "Name: __________________________"
                "<br/>"
                "Tel No: _________________________"
                "<br/>"
                "Date: ___________________________"
                "<br/>"
                "Signature: ______________________",
                small_style
            ),

        ],

    ]

    signatures_table = Table(
        signatures_data,
        colWidths=[
            88 * mm,
            88 * mm,
        ],
    )

    signatures_table.setStyle(
        TableStyle(
            [

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER,
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    LIGHT_SKY_BLUE,
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),

            ]
        )
    )

    elements.append(
        signatures_table
    )

    # ==================================================
    # VEHICLE PHOTOS
    # ==================================================

    if vehicle.photos:

        elements.append(PageBreak())

        elements.append(
            Paragraph(
                "VEHICLE PHOTOGRAPHS",
                title_style
            )
        )

        elements.append(Spacer(1, 8))

        photo_cells = []
        row = []

        IMAGE_WIDTH = 80 * mm
        IMAGE_HEIGHT = 60 * mm

        for photo in vehicle.photos:

            image_path = os.path.join(
                "static",
                "uploads",
                "vehicles",
                photo.filename
            )

            if os.path.exists(image_path):

                img = Image(image_path)

                img.drawWidth = IMAGE_WIDTH
                img.drawHeight = IMAGE_HEIGHT

                row.append(img)

                if len(row) == 2:
                    photo_cells.append(row)
                    row = []

        if row:
            while len(row) < 2:
                row.append("")
            photo_cells.append(row)

        if photo_cells:

            photo_table = Table(
                photo_cells,
                colWidths=[88 * mm, 88 * mm]
            )

            photo_table.setStyle(
                TableStyle([
                    ("ALIGN", (0,0), (-1,-1), "CENTER"),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 10),
                ])
            )

            elements.append(photo_table)

    # ==================================================
    # BUILD
    # ==================================================

    doc.build(
        elements
    )

    buffer.seek(0)

    return buffer