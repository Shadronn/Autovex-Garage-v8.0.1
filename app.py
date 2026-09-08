from flask import Flask, send_file,jsonify, render_template, request, redirect, url_for, session,flash,abort
from flask_sqlalchemy import SQLAlchemy
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, time
from flask_login import logout_user,login_required, current_user
from sqlalchemy import func
import base64
import os
import uuid
import io
import csv
import pandas as pd
from flask import send_file, Response
from functools import wraps
import pyotp
import qrcode
import io
from pdf.inspection_pdf import generate_inspection_pdf
from flask import send_file  
from  inspection_items import INSPECTION_ITEMS
from pdf.satisfaction_note import generate_satisfaction_note
from pdf.invoice_pdf import generate_invoice_pdf
from flask_migrate import Migrate
from io import BytesIO

from flask import send_file

from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)


# APP CONFIG
# ------------------------------------------------

app = Flask(__name__)
app.secret_key = "Mysecretekey1234"
app.permanent_session_lifetime = timedelta(minutes=10)  # session expires after 10 min of inactivity

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

else:
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "mysql+pymysql://root:@localhost/garage_db"
    )

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "vehicles")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ===================== MODELS =====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120))
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)


class Customer(db.Model):
    __tablename__ = "customer"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    telno = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    customer_class = db.Column(db.String(100))  # ✅ RESTORED
    address = db.Column(db.String(100))
    status = db.Column(db.String(20), default="Active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vehicles = db.relationship(
        "Vehicle",
        backref="customer",
        cascade="all, delete-orphan"
    )


class Vehicle(db.Model):
    __tablename__ = "vehicle"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customer.id"),
        nullable=False
    )
    registration_no = db.Column(db.String(20), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(100), nullable=False)
    yom = db.Column(db.String(10), nullable=False)
    owner = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    photos = db.relationship("VehiclePhoto", backref="vehicle", lazy=True)
    inspection = db.relationship(
    "VehicleInspection",
    backref="vehicle",
    uselist=False,
    cascade="all, delete-orphan"
)
class VehiclePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))
    image_path = db.Column(db.String(255))
    filename = db.Column(db.String(255), nullable=False)  # <--- Add this

class VehicleInspection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"))

    # ---------- OUTSIDE ----------
    front_bumper = db.Column(db.String(30))
    rear_bumper = db.Column(db.String(30))
    bonnet = db.Column(db.String(30))
    roof = db.Column(db.String(30))
    boot = db.Column(db.String(30))

    left_front_door = db.Column(db.String(30))
    right_front_door = db.Column(db.String(30))
    left_rear_door = db.Column(db.String(30))
    right_rear_door = db.Column(db.String(30))

    left_front_fender = db.Column(db.String(30))
    right_front_fender = db.Column(db.String(30))
    left_rear_fender = db.Column(db.String(30))
    right_rear_fender = db.Column(db.String(30))

    windscreen = db.Column(db.String(30))
    rear_screen = db.Column(db.String(30))
    mirrors = db.Column(db.String(30))

    headlights = db.Column(db.String(30))
    tail_lights = db.Column(db.String(30))

    tyres = db.Column(db.String(30))

    outside_comments = db.Column(db.Text)

    # ---------- ENGINE ----------
    engine_oil = db.Column(db.String(30))
    coolant = db.Column(db.String(30))
    brake_fluid = db.Column(db.String(30))
    steering_fluid = db.Column(db.String(30))

    battery = db.Column(db.String(30))
    belts = db.Column(db.String(30))

    oil_leaks = db.Column(db.String(30))
    coolant_leaks = db.Column(db.String(30))

    engine_comments = db.Column(db.Text)

    # ---------- INTERIOR ----------
    seats = db.Column(db.String(30))
    dashboard = db.Column(db.String(30))
    steering_wheel = db.Column(db.String(30))
    infotainment = db.Column(db.String(30))
    radio = db.Column(db.String(30))
    aircon = db.Column(db.String(30))
    horn = db.Column(db.String(30))
    interior_lights = db.Column(db.String(30))

    fuel_level = db.Column(db.String(20))

    interior_comments = db.Column(db.Text)

    # ---------- ACCESSORIES ----------
    spare_wheel = db.Column(db.Boolean)
    jack = db.Column(db.Boolean)
    wheel_spanner = db.Column(db.Boolean)
    toolkit = db.Column(db.Boolean)
    fire_extinguisher = db.Column(db.Boolean)
    warning_triangle = db.Column(db.Boolean)
    first_aid_kit = db.Column(db.Boolean)
from datetime import datetime

class Jobs(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customer.id"),
        nullable=False
    )

    customer_name = db.Column(
        db.String(100),
        nullable=False
    )

    vehicle_id = db.Column(
        db.Integer,
        db.ForeignKey("vehicle.id"),
        nullable=False
    )

    telno = db.Column(
        db.String(20),
        nullable=False
    )

    vehicle = db.Column(
        db.String(100),
        nullable=False
    )

    vehicle_model = db.Column(
        db.String(100),
        nullable=False
    )

    # -------------------------------------------------
    # SERVICE TYPE
    # -------------------------------------------------

    service_type = db.Column(
        db.String(100),
        nullable=False,
        default="General Repairs"
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="Open"
    )

    assigned_to = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    deadline = db.Column(
        db.DateTime
    )

    mechanic = db.relationship(
        "User",
        foreign_keys=[assigned_to]
    )

    invoice = db.relationship(
        "Invoice",
        backref="job",
        uselist=False,
        cascade="all, delete-orphan"
    )
class JobCard(db.Model):
    __tablename__ = "job_card"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id"),
        nullable=False,
        unique=True
    )

    # Relationship to Jobs
    job = db.relationship(
        "Jobs",
        backref=db.backref(
            "job_card",
            uselist=False,
            cascade="all, delete-orphan"
        )
    )

    job_card_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    work_description = db.Column(
        db.Text
    )

    technician_notes = db.Column(
        db.Text
    )

    completion_notes = db.Column(
        db.Text
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Open"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    completed_at = db.Column(
        db.DateTime
    )

    parts = db.relationship(
        "JobCardPart",
        back_populates="job_card",
        cascade="all, delete-orphan"
    )

    labour_items = db.relationship(
        "JobCardLabour",
        back_populates="job_card",
        cascade="all, delete-orphan"
    )
class JobCardPart(db.Model):
    __tablename__ = "job_card_part"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    job_card_id = db.Column(
        db.Integer,
        db.ForeignKey("job_card.id"),
        nullable=False
    )

    part_name = db.Column(
        db.String(150),
        nullable=False
    )

    part_number = db.Column(
        db.String(100)
    )

    quantity = db.Column(
        db.Float,
        nullable=False,
        default=1
    )

    unit_price = db.Column(
        db.Float,
        nullable=False,
        default=0
    )
    unit_cost = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    cost_total = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    total = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    notes = db.Column(
        db.Text
    )

    job_card = db.relationship(
        "JobCard",
        back_populates="parts"
    )
class JobCardLabour(db.Model):
    __tablename__ = "job_card_labour"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    job_card_id = db.Column(
        db.Integer,
        db.ForeignKey("job_card.id"),
        nullable=False
    )

    description = db.Column(
        db.String(200),
        nullable=False
    )

    hours = db.Column(
        db.Float,
        nullable=False,
        default=1
    )

    # ACTUAL LABOUR COST
    hourly_cost = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    # CUSTOMER CHARGE
    hourly_rate = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    # ACTUAL LABOUR COST
    cost_total = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    # CUSTOMER CHARGE
    total = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    notes = db.Column(
        db.Text
    )

    job_card = db.relationship(
        "JobCard",
        back_populates="labour_items"
    )
class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id"),
        nullable=False
    )

    invoice_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    issue_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    due_date = db.Column(
        db.DateTime
    )

    subtotal = db.Column(
        db.Float,
        nullable=False
    )

    tax_rate = db.Column(
        db.Float,
        nullable=False,
        default=16.0
    )

    tax_amount = db.Column(
        db.Float,
        nullable=False
    )

    total_amount = db.Column(
        db.Float,
        nullable=False
    )

    # Total amount paid so far
    amount = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    # Amount still outstanding
    Balance = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Unpaid"
    )

    notes = db.Column(
        db.Text
    )

    # -------------------------------------------------
    # EXISTING PAYMENT FIELDS
    # -------------------------------------------------
    # Keep these for now so existing data is preserved.

    payment_method = db.Column(
        db.String(120)
    )

    payment_reference = db.Column(
        db.String(120)
    )

    payment_proof = db.Column(
        db.String(200)
    )

    paid_at = db.Column(
        db.DateTime
    )

    # -------------------------------------------------
    # NEW: MULTIPLE PAYMENTS
    # -------------------------------------------------

    payments = db.relationship(
        "Payment",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="Payment.paid_at"
    )

    items = db.relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceItem.id"
    )

class InvoiceItem(db.Model):
    __tablename__ = "invoice_item"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey("invoice.id"),
        nullable=False
    )

    description = db.Column(
        db.String(255),
        nullable=False
    )

    # What kind of item was sold
    item_type = db.Column(
        db.String(50),
        nullable=False
    )

    # P&L revenue classification
    revenue_category = db.Column(
        db.String(100),
        nullable=False
    )

    quantity = db.Column(
        db.Float,
        nullable=False,
        default=1
    )

    unit_price = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    total = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    # Actual cost to Autovex
    unit_cost = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    cost_total = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    invoice = db.relationship(
        "Invoice",
        back_populates="items"
    )

class Payment(db.Model):
    __tablename__ = "payment"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey("invoice.id"),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    payment_method = db.Column(
        db.String(120),
        nullable=False
    )

    payment_reference = db.Column(
        db.String(120)
    )

    payment_proof = db.Column(
        db.String(200)
    )

    paid_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    receipt_number = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    notes = db.Column(
        db.Text
    )

    invoice = db.relationship(
        "Invoice",
        back_populates="payments"
    )
class Company(db.Model):
    __tablename__ = "company"

    id = db.Column(db.Integer, primary_key=True)

    company_name = db.Column(db.String(150), nullable=False)
    tagline = db.Column(db.String(150))

    address = db.Column(db.String(200))
    city = db.Column(db.String(100))

    phone = db.Column(db.String(50))
    alternate_phone = db.Column(db.String(50))

    email = db.Column(db.String(120))
    website = db.Column(db.String(120))

    kra_pin = db.Column(db.String(50))
    vat_number = db.Column(db.String(50))
    etims_branch = db.Column(db.String(50))

    bank_name = db.Column(db.String(100))
    account_name = db.Column(db.String(100))
    account_number = db.Column(db.String(100))
    currency = db.Column(db.String(10), default="KES")

    logo = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# =========================================================
# FINANCIALS MODELS
# =========================================================
class Expense(db.Model):
    __tablename__ = "expense"

    id = db.Column(db.Integer, primary_key=True)

    expense_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    expense_date = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    description = db.Column(
        db.String(255),
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    reference = db.Column(
        db.String(120)
    )

    payment_method = db.Column(
        db.String(120)
    )

    amount = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Pending"
    )

    notes = db.Column(
        db.Text
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user = db.relationship(
        "User",
        foreign_keys=[created_by]
    )


class Supplier(db.Model):
    __tablename__ = "supplier"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    supplier_name = db.Column(
        db.String(150),
        nullable=False
    )

    contact_person = db.Column(
        db.String(150)
    )

    phone = db.Column(
        db.String(50)
    )

    email = db.Column(
        db.String(120)
    )

    address = db.Column(
        db.String(255)
    )

    tax_pin = db.Column(
        db.String(50)
    )

    status = db.Column(
        db.String(30),
        default="Active",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    bills = db.relationship(
        "SupplierBill",
        back_populates="supplier",
        cascade="all, delete-orphan"
    )

    purchase_orders = db.relationship(
        "PurchaseOrder",
        back_populates="supplier",
        cascade="all, delete-orphan"
    )


class SupplierBill(db.Model):
    __tablename__ = "supplier_bill"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier.id"),
        nullable=False
    )

    bill_number = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    bill_date = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    due_date = db.Column(
        db.DateTime
    )

    description = db.Column(
        db.String(255)
    )

    amount = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    amount_paid = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    balance = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Unpaid"
    )

    notes = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    supplier = db.relationship(
        "Supplier",
        back_populates="bills"
    )

    payments = db.relationship(
        "SupplierPayment",
        back_populates="bill",
        cascade="all, delete-orphan",
        order_by="SupplierPayment.paid_at"
    )


class SupplierPayment(db.Model):
    __tablename__ = "supplier_payment"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    supplier_bill_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_bill.id"),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    payment_method = db.Column(
        db.String(120),
        nullable=False
    )

    # Internal payment document/reference generated by our system
    payment_reference = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    # M-Pesa / bank / cheque / EFT reference
    external_reference = db.Column(
        db.String(120)
    )

    # Receipt number issued by the supplier
    receipt_number = db.Column(
        db.String(100),
        unique=True,
        nullable=True
    )

    payment_proof = db.Column(
        db.String(255)
    )

    paid_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    notes = db.Column(
        db.Text
    )

    bill = db.relationship(
        "SupplierBill",
        back_populates="payments"
    )

class PurchaseOrder(db.Model):
    __tablename__ = "purchase_order"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier.id"),
        nullable=False
    )

    lpo_number = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    order_date = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    expected_date = db.Column(
        db.DateTime
    )

    description = db.Column(
        db.String(255)
    )

    total_amount = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Draft"
    )

    notes = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    supplier = db.relationship(
        "Supplier",
        back_populates="purchase_orders"
    )

    items = db.relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderItem.id"
    )

    goods_receipts = db.relationship(
        "GoodsReceipt",
        back_populates="purchase_order",
        cascade="all, delete-orphan"
    )

class PurchaseOrderItem(db.Model):
    __tablename__ = "purchase_order_item"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    purchase_order_id = db.Column(
        db.Integer,
        db.ForeignKey("purchase_order.id"),
        nullable=False
    )

    item_description = db.Column(
        db.String(255),
        nullable=False
    )

    quantity = db.Column(
        db.Float,
        nullable=False,
        default=1.0
    )

    unit_price = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    total_price = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    notes = db.Column(
        db.Text
    )

    purchase_order = db.relationship(
        "PurchaseOrder",
        back_populates="items"
    )
    goods_receipt_items = db.relationship(
        "GoodsReceiptItem",
        back_populates="purchase_order_item"
    )

class GoodsReceipt(db.Model):
    __tablename__ = "goods_receipt"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    purchase_order_id = db.Column(
        db.Integer,
        db.ForeignKey("purchase_order.id"),
        nullable=False
    )

    grn_number = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    received_date = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    received_by = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Received"
    )

    notes = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    purchase_order = db.relationship(
        "PurchaseOrder",
        back_populates="goods_receipts"
    )

    items = db.relationship(
        "GoodsReceiptItem",
        back_populates="goods_receipt",
        cascade="all, delete-orphan"
    )

    received_by_user = db.relationship(
        "User",
        foreign_keys=[received_by]
    )


class GoodsReceiptItem(db.Model):
    __tablename__ = "goods_receipt_item"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    goods_receipt_id = db.Column(
        db.Integer,
        db.ForeignKey("goods_receipt.id"),
        nullable=False
    )

    purchase_order_item_id = db.Column(
        db.Integer,
        db.ForeignKey("purchase_order_item.id"),
        nullable=False
    )

    quantity_received = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    notes = db.Column(
        db.Text
    )

    goods_receipt = db.relationship(
        "GoodsReceipt",
        back_populates="items"
    )

    purchase_order_item = db.relationship(
        "PurchaseOrderItem",
        back_populates="goods_receipt_items"
    )

class ExpenseApproval(db.Model):
    __tablename__ = "expense_approval"

    id = db.Column(db.Integer, primary_key=True)

    expense_id = db.Column(
        db.Integer,
        db.ForeignKey("expense.id"),
        nullable=False
    )

    action = db.Column(
        db.String(30),
        nullable=False
    )

    reason = db.Column(db.Text)

    performed_by = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    performed_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    expense = db.relationship(
        "Expense",
        backref=db.backref(
            "approval_history",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    user = db.relationship(
        "User",
        foreign_keys=[performed_by]
    )

class FinancialReport(db.Model):
    __tablename__ = "financial_report"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    report_type = db.Column(
        db.String(100),
        nullable=False
    )

    period_start = db.Column(
        db.DateTime,
        nullable=False
    )

    period_end = db.Column(
        db.DateTime,
        nullable=False
    )

    accounting_basis = db.Column(
        db.String(30),
        nullable=False,
        default="Accrual"
    )

    format = db.Column(
        db.String(30),
        nullable=False,
        default="PDF"
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Generated"
    )

    file_path = db.Column(
        db.String(255)
    )

    generated_by = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    generated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user = db.relationship(
        "User",
        foreign_keys=[generated_by]
    )
# ===================== INIT =====================
def init_db():
    db.create_all()

    if not User.query.first():
        users = [
            User(username="superadmin",
                 password=generate_password_hash("superadmin"),
                 role="superadmin"),

            User(username="admin",
                 password=generate_password_hash("admin"),
                 role="admin"),

            User(username="accounts",
                 password=generate_password_hash("accounts"),
                 role="accounts"),

            User(username="mechanic",
                 password=generate_password_hash("mechanic"),
                 role="mechanic"),
        ]

        db.session.add_all(users)

    if not Company.query.first():

        company = Company(
            company_name="Hillance Enterprises",
            tagline="Professional Vehicle Service Centre",

            address="P.O Box 1234-00100, Nairobi",

            city="Nairobi",

            phone="0723523109",

            alternate_phone="0783644648",

            email="info@hillance.com",

            website="www.hillance.com",

            kra_pin="P051234567A",

            vat_number="VAT123456",

            etims_branch="001",

            bank_name="I&M Bank",

            account_name="Hillance Enterprises",

            account_number="00207958476150",

            currency="KES",

            logo="assets/images/logo.png"
        )

        db.session.add(company)

    db.session.commit()
    
with app.app_context():
    init_db()

#========   =========helpers==================

def require_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user" not in session or session.get("role") not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# ===================== PAYMENT HELPERS =====================
def generate_invoice_number():
    date_part = datetime.utcnow().strftime("%Y%m%d")

    last_invoice = Invoice.query.order_by(
        Invoice.id.desc()
    ).first()

    next_id = (
        last_invoice.id + 1
        if last_invoice
        else 1
    )

    return f"INV-{date_part}-{next_id:05d}"

def generate_receipt_number(invoice_id):
    date_part = datetime.utcnow().strftime("%Y%m%d")
    random_part = uuid.uuid4().hex[:6].upper()

    return f"RCT-{date_part}-{invoice_id:05d}-{random_part}"

def generate_job_card_number():
    date_part = datetime.utcnow().strftime("%Y%m%d")
    random_part = uuid.uuid4().hex[:6].upper()

    return f"JC-{date_part}-{random_part}"

def generate_expense_number():
    date_part = datetime.utcnow().strftime("%Y%m%d")

    last_expense = (
        Expense.query
        .order_by(Expense.id.desc())
        .first()
    )

    next_id = (
        last_expense.id + 1
        if last_expense
        else 1
    )

    return f"EXP-{date_part}-{next_id:05d}"

def calculate_invoice_payment_status(invoice):
    """
    Recalculate total paid, balance and invoice status
    from all Payment records.
    """

    total_paid = sum(
        float(payment.amount or 0)
        for payment in invoice.payments
    )

    total_amount = float(invoice.total_amount or 0)

    balance = max(total_amount - total_paid, 0)

    invoice.amount = total_paid
    invoice.Balance = balance

    if total_paid <= 0:
        invoice.status = "Unpaid"
        invoice.paid_at = None

    elif total_paid < total_amount:
        invoice.status = "Partially Paid"
        invoice.paid_at = None

    else:
        invoice.status = "Paid"

        paid_dates = [
            payment.paid_at
            for payment in invoice.payments
            if payment.paid_at
        ]

        invoice.paid_at = max(paid_dates) if paid_dates else datetime.utcnow()

    return invoice


# ===================== AUTH =====================

@app.route("/")
def start():
    return render_template("start.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session.clear()
            session.permanent = True
            session["user_id"] = user.id
            session["user"] = user.username
            session["role"] = user.role
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/verify-2fa", methods=["GET", "POST"])
def verify_2fa():
    if request.method == "POST":
        otp = request.form.get("otp")
        user = User.query.get(session["login_user_id"])

        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(otp):
            # OTP correct → finalize login
            session["user_id"] = user.id
            session["user"] = user.username
            session["role"] = user.role
            session.pop("needs_2fa", None)
            session.pop("login_user_id", None)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid 2FA code", "danger")

    return render_template("verify_2fa.html")

# ================= SESSION ACTIVITY TRACKER =================

@app.before_request
def session_management():

    allowed_routes = ["login", "start", "static"]

    # If logged in → refresh session expiry
    if "user" in session:
        session.permanent = True

    # If not logged in → protect routes
    elif request.endpoint not in allowed_routes:
        return redirect(url_for("login"))

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

def get_dashboard_financials():
    # -----------------------------------------
    # REVENUE
    # Actual money received from payments
    # -----------------------------------------
    revenue = (
        db.session.query(
            func.coalesce(func.sum(Payment.amount), 0)
        )
        .scalar()
        or 0
    )

    # -----------------------------------------
    # DEBT
    # Outstanding balance on all invoices
    # -----------------------------------------
    debt = (
        db.session.query(
            func.coalesce(func.sum(Invoice.Balance), 0)
        )
        .filter(Invoice.Balance > 0)
        .scalar()
        or 0
    )

    # -----------------------------------------
    # PENDING
    # Completed jobs without an invoice
    # -----------------------------------------
    pending_invoices = (
        Jobs.query
        .outerjoin(Invoice, Invoice.job_id == Jobs.id)
        .filter(
            Jobs.status == "Complete",
            Invoice.id == None
        )
        .count()
    )

    # -----------------------------------------
    # OVERDUE
    # Invoices with outstanding balance
    # older than 30 days
    # -----------------------------------------
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    overdue_invoices = (
        Invoice.query
        .filter(
            Invoice.Balance > 0,
            Invoice.issue_date <= thirty_days_ago
        )
        .count()
    )

    return {
        "revenue": float(revenue),
        "debt": float(debt),
        "pending_invoices": pending_invoices,
        "overdue_invoices": overdue_invoices
    }

# ===================== DASHBOARD =====================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    role = session.get("role")

    if role == "superadmin":
        return redirect(url_for("superadmin_dashboard"))
    elif role == "admin":
        return redirect(url_for("admin_dashboard"))
    elif role == "accounts":
        return redirect(url_for("accounts_dashboard"))
    else:
        abort(403)
        
@app.route("/dashboard/admin")
def admin_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    role = session["role"]

    if role == "admin":
        total_jobs = Jobs.query.count()
        open_jobs = Jobs.query.filter_by(status="Open").count()
        completed_jobs = Jobs.query.filter_by(status="Complete").count()

        # 💰 Revenue - actual payments received
        revenue = (
            db.session.query(
                func.coalesce(func.sum(Payment.amount), 0)
            )
            .scalar()
            or 0
        )

        # 📉 Debt - total outstanding balances
        debt = (
            db.session.query(
                func.coalesce(func.sum(Invoice.Balance), 0)
            )
            .filter(Invoice.Balance > 0)
            .scalar()
            or 0
        )

        # ⏳ Pending - completed jobs that don't have an invoice yet
        pending_amount = 0

        completed_jobs_list = Jobs.query.filter_by(
            status="Complete"
        ).all()

        for job in completed_jobs_list:
            if not job.invoice and job.job_card:
                parts_total = sum(
                    float(part.total or 0)
                    for part in job.job_card.parts
                )

                labour_total = sum(
                    float(labour.total or 0)
                    for labour in job.job_card.labour_items
                )

                subtotal = parts_total + labour_total
                tax = subtotal * 0.16

                pending_amount += subtotal + tax

        # 📅 +30 Days - outstanding invoices older than 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)

        overdue_amount = (
            db.session.query(
                func.coalesce(func.sum(Invoice.Balance), 0)
            )
            .filter(
                Invoice.Balance > 0,
                Invoice.issue_date <= thirty_days_ago
            )
            .scalar()
            or 0
        )

        now = datetime.now()

        return render_template(
            "admin/dashboard.html",
            user=session["user"],
            role=role,
            total_jobs=total_jobs,
            open_jobs=open_jobs,
            completed_jobs=completed_jobs,
            revenue=revenue,
            debt=debt,
            pending_amount=pending_amount,
            overdue_amount=overdue_amount,
            now=now
        )
        
@app.route("/dashboard/superadmin")
def superadmin_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    role = session["role"]

    if role == "superadmin":
        total_jobs = Jobs.query.count()
        open_jobs = Jobs.query.filter_by(status="Open").count()
        completed_jobs = Jobs.query.filter_by(status="Complete").count()

        # 💰 Revenue (Paid invoices)
        revenue = (
            db.session.query(func.coalesce(func.sum(Invoice.total_amount), 0))
            .filter(Invoice.status == "Paid")
            .scalar()
        )

        # 📉 Debt (Unpaid invoices)
        debt = (
            db.session.query(func.coalesce(func.sum(Invoice.total_amount), 0))
            .filter(Invoice.status == "Unpaid")
            .scalar()
        )

        now = datetime.now()   # ✅ current date and time

        return render_template(
            "admin/dashboard.html",
            user=session["user"],
            role=role,
            total_jobs=total_jobs,
            open_jobs=open_jobs,
            completed_jobs=completed_jobs,
            revenue=revenue,
            debt=debt,
            now=now
        )
@app.route("/financials")
@require_roles("admin", "accounts", "superadmin")
def financials():

    # =====================================================
    # BASIC FINANCIAL TOTALS
    # =====================================================

    revenue = (
        db.session.query(
            func.coalesce(func.sum(Payment.amount), 0)
        )
        .scalar()
    ) or 0

    expenses = (
        db.session.query(
            func.coalesce(func.sum(Expense.amount), 0)
        )
        .filter(
            Expense.status.in_(["Approved", "Paid"])
        )
        .scalar()
    ) or 0

    outstanding_debt = (
        db.session.query(
            func.coalesce(func.sum(Invoice.Balance), 0)
        )
        .filter(
            Invoice.Balance > 0
        )
        .scalar()
    ) or 0

    creditors = (
        db.session.query(
            func.coalesce(func.sum(SupplierBill.balance), 0)
        )
        .filter(
            SupplierBill.balance > 0
        )
        .scalar()
    ) or 0

    net_position = float(revenue) - float(expenses)


    # =====================================================
    # RECENT CUSTOMER PAYMENTS
    # =====================================================

    recent_payments = (
        Payment.query
        .order_by(Payment.paid_at.desc())
        .limit(10)
        .all()
    )


    # =====================================================
    # RECENT SUPPLIER PAYMENTS
    # =====================================================

    recent_supplier_payments = (
        SupplierPayment.query
        .order_by(SupplierPayment.paid_at.desc())
        .limit(10)
        .all()
    )


    # =====================================================
    # EXPENSE RECORDS
    # =====================================================

    expenses_list = (
        Expense.query
        .order_by(Expense.expense_date.desc())
        .limit(10)
        .all()
    )

    recent_expenses = expenses_list


    # =====================================================
    # COUNTS
    # =====================================================

    expense_count = Expense.query.count()

    supplier_count = Supplier.query.count()

    outstanding_invoice_count = (
        Invoice.query
        .filter(Invoice.Balance > 0)
        .count()
    )

    outstanding_bill_count = (
        SupplierBill.query
        .filter(SupplierBill.balance > 0)
        .count()
    )


    # =====================================================
    # EXPENSE SUMMARY
    # =====================================================

    today = datetime.now()

    # Start of current month
    month_start = today.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    # Total expenses this month
    expense_this_month = (
        db.session.query(
            func.coalesce(func.sum(Expense.amount), 0)
        )
        .filter(
            Expense.expense_date >= month_start
        )
        .scalar()
    ) or 0


    # Pending expenses
    pending_expenses = (
        db.session.query(
            func.coalesce(func.sum(Expense.amount), 0)
        )
        .filter(
            Expense.status == "Pending"
        )
        .scalar()
    ) or 0


    # Approved expenses
    approved_expenses = (
        db.session.query(
            func.coalesce(func.sum(Expense.amount), 0)
        )
        .filter(
            Expense.status == "Approved"
        )
        .scalar()
    ) or 0


    # =====================================================
    # TOTAL EXPENSES THIS YEAR
    # =====================================================

    year_start = today.replace(
        month=1,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    total_expenses_year = (
        db.session.query(
            func.coalesce(func.sum(Expense.amount), 0)
        )
        .filter(
            Expense.expense_date >= year_start
        )
        .scalar()
    ) or 0


    # =====================================================
    # EXPENSE CATEGORIES
    # =====================================================

    expense_categories = (
        db.session.query(
            Expense.category,
            func.coalesce(
                func.sum(Expense.amount),
                0
            ).label("total")
        )
        .filter(
            Expense.status.in_(["Approved", "Paid"])
        )
        .group_by(
            Expense.category
        )
        .order_by(
            func.sum(Expense.amount).desc()
        )
        .all()
    )
    # =========================================================
    # DEBTORS
    # =========================================================

    today = datetime.now().date()

    debtor_invoices = []

    total_debtors = 0
    total_outstanding = 0
    current_amount = 0
    days_31_60_amount = 0
    days_61_90_amount = 0
    days_90_plus_amount = 0


    # Get invoices together with their jobs/customers
    debtor_query = (
        db.session.query(Invoice, Jobs)
        .join(Jobs, Invoice.job_id == Jobs.id)
        .order_by(Invoice.due_date.asc())
        .all()
    )


    for invoice, job in debtor_query:

        # -----------------------------------------------------
        # Calculate amount paid
        # -----------------------------------------------------

        total_amount = float(invoice.total_amount or 0)
        amount_paid = float(invoice.amount or 0)

        balance = total_amount - amount_paid

        # Protect against tiny negative balances
        if balance < 0:
            balance = 0


        # -----------------------------------------------------
        # Only invoices with outstanding balances are debtors
        # -----------------------------------------------------

        if balance <= 0:
            continue


        total_debtors += 1
        total_outstanding += balance


        # -----------------------------------------------------
        # Determine aging
        # -----------------------------------------------------

        due_date = invoice.due_date.date() if invoice.due_date else None

        if due_date:

            days_overdue = (today - due_date).days

            if days_overdue <= 0:

                aging = "Current"
                current_amount += balance

            elif days_overdue <= 30:

                aging = "1–30 Days"
                current_amount += balance

            elif days_overdue <= 60:

                aging = "31–60 Days"
                days_31_60_amount += balance

            elif days_overdue <= 90:

                aging = "61–90 Days"
                days_61_90_amount += balance

            else:

                aging = "90+ Days"
                days_90_plus_amount += balance

        else:

            days_overdue = 0
            aging = "Current"
            current_amount += balance


        # -----------------------------------------------------
        # Status
        # -----------------------------------------------------

        if amount_paid <= 0:

            debtor_status = "Unpaid"

        elif balance > 0:

            debtor_status = "Partial"

        else:

            debtor_status = "Paid"


        # -----------------------------------------------------
        # Add debtor record
        # -----------------------------------------------------

        debtor_invoices.append({

            "invoice": invoice,

            "job": job,

            "customer_name": (
                job.customer_name
                if job.customer_name
                else "Unknown Customer"
            ),

            "invoice_number": (
                invoice.invoice_number
                or f"INV-{invoice.id}"
            ),

            "invoice_date": invoice.issue_date,

            "due_date": invoice.due_date,

            "total_amount": total_amount,

            "amount_paid": amount_paid,

            "balance": balance,

            "days_overdue": max(days_overdue, 0),

            "aging": aging,

            "status": debtor_status

        })


    # ---------------------------------------------------------
    # Total overdue
    # ---------------------------------------------------------

    total_overdue = (
        days_31_60_amount
        + days_61_90_amount
        + days_90_plus_amount
    )

    # =========================================================
    # CREDITORS
    # =========================================================

    today = datetime.now().date()

    creditor_bills = []

    total_creditors = 0
    total_payables = 0
    creditor_current_amount = 0
    creditor_1_30_amount = 0
    creditor_31_60_amount = 0
    creditor_61_90_amount = 0
    creditor_90_plus_amount = 0
    creditor_overdue = 0
    creditor_due_soon = 0


    # ---------------------------------------------------------
    # Get outstanding supplier bills
    # ---------------------------------------------------------

    creditor_query = (
        SupplierBill.query
        .filter(
            SupplierBill.balance > 0
        )
        .order_by(
            SupplierBill.due_date.asc()
        )
        .all()
    )


    for bill in creditor_query:

        balance = float(
            bill.balance or 0
        )

        if balance <= 0:
            continue

        total_creditors += 1
        total_payables += balance

        # -----------------------------------------------------
        # Supplier
        # -----------------------------------------------------

        supplier_name = (
            bill.supplier.supplier_name
            if bill.supplier
            else "Unknown Supplier"
        )

        # -----------------------------------------------------
        # Aging
        # -----------------------------------------------------

        due_date = (
            bill.due_date.date()
            if bill.due_date
            and hasattr(bill.due_date, "date")
            else bill.due_date
        )

        days_overdue = 0

        if due_date:

            days_difference = (
                today - due_date
            ).days

            if days_difference <= 0:

                aging = "Current"

                creditor_current_amount += balance

                # Due within the next 7 days
                days_until_due = (
                    due_date - today
                ).days

                if 0 <= days_until_due <= 7:
                    creditor_due_soon += balance

            elif days_difference <= 30:

                aging = "1–30 Days"

                creditor_1_30_amount += balance
                creditor_overdue += balance
                days_overdue = days_difference

            elif days_difference <= 60:

                aging = "31–60 Days"

                creditor_31_60_amount += balance
                creditor_overdue += balance
                days_overdue = days_difference

            elif days_difference <= 90:

                aging = "61–90 Days"

                creditor_61_90_amount += balance
                creditor_overdue += balance
                days_overdue = days_difference

            else:

                aging = "90+ Days"

                creditor_90_plus_amount += balance
                creditor_overdue += balance
                days_overdue = days_difference

        else:

            aging = "No Due Date"

            creditor_current_amount += balance


        # -----------------------------------------------------
        # Payment status
        # -----------------------------------------------------

        amount_paid = float(
            bill.amount_paid or 0
        )

        if amount_paid <= 0:

            bill_status = "Unpaid"

        elif balance > 0:

            bill_status = "Partial"

        else:

            bill_status = "Paid"


        # -----------------------------------------------------
        # Add creditor record
        # -----------------------------------------------------

        creditor_bills.append({

            "bill": bill,

            "supplier_name": supplier_name,

            "bill_number": (
                bill.bill_number
                or f"BILL-{bill.id}"
            ),

            "bill_date": bill.bill_date,

            "due_date": bill.due_date,

            "amount": float(
                bill.amount or 0
            ),

            "amount_paid": amount_paid,

            "balance": balance,

            "days_overdue": days_overdue,

            "aging": aging,

            "status": bill_status

        })


    # ---------------------------------------------------------
    # Creditor aging totals
    # ---------------------------------------------------------

    creditor_total_overdue = (
        creditor_1_30_amount
        + creditor_31_60_amount
        + creditor_61_90_amount
        + creditor_90_plus_amount
    )

        # =====================================================
    # FINANCIAL PAYMENT RECORDS
    # =====================================================

    financial_payment_records = []

    # -----------------------------------------------------
    # CUSTOMER PAYMENTS
    # -----------------------------------------------------

    customer_payment_query = (
        db.session.query(Payment, Invoice, Jobs)
        .join(
            Invoice,
            Payment.invoice_id == Invoice.id
        )
        .join(
            Jobs,
            Invoice.job_id == Jobs.id
        )
        .order_by(
            Payment.paid_at.asc(),
            Payment.id.asc()
        )
        .all()
    )

    # Keep track of payments separately for each invoice
    invoice_paid_so_far = {}

    for payment, invoice, job in customer_payment_query:

        invoice_id = invoice.id

        previous_paid = invoice_paid_so_far.get(
            invoice_id,
            0.0
        )

        payment_amount = float(
            payment.amount or 0
        )

        total_amount = float(
            invoice.total_amount or 0
        )

        paid_after_payment = (
            previous_paid
            + payment_amount
        )

        balance_after_payment = max(
            total_amount - paid_after_payment,
            0
        )

        invoice_paid_so_far[invoice_id] = (
            paid_after_payment
        )

        financial_payment_records.append({

            "date": payment.paid_at,

            "reference": (
                payment.payment_reference
                or payment.receipt_number
                or f"PAY-{payment.id}"
            ),

            "party": (
                job.customer_name
                or "Unknown Customer"
            ),

            "type": "Customer Payment",

            "method": (
                payment.payment_method
                or "—"
            ),

            "amount": payment_amount,

            "balance": balance_after_payment,

            "status": "Completed",

            "invoice_id": invoice.id,

            "bill_id": None

        })


        # -----------------------------------------------------
    # SUPPLIER PAYMENTS
    # -----------------------------------------------------

    supplier_payment_query = (
        db.session.query(
            SupplierPayment,
            SupplierBill,
            Supplier
        )
        .join(
            SupplierBill,
            SupplierPayment.supplier_bill_id
            == SupplierBill.id
        )
        .join(
            Supplier,
            SupplierBill.supplier_id
            == Supplier.id
        )
        .order_by(
            SupplierPayment.paid_at.asc(),
            SupplierPayment.id.asc()
        )
        .all()
    )

    # Keep track of supplier payments separately
    supplier_paid_so_far = {}

    for payment, bill, supplier in supplier_payment_query:

        bill_id = bill.id

        previous_paid = supplier_paid_so_far.get(
            bill_id,
            0.0
        )

        payment_amount = float(
            payment.amount or 0
        )

        bill_amount = float(
            bill.amount or 0
        )

        paid_after_payment = (
            previous_paid
            + payment_amount
        )

        balance_after_payment = max(
            bill_amount - paid_after_payment,
            0
        )

        supplier_paid_so_far[bill_id] = (
            paid_after_payment
        )

        financial_payment_records.append({

            "date": payment.paid_at,

            "reference": (
                payment.payment_reference
                or payment.receipt_number
                or f"SP-{payment.id}"
            ),

            "party": (
                supplier.supplier_name
                or "Unknown Supplier"
            ),

            "type": "Supplier Payment",

            "method": (
                payment.payment_method
                or "—"
            ),

            "amount": payment_amount,

            "balance": balance_after_payment,

            "status": "Completed",

            "invoice_id": None,

            "bill_id": bill.id

        })
    # -----------------------------------------------------
    # SORT COMBINED PAYMENTS
    # -----------------------------------------------------

    financial_payment_records.sort(

        key=lambda payment: (
            payment["date"]
            or datetime.min
        ),

        reverse=True

    )


    # =====================================================
    # PAYMENT SUMMARY
    # =====================================================

    payment_money_in = sum(

        payment["amount"]

        for payment in financial_payment_records

        if payment["type"]
        == "Customer Payment"

    )


    payment_money_out = sum(

        payment["amount"]

        for payment in financial_payment_records

        if payment["type"]
        == "Supplier Payment"

    )


    payment_net_movement = (
        payment_money_in
        - payment_money_out
    )


    payment_transaction_count = len(
        financial_payment_records
    )
    # =====================================================
    # RENDER FINANCIALS
    # =====================================================

    return render_template(
        "financials.html",

        # Financial totals
        revenue=revenue,
        expenses=expenses,
        outstanding_debt=outstanding_debt,
        creditors=creditors,
        net_position=net_position,

        # Payments
        recent_payments=recent_payments,
        recent_supplier_payments=recent_supplier_payments,

        # Counts
        expense_count=expense_count,
        supplier_count=supplier_count,
        outstanding_invoice_count=outstanding_invoice_count,
        outstanding_bill_count=outstanding_bill_count,

        # Expense data
        expenses_list=expenses_list,
        recent_expenses=recent_expenses,
        expense_this_month=expense_this_month,
        pending_expenses=pending_expenses,
        approved_expenses=approved_expenses,
        total_expenses_year=total_expenses_year,
        expense_categories=expense_categories,

        # Debtor data
        total_debtors=total_debtors,
        total_outstanding=total_outstanding,
        current_amount=current_amount,
        days_31_60_amount=days_31_60_amount,
        days_61_90_amount=days_61_90_amount,
        days_90_plus_amount=days_90_plus_amount,
        total_overdue=total_overdue,
        debtor_invoices=debtor_invoices,

        # Creditor data
        total_creditors=total_creditors,
        total_payables=total_payables,
        creditor_current_amount=creditor_current_amount,
        creditor_1_30_amount=creditor_1_30_amount,
        creditor_31_60_amount=creditor_31_60_amount,
        creditor_61_90_amount=creditor_61_90_amount,
        creditor_90_plus_amount=creditor_90_plus_amount,
        creditor_overdue=creditor_overdue,
        creditor_due_soon=creditor_due_soon,
        creditor_total_overdue=creditor_total_overdue,
        creditor_bills=creditor_bills,

        # Payment management
        financial_payment_records=financial_payment_records,
        payment_money_in=payment_money_in,
        payment_money_out=payment_money_out,
        payment_net_movement=payment_net_movement,
        payment_transaction_count=payment_transaction_count,

        # Template data
        now=datetime.now(),
        user=session.get("user"),
        role=session.get("role")
    )
@app.route("/financials/expenses/create", methods=["POST"])
@require_roles("superadmin", "admin", "accounts")
def create_expense():

    try:
        expense_date_str = request.form.get("expense_date", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        reference = request.form.get("reference", "").strip()
        payment_method = request.form.get("payment_method", "").strip()
        amount_str = request.form.get("amount", "").strip()
        notes = request.form.get("notes", "").strip()

        # -----------------------------
        # VALIDATION
        # -----------------------------

        if not category:
            flash("Expense category is required.", "danger")
            return redirect(url_for("financials"))

        if not description:
            flash("Expense description is required.", "danger")
            return redirect(url_for("financials"))

        if not amount_str:
            flash("Expense amount is required.", "danger")
            return redirect(url_for("financials"))

        try:
            amount = float(amount_str)
        except (ValueError, TypeError):
            flash("Please enter a valid expense amount.", "danger")
            return redirect(url_for("financials"))

        if amount <= 0:
            flash("Expense amount must be greater than zero.", "danger")
            return redirect(url_for("financials"))

        # -----------------------------
        # EXPENSE DATE
        # -----------------------------

        if expense_date_str:
            try:
                expense_date = datetime.strptime(
                    expense_date_str,
                    "%Y-%m-%d"
                )
            except ValueError:
                flash("Invalid expense date.", "danger")
                return redirect(url_for("financials"))
        else:
            expense_date = datetime.utcnow()

        # -----------------------------
        # LOGGED-IN USER
        # -----------------------------

        user_id = session.get("user_id")

        if not user_id:
            flash("Your session has expired. Please log in again.", "danger")
            return redirect(url_for("login"))

        user = User.query.get(user_id)

        if not user:
            flash("Logged-in user could not be found.", "danger")
            return redirect(url_for("login"))

        # -----------------------------
        # CREATE EXPENSE
        # -----------------------------

        expense = Expense(
            expense_number=generate_expense_number(),
            expense_date=expense_date,
            description=description,
            category=category,
            reference=reference or None,
            payment_method=payment_method or None,
            amount=amount,
            status="Pending",
            notes=notes or None,
            created_by=user.id
        )

        db.session.add(expense)

        # Force SQLAlchemy to send the INSERT now.
        db.session.flush()

        db.session.commit()

        flash(
            f"Expense {expense.expense_number} created successfully.",
            "success"
        )

        return redirect(url_for("financials"))

    except Exception as e:

        db.session.rollback()

        app.logger.exception(
            "ERROR CREATING EXPENSE: %s",
            str(e)
        )

        flash(
            f"Expense could not be saved: {str(e)}",
            "danger"
        )

        return redirect(url_for("financials"))

@app.route("/financials/expenses/<int:expense_id>")
@require_roles("admin", "accounts", "superadmin")
def view_expense(expense_id):

    expense = Expense.query.get_or_404(expense_id)

    return jsonify({
        "id": expense.id,
        "expense_number": expense.expense_number,
        "expense_date": (
            expense.expense_date.strftime("%d %b %Y")
            if expense.expense_date else None
        ),
        "description": expense.description,
        "category": expense.category,
        "reference": expense.reference,
        "payment_method": expense.payment_method,
        "amount": float(expense.amount or 0),
        "status": expense.status,
        "notes": expense.notes,
        "created_by": (
            expense.user.username
            if expense.user else None
        ),
        "created_at": (
            expense.created_at.strftime("%d %b %Y %H:%M")
            if expense.created_at else None
        )
    })

@app.route(
    "/financials/expenses/<int:expense_id>/approve",
    methods=["POST"]
)
@require_roles("admin", "accounts", "superadmin")
def approve_expense(expense_id):

    expense = Expense.query.get_or_404(expense_id)

    if expense.status != "Pending":
        return jsonify({
            "success": False,
            "message": (
                f"Expense {expense.expense_number} "
                f"is already {expense.status.lower()}."
            )
        }), 400

    try:
        expense.status = "Approved"

        db.session.commit()

        return jsonify({
            "success": True,
            "message": (
                f"Expense {expense.expense_number} "
                "approved successfully."
            ),
            "status": expense.status
        })

    except Exception as e:
        db.session.rollback()

        app.logger.exception(
            "Error approving expense %s: %s",
            expense_id,
            e
        )

        return jsonify({
            "success": False,
            "message": "An error occurred while approving the expense."
        }), 500
        
@app.route("/financials/expenses/<int:expense_id>/reject", methods=["POST"])
@require_roles("admin", "superadmin")
def reject_expense(expense_id):

    expense = Expense.query.get_or_404(expense_id)

    # Only pending expenses can be rejected
    if expense.status != "Pending":
        return jsonify({
            "success": False,
            "message": (
                f"Expense {expense.expense_number} "
                f"is already {expense.status.lower()}."
            )
        }), 400

    try:

        data = request.get_json(silent=True) or {}

        reason = str(
            data.get("reason", "")
        ).strip()

        if not reason:
            return jsonify({
                "success": False,
                "message": "A rejection reason is required."
            }), 400

        expense.status = "Rejected"

        # Store rejection reason in the existing notes field
        if expense.notes:
            expense.notes = (
                f"{expense.notes}\n\n"
                f"Rejection reason: {reason}"
            )
        else:
            expense.notes = (
                f"Rejection reason: {reason}"
            )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": (
                f"Expense {expense.expense_number} "
                "rejected successfully."
            ),
            "status": expense.status
        })

    except Exception as e:

        db.session.rollback()

        app.logger.exception(
            "Error rejecting expense %s: %s",
            expense_id,
            e
        )

        return jsonify({
            "success": False,
            "message": "An error occurred while rejecting the expense."
        }), 500

@app.route("/financials/expenses/<int:id>/pay", methods=["POST"])
@require_roles("superadmin", "admin", "accounts")
def pay_expense(id):
    expense = Expense.query.get_or_404(id)

    if expense.status != "Approved":
        flash(
            "Only approved expenses can be marked as paid.",
            "warning"
        )
        return redirect(url_for("financials"))

    expense.status = "Paid"

    db.session.commit()

    flash(
        f"Expense {expense.expense_number} marked as paid.",
        "success"
    )

    return redirect(url_for("financials"))


@app.route("/financials/payments/export")
@require_roles("admin", "accounts", "superadmin")
def export_financial_payments():

    import csv
    from io import StringIO
    from flask import make_response

    # =====================================================
    # FILTERS
    # =====================================================

    search = request.args.get(
        "search",
        ""
    ).strip().lower()

    payment_type = request.args.get(
        "payment_type",
        ""
    ).strip()

    payment_method = request.args.get(
        "payment_method",
        ""
    ).strip()

    period = request.args.get(
        "period",
        "All Time"
    ).strip()


    # =====================================================
    # DATE RANGE
    # =====================================================

    today = datetime.now()

    start_date = None

    if period == "Today":

        start_date = today.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

    elif period == "This Week":

        start_date = today - timedelta(
            days=today.weekday()
        )

        start_date = start_date.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

    elif period == "This Month":

        start_date = today.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

    elif period == "This Quarter":

        quarter_month = (
            ((today.month - 1) // 3) * 3
        ) + 1

        start_date = today.replace(
            month=quarter_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

    elif period == "This Year":

        start_date = today.replace(
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )


    # =====================================================
    # CUSTOMER PAYMENTS
    # =====================================================

    customer_query = Payment.query


    if start_date:

        customer_query = customer_query.filter(
            Payment.paid_at >= start_date
        )


    customer_payments = (
        customer_query
        .order_by(
            Payment.paid_at.desc()
        )
        .all()
    )


    # =====================================================
    # SUPPLIER PAYMENTS
    # =====================================================

    supplier_query = SupplierPayment.query


    if start_date:

        supplier_query = supplier_query.filter(
            SupplierPayment.paid_at >= start_date
        )


    supplier_payments = (
        supplier_query
        .order_by(
            SupplierPayment.paid_at.desc()
        )
        .all()
    )


    # =====================================================
    # COMBINE PAYMENTS
    # =====================================================

    records = []


    # -----------------------------------------------------
    # CUSTOMER PAYMENTS
    # -----------------------------------------------------

    for payment in customer_payments:

        party = "Customer"

        if hasattr(payment, "customer") and payment.customer:

            party = (
                getattr(
                    payment.customer,
                    "customer_name",
                    None
                )
                or getattr(
                    payment.customer,
                    "name",
                    None
                )
                or "Customer"
            )

        elif hasattr(payment, "invoice") and payment.invoice:

            invoice = payment.invoice

            if hasattr(invoice, "customer"):

                party = (
                    getattr(
                        invoice.customer,
                        "customer_name",
                        None
                    )
                    or getattr(
                        invoice.customer,
                        "name",
                        None
                    )
                    or "Customer"
                )


        reference = (
            getattr(
                payment,
                "payment_reference",
                None
            )
            or getattr(
                payment,
                "reference",
                None
            )
            or getattr(
                payment,
                "receipt_number",
                None
            )
            or f"PAY-{payment.id}"
        )


        method = (
            getattr(
                payment,
                "payment_method",
                None
            )
            or "—"
        )


        amount = float(
            getattr(
                payment,
                "amount",
                0
            )
            or 0
        )


        paid_at = getattr(
            payment,
            "paid_at",
            None
        )


        records.append({

            "date": paid_at,

            "reference": reference,

            "party": party,

            "type": "Customer Payment",

            "method": method,

            "amount": amount,

            "status": "Completed"

        })


    # -----------------------------------------------------
    # SUPPLIER PAYMENTS
    # -----------------------------------------------------

    for payment in supplier_payments:

        supplier = getattr(
            payment,
            "supplier",
            None
        )


        party = (
            getattr(
                supplier,
                "supplier_name",
                None
            )
            if supplier
            else "Supplier"
        )


        reference = (
            getattr(
                payment,
                "payment_reference",
                None
            )
            or getattr(
                payment,
                "reference",
                None
            )
            or getattr(
                payment,
                "receipt_number",
                None
            )
            or f"SP-{payment.id}"
        )


        method = (
            getattr(
                payment,
                "payment_method",
                None
            )
            or "—"
        )


        amount = float(
            getattr(
                payment,
                "amount",
                0
            )
            or 0
        )


        paid_at = getattr(
            payment,
            "paid_at",
            None
        )


        status = (
            getattr(
                payment,
                "status",
                None
            )
            or "Completed"
        )


        records.append({

            "date": paid_at,

            "reference": reference,

            "party": party,

            "type": "Supplier Payment",

            "method": method,

            "amount": amount,

            "status": status

        })


    # =====================================================
    # APPLY TYPE / METHOD / SEARCH FILTERS
    # =====================================================

    filtered_records = []


    for record in records:

        if payment_type:

            if record["type"] != payment_type:
                continue


        if payment_method:

            if (
                str(record["method"]).lower()
                != payment_method.lower()
            ):
                continue


        if search:

            searchable = " ".join([

                str(record["party"]),

                str(record["reference"]),

                str(record["type"]),

                str(record["method"]),

                str(record["status"])

            ]).lower()


            if search not in searchable:
                continue


        filtered_records.append(
            record
        )


    # =====================================================
    # SORT
    # =====================================================

    filtered_records.sort(

        key=lambda x: (
            x["date"]
            or datetime.min
        ),

        reverse=True

    )


    # =====================================================
    # CSV
    # =====================================================

    output = StringIO()

    writer = csv.writer(
        output
    )


    writer.writerow([

        "Date",
        "Reference",
        "Party",
        "Payment Type",
        "Payment Method",
        "Amount",
        "Status"

    ])


    for record in filtered_records:

        date_value = record["date"]

        if date_value:

            date_value = date_value.strftime(
                "%d %b %Y %H:%M"
            )

        else:

            date_value = ""


        writer.writerow([

            date_value,

            record["reference"],

            record["party"],

            record["type"],

            record["method"],

            f"{record['amount']:.2f}",

            record["status"]

        ])


    # =====================================================
    # RESPONSE
    # =====================================================

    response = make_response(
        output.getvalue()
    )


    response.headers[
        "Content-Disposition"
    ] = (
        "attachment; "
        "filename=financial_payments.csv"
    )


    response.headers[
        "Content-Type"
    ] = "text/csv; charset=utf-8"


    return response

#FINANCIAL REPORTS

#Financial profit and loss report

@app.route("/financials/reports/profit-loss")
@require_roles("admin", "accounts", "superadmin")
def profit_loss_report():

    # =========================================================
    # REPORT PARAMETERS
    # =========================================================

    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    basis = request.args.get("basis", "Accrual")

    # Default to current month if dates are not supplied
    today = datetime.utcnow().date()

    if not start_date_str:
        start_date = today.replace(day=1)
    else:
        try:
            start_date = datetime.strptime(
                start_date_str,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            flash("Invalid start date.", "danger")
            return redirect(url_for("financials"))

    if not end_date_str:
        end_date = today
    else:
        try:
            end_date = datetime.strptime(
                end_date_str,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            flash("Invalid end date.", "danger")
            return redirect(url_for("financials"))

    if start_date > end_date:
        flash(
            "The start date cannot be after the end date.",
            "danger"
        )
        return redirect(url_for("financials"))

    # =========================================================
    # DATETIME RANGE
    # =========================================================

    start_datetime = datetime.combine(
        start_date,
        time.min
    )

    end_datetime = datetime.combine(
        end_date,
        time.max
    )

    # =========================================================
    # REVENUE
    # =========================================================

    revenue_categories = {
        "Labour / Service Revenue": 0.0,
        "Parts & Accessories Sales": 0.0,
        "Diagnostic Services": 0.0,
        "Inspection Services": 0.0,
        "Vehicle Recovery / Towing": 0.0,
        "Other Garage Revenue": 0.0
    }

    # ---------------------------------------------------------
    # ACCRUAL BASIS
    #
    # Revenue is recognized when invoices are issued.
    # ---------------------------------------------------------

    if basis.lower() == "accrual":

        invoice_items = (
            InvoiceItem.query
            .join(Invoice, InvoiceItem.invoice_id == Invoice.id)
            .filter(
                Invoice.issue_date >= start_datetime,
                Invoice.issue_date <= end_datetime
            )
            .all()
        )

        for item in invoice_items:

            category = item.revenue_category

            if category not in revenue_categories:
                category = "Other Garage Revenue"

            revenue_categories[category] += float(
                item.total or 0
            )

    # ---------------------------------------------------------
    # CASH BASIS
    #
    # Revenue is recognized when payment is received.
    #
    # Payments belong to invoices, so we allocate the payment
    # across the invoice items proportionally.
    # ---------------------------------------------------------

    else:

        payments = (
            Payment.query
            .filter(
                Payment.paid_at >= start_datetime,
                Payment.paid_at <= end_datetime
            )
            .all()
        )

        for payment in payments:

            invoice = payment.invoice

            if not invoice:
                continue

            invoice_subtotal = float(
                invoice.subtotal or 0
            )

            if invoice_subtotal <= 0:
                continue

            invoice_items = invoice.items

            for item in invoice_items:

                item_total = float(
                    item.total or 0
                )

                proportion = (
                    item_total / invoice_subtotal
                )

                allocated_amount = (
                    float(payment.amount or 0)
                    * proportion
                )

                category = item.revenue_category

                if category not in revenue_categories:
                    category = "Other Garage Revenue"

                revenue_categories[category] += (
                    allocated_amount
                )

    # =========================================================
    # TOTAL REVENUE
    # =========================================================

    total_revenue = sum(
        revenue_categories.values()
    )

    # =========================================================
    # COST OF SALES / DIRECT COSTS
    # =========================================================

    direct_costs = {
        "Parts & Materials Used": 0.0,
        "Lubricants & Fluids": 0.0,
        "Subcontracted Repairs": 0.0,
        "Direct Labour": 0.0,
        "Other Direct Job Costs": 0.0
    }

    # ---------------------------------------------------------
    # DIRECT COSTS FROM INVOICE ITEMS
    #
    # Parts:
    #     unit_cost / cost_total
    #
    # Labour:
    #     hourly_cost / cost_total
    # ---------------------------------------------------------

    invoice_items_for_cost = (
        InvoiceItem.query
        .join(Invoice, InvoiceItem.invoice_id == Invoice.id)
        .filter(
            Invoice.issue_date >= start_datetime,
            Invoice.issue_date <= end_datetime
        )
        .all()
    )

    for item in invoice_items_for_cost:

        cost = float(
            item.cost_total or 0
        )

        if cost <= 0:
            continue

        if item.item_type == "Parts":

            direct_costs[
                "Parts & Materials Used"
            ] += cost

        elif item.item_type == "Labour":

            direct_costs[
                "Direct Labour"
            ] += cost

        else:

            direct_costs[
                "Other Direct Job Costs"
            ] += cost

    # =========================================================
    # TOTAL COST OF SALES
    # =========================================================

    total_cost_of_sales = sum(
        direct_costs.values()
    )

    # =========================================================
    # GROSS PROFIT
    # =========================================================

    gross_profit = (
        total_revenue -
        total_cost_of_sales
    )

    if total_revenue > 0:

        gross_profit_margin = (
            gross_profit /
            total_revenue
        ) * 100

    else:

        gross_profit_margin = 0.0

    # =========================================================
    # OPERATING EXPENSES
    # =========================================================

    operating_expenses = {}

    expenses = (
        Expense.query
        .filter(
            Expense.expense_date >= start_datetime,
            Expense.expense_date <= end_datetime,
            Expense.status.in_([
                "Approved",
                "Paid"
            ])
        )
        .all()
    )

    for expense in expenses:

        category = (
            expense.category or
            "Other Operating Expenses"
        )

        amount = float(
            expense.amount or 0
        )

        operating_expenses[category] = (
            operating_expenses.get(category, 0.0)
            + amount
        )

    total_operating_expenses = sum(
        operating_expenses.values()
    )

    # =========================================================
    # OPERATING PROFIT
    # =========================================================

    operating_profit = (
        gross_profit -
        total_operating_expenses
    )

    # =========================================================
    # FINANCE / INTEREST EXPENSE
    # =========================================================
    #
    # We do not currently have a dedicated finance-expense
    # field/model, so this remains zero until we add proper
    # finance expense classification.
    # =========================================================

    finance_interest_expense = 0.0

    # =========================================================
    # OTHER INCOME
    # =========================================================

    other_income = 0.0

    # =========================================================
    # OTHER EXPENSES
    # =========================================================

    other_expenses = 0.0

    # =========================================================
    # PROFIT BEFORE TAX
    # =========================================================

    profit_before_tax = (
        operating_profit
        + other_income
        - finance_interest_expense
        - other_expenses
    )

    # =========================================================
    # INCOME TAX
    # =========================================================
    #
    # We do not yet have a tax configuration/model, so don't
    # invent a tax amount.
    # =========================================================

    income_tax = 0.0

    # =========================================================
    # NET PROFIT
    # =========================================================

    net_profit = (
        profit_before_tax -
        income_tax
    )

    if total_revenue > 0:

        net_profit_margin = (
            net_profit /
            total_revenue
        ) * 100

    else:

        net_profit_margin = 0.0

    # =========================================================
    # RENDER REPORT
    # =========================================================

    return render_template(
        "financials/profit_loss.html",

        start_date=start_date,
        end_date=end_date,

        basis=basis,

        revenue_categories=revenue_categories,
        total_revenue=total_revenue,

        direct_costs=direct_costs,
        total_cost_of_sales=total_cost_of_sales,

        gross_profit=gross_profit,
        gross_profit_margin=gross_profit_margin,

        operating_expenses=operating_expenses,
        total_operating_expenses=total_operating_expenses,

        operating_profit=operating_profit,

        finance_interest_expense=finance_interest_expense,

        other_income=other_income,

        other_expenses=other_expenses,

        profit_before_tax=profit_before_tax,

        income_tax=income_tax,

        net_profit=net_profit,

        net_profit_margin=net_profit_margin,

        user=session.get("user"),
        role=session.get("role")
    )

@app.route("/financials/reports/profit-loss/pdf")
@require_roles("admin", "accounts", "superadmin")
def profit_loss_pdf():

    # =========================================================
    # REPORT PARAMETERS
    # =========================================================

    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    basis = request.args.get("basis", "Accrual")

    today = datetime.utcnow().date()

    # ---------------------------------------------------------
    # START DATE
    # ---------------------------------------------------------

    if start_date_str:
        try:
            start_date = datetime.strptime(
                start_date_str,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            flash("Invalid start date.", "danger")
            return redirect(url_for("financials"))
    else:
        start_date = today.replace(day=1)

    # ---------------------------------------------------------
    # END DATE
    # ---------------------------------------------------------

    if end_date_str:
        try:
            end_date = datetime.strptime(
                end_date_str,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            flash("Invalid end date.", "danger")
            return redirect(url_for("financials"))
    else:
        end_date = today

    if start_date > end_date:
        flash(
            "The start date cannot be after the end date.",
            "danger"
        )
        return redirect(url_for("financials"))

    # =========================================================
    # DATETIME RANGE
    # =========================================================

    start_datetime = datetime.combine(
        start_date,
        time.min
    )

    end_datetime = datetime.combine(
        end_date,
        time.max
    )

    # =========================================================
    # REVENUE
    # =========================================================

    revenue_categories = {
        "Labour / Service Revenue": 0.0,
        "Parts & Accessories Sales": 0.0,
        "Diagnostic Services": 0.0,
        "Inspection Services": 0.0,
        "Vehicle Recovery / Towing": 0.0,
        "Other Garage Revenue": 0.0
    }

    if basis.lower() == "accrual":

        invoice_items = (
            InvoiceItem.query
            .join(
                Invoice,
                InvoiceItem.invoice_id == Invoice.id
            )
            .filter(
                Invoice.issue_date >= start_datetime,
                Invoice.issue_date <= end_datetime
            )
            .all()
        )

        for item in invoice_items:

            category = item.revenue_category

            if category not in revenue_categories:
                category = "Other Garage Revenue"

            revenue_categories[category] += float(
                item.total or 0
            )

    else:

        payments = (
            Payment.query
            .filter(
                Payment.paid_at >= start_datetime,
                Payment.paid_at <= end_datetime
            )
            .all()
        )

        for payment in payments:

            invoice = payment.invoice

            if not invoice:
                continue

            invoice_subtotal = float(
                invoice.subtotal or 0
            )

            if invoice_subtotal <= 0:
                continue

            for item in invoice.items:

                item_total = float(
                    item.total or 0
                )

                proportion = (
                    item_total /
                    invoice_subtotal
                )

                allocated_amount = (
                    float(payment.amount or 0)
                    * proportion
                )

                category = item.revenue_category

                if category not in revenue_categories:
                    category = "Other Garage Revenue"

                revenue_categories[category] += (
                    allocated_amount
                )

    total_revenue = sum(
        revenue_categories.values()
    )

    # =========================================================
    # DIRECT COSTS
    # =========================================================

    direct_costs = {
        "Parts & Materials Used": 0.0,
        "Lubricants & Fluids": 0.0,
        "Subcontracted Repairs": 0.0,
        "Direct Labour": 0.0,
        "Other Direct Job Costs": 0.0
    }

    invoice_items_for_cost = (
        InvoiceItem.query
        .join(
            Invoice,
            InvoiceItem.invoice_id == Invoice.id
        )
        .filter(
            Invoice.issue_date >= start_datetime,
            Invoice.issue_date <= end_datetime
        )
        .all()
    )

    for item in invoice_items_for_cost:

        cost = float(
            item.cost_total or 0
        )

        if cost <= 0:
            continue

        if item.item_type == "Parts":

            direct_costs[
                "Parts & Materials Used"
            ] += cost

        elif item.item_type == "Labour":

            direct_costs[
                "Direct Labour"
            ] += cost

        else:

            direct_costs[
                "Other Direct Job Costs"
            ] += cost

    total_cost_of_sales = sum(
        direct_costs.values()
    )

    # =========================================================
    # GROSS PROFIT
    # =========================================================

    gross_profit = (
        total_revenue -
        total_cost_of_sales
    )

    gross_profit_margin = (
        (gross_profit / total_revenue) * 100
        if total_revenue > 0
        else 0.0
    )

    # =========================================================
    # OPERATING EXPENSES
    # =========================================================

    operating_expenses = {}

    expenses = (
        Expense.query
        .filter(
            Expense.expense_date >= start_datetime,
            Expense.expense_date <= end_datetime,
            Expense.status.in_([
                "Approved",
                "Paid"
            ])
        )
        .all()
    )

    for expense in expenses:

        category = (
            expense.category or
            "Other Operating Expenses"
        )

        amount = float(
            expense.amount or 0
        )

        operating_expenses[category] = (
            operating_expenses.get(category, 0.0)
            + amount
        )

    total_operating_expenses = sum(
        operating_expenses.values()
    )

    # =========================================================
    # PROFITS
    # =========================================================

    operating_profit = (
        gross_profit -
        total_operating_expenses
    )

    finance_interest_expense = 0.0
    other_income = 0.0
    other_expenses = 0.0

    profit_before_tax = (
        operating_profit
        + other_income
        - finance_interest_expense
        - other_expenses
    )

    income_tax = 0.0

    net_profit = (
        profit_before_tax -
        income_tax
    )

    net_profit_margin = (
        (net_profit / total_revenue) * 100
        if total_revenue > 0
        else 0.0
    )

    # =========================================================
    # PDF SETUP
    # =========================================================

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Autovex Garage MS Profit & Loss Statement",
        author=session.get("user", "Autovex Garage MS")
    )

    styles = getSampleStyleSheet()

    company_style = ParagraphStyle(
        "Company",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceAfter=2
    )

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=5
    )

    normal_style = ParagraphStyle(
        "NormalSmall",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12
    )

    bold_style = ParagraphStyle(
        "BoldSmall",
        parent=normal_style,
        fontName="Helvetica-Bold"
    )

    section_style = ParagraphStyle(
        "Section",
        parent=normal_style,
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12
    )

    right_style = ParagraphStyle(
        "Right",
        parent=normal_style,
        alignment=TA_RIGHT
    )

    # =========================================================
    # HELPERS
    # =========================================================

    def money(value):
        return f"KES {float(value or 0):,.2f}"

    def statement_row(
        label,
        amount,
        indent=False,
        bold=False
    ):

        label_style = bold_style if bold else normal_style
        amount_style = (
            ParagraphStyle(
                "AmountBold",
                parent=right_style,
                fontName="Helvetica-Bold"
            )
            if bold
            else right_style
        )

        if indent:
            label = "&nbsp;&nbsp;&nbsp;" + label

        return [
            Paragraph(label, label_style),
            Paragraph(money(amount), amount_style)
        ]

    # =========================================================
    # DOCUMENT CONTENT
    # =========================================================

    story = []

    # ---------------------------------------------------------
    # HEADER
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "AUTOVEX GARAGE MS",
            company_style
        )
    )

    story.append(
        Paragraph(
            "PROFIT &amp; LOSS STATEMENT",
            title_style
        )
    )

    story.append(
        Paragraph(
            f"Reporting Period: "
            f"<b>{start_date.strftime('%d %B %Y')}</b> "
            f"to "
            f"<b>{end_date.strftime('%d %B %Y')}</b>",
            ParagraphStyle(
                "Period",
                parent=normal_style,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#667085")
            )
        )
    )

    story.append(Spacer(1, 7 * mm))

    # ---------------------------------------------------------
    # META
    # ---------------------------------------------------------

    meta = Table(
        [[
            Paragraph(
                f"<b>Accounting Basis:</b> {basis}",
                normal_style
            ),
            Paragraph(
                "<b>Currency:</b> KES",
                ParagraphStyle(
                    "MetaRight",
                    parent=normal_style,
                    alignment=TA_RIGHT
                )
            )
        ]],
        colWidths=[
            87 * mm,
            87 * mm
        ]
    )

    meta.setStyle(
        TableStyle([
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "LINEABOVE",
                (0, 0),
                (-1, 0),
                0.5,
                colors.HexColor("#D9DEE8")
            ),
            (
                "LINEBELOW",
                (0, 0),
                (-1, 0),
                0.5,
                colors.HexColor("#D9DEE8")
            )
        ])
    )

    story.append(meta)
    story.append(Spacer(1, 5 * mm))

    # =========================================================
    # REVENUE
    # =========================================================

    story.append(
        Paragraph(
            "REVENUE",
            section_style
        )
    )

    revenue_rows = []

    for category in [
        "Labour / Service Revenue",
        "Parts & Accessories Sales",
        "Diagnostic Services",
        "Inspection Services",
        "Vehicle Recovery / Towing",
        "Other Garage Revenue"
    ]:

        revenue_rows.append(
            statement_row(
                category,
                revenue_categories.get(category, 0),
                indent=True
            )
        )

    revenue_rows.append(
        statement_row(
            "Total Revenue",
            total_revenue,
            bold=True
        )
    )

    revenue_table = Table(
        revenue_rows,
        colWidths=[120 * mm, 54 * mm]
    )

    revenue_table.setStyle(
        TableStyle([
            (
                "LINEBELOW",
                (0, 0),
                (-1, -1),
                0.25,
                colors.HexColor("#E5E7EB")
            ),
            (
                "LINEABOVE",
                (0, -1),
                (-1, -1),
                0.7,
                colors.HexColor("#7A8494")
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4
            )
        ])
    )

    story.append(revenue_table)
    story.append(Spacer(1, 5 * mm))

    # =========================================================
    # COST OF SALES
    # =========================================================

    story.append(
        Paragraph(
            "COST OF SALES / DIRECT COSTS",
            section_style
        )
    )

    cost_rows = []

    for category in [
        "Parts & Materials Used",
        "Lubricants & Fluids",
        "Subcontracted Repairs",
        "Direct Labour",
        "Other Direct Job Costs"
    ]:

        cost_rows.append(
            statement_row(
                category,
                direct_costs.get(category, 0),
                indent=True
            )
        )

    cost_rows.append(
        statement_row(
            "Total Cost of Sales",
            total_cost_of_sales,
            bold=True
        )
    )

    cost_table = Table(
        cost_rows,
        colWidths=[120 * mm, 54 * mm]
    )

    cost_table.setStyle(
        TableStyle([
            (
                "LINEBELOW",
                (0, 0),
                (-1, -1),
                0.25,
                colors.HexColor("#E5E7EB")
            ),
            (
                "LINEABOVE",
                (0, -1),
                (-1, -1),
                0.7,
                colors.HexColor("#7A8494")
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4
            )
        ])
    )

    story.append(cost_table)
    story.append(Spacer(1, 5 * mm))

    # =========================================================
    # GROSS PROFIT
    # =========================================================

    gross_table = Table(
        [
            statement_row(
                "GROSS PROFIT",
                gross_profit,
                bold=True
            ),
            [
                Paragraph(
                    "<i>Gross Profit Margin %</i>",
                    ParagraphStyle(
                        "Margin",
                        parent=normal_style,
                        textColor=colors.HexColor("#667085")
                    )
                ),
                Paragraph(
                    f"{gross_profit_margin:,.2f}%",
                    ParagraphStyle(
                        "MarginRight",
                        parent=right_style,
                        textColor=colors.HexColor("#667085"),
                        fontName="Helvetica-Oblique"
                    )
                )
            ]
        ],
        colWidths=[120 * mm, 54 * mm]
    )

    gross_table.setStyle(
        TableStyle([
            (
                "LINEABOVE",
                (0, 0),
                (-1, 0),
                1,
                colors.HexColor("#172033")
            ),
            (
                "LINEBELOW",
                (0, 0),
                (-1, 0),
                1,
                colors.HexColor("#172033")
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    story.append(gross_table)

    # =========================================================
    # OPERATING EXPENSES
    # =========================================================

    story.append(
        Paragraph(
            "OPERATING EXPENSES",
            section_style
        )
    )

    expense_rows = []

    if operating_expenses:

        for category, amount in sorted(
            operating_expenses.items()
        ):

            expense_rows.append(
                statement_row(
                    category,
                    amount,
                    indent=True
                )
            )

    else:

        expense_rows.append(
            [
                Paragraph(
                    "No operating expenses recorded",
                    ParagraphStyle(
                        "Empty",
                        parent=normal_style,
                        textColor=colors.HexColor("#98A2B3")
                    )
                ),
                Paragraph(
                    "KES 0.00",
                    right_style
                )
            ]
        )

    expense_rows.append(
        statement_row(
            "Total Operating Expenses",
            total_operating_expenses,
            bold=True
        )
    )

    expense_table = Table(
        expense_rows,
        colWidths=[120 * mm, 54 * mm]
    )

    expense_table.setStyle(
        TableStyle([
            (
                "LINEBELOW",
                (0, 0),
                (-1, -1),
                0.25,
                colors.HexColor("#E5E7EB")
            ),
            (
                "LINEABOVE",
                (0, -1),
                (-1, -1),
                0.7,
                colors.HexColor("#7A8494")
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4
            )
        ])
    )

    story.append(expense_table)
    story.append(Spacer(1, 6 * mm))

    # =========================================================
    # OPERATING PROFIT
    # =========================================================

    operating_table = Table(
        [
            statement_row(
                "OPERATING PROFIT",
                operating_profit,
                bold=True
            )
        ],
        colWidths=[120 * mm, 54 * mm]
    )

    operating_table.setStyle(
        TableStyle([
            (
                "LINEABOVE",
                (0, 0),
                (-1, 0),
                1,
                colors.HexColor("#172033")
            ),
            (
                "LINEBELOW",
                (0, 0),
                (-1, 0),
                1,
                colors.HexColor("#172033")
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    story.append(operating_table)
    story.append(Spacer(1, 7 * mm))

    # =========================================================
    # OTHER INCOME / EXPENSES
    # =========================================================

    story.append(
        Paragraph(
            "OTHER INCOME &amp; EXPENSES",
            section_style
        )
    )

    other_rows = [
        statement_row(
            "Finance / Interest Expense",
            finance_interest_expense,
            indent=True
        ),
        statement_row(
            "Other Income",
            other_income,
            indent=True
        ),
        statement_row(
            "Other Expenses",
            other_expenses,
            indent=True
        )
    ]

    other_table = Table(
        other_rows,
        colWidths=[120 * mm, 54 * mm]
    )

    other_table.setStyle(
        TableStyle([
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4
            )
        ])
    )

    story.append(other_table)
    story.append(Spacer(1, 5 * mm))

    # =========================================================
    # PROFIT BEFORE TAX
    # =========================================================

    pbt_table = Table(
        [
            statement_row(
                "PROFIT BEFORE TAX",
                profit_before_tax,
                bold=True
            ),
            statement_row(
                "Income Tax",
                income_tax,
                indent=True
            ),
            statement_row(
                "NET PROFIT",
                net_profit,
                bold=True
            ),
            [
                Paragraph(
                    "<i>Net Profit Margin %</i>",
                    ParagraphStyle(
                        "NetMargin",
                        parent=normal_style,
                        textColor=colors.HexColor("#667085")
                    )
                ),
                Paragraph(
                    f"{net_profit_margin:,.2f}%",
                    ParagraphStyle(
                        "NetMarginRight",
                        parent=right_style,
                        textColor=colors.HexColor("#667085"),
                        fontName="Helvetica-Oblique"
                    )
                )
            ]
        ],
        colWidths=[120 * mm, 54 * mm]
    )

    pbt_table.setStyle(
        TableStyle([
            (
                "LINEABOVE",
                (0, 0),
                (-1, 0),
                1,
                colors.HexColor("#172033")
            ),
            (
                "LINEBELOW",
                (0, 2),
                (-1, 2),
                1,
                colors.HexColor("#172033")
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    story.append(pbt_table)

    # =========================================================
    # SIGNATURES
    # =========================================================

    story.append(Spacer(1, 20 * mm))

    signature_table = Table(
        [
            [
                Paragraph(
                    "Prepared By",
                    bold_style
                ),
                Paragraph(
                    "Approved By / Signature",
                    bold_style
                )
            ],
            [
                Paragraph(
                    session.get("user", ""),
                    normal_style
                ),
                Paragraph(
                    "____________________________",
                    normal_style
                )
            ],
            [
                Paragraph(
                    f"Date: {end_date.strftime('%d %B %Y')}",
                    normal_style
                ),
                Paragraph(
                    "Date: ____________________",
                    normal_style
                )
            ]
        ],
        colWidths=[
            87 * mm,
            87 * mm
        ]
    )

    signature_table.setStyle(
        TableStyle([
            (
                "LINEABOVE",
                (0, 0),
                (0, 0),
                0.7,
                colors.HexColor("#667085")
            ),
            (
                "LINEABOVE",
                (1, 0),
                (1, 0),
                0.7,
                colors.HexColor("#667085")
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    story.append(signature_table)

    # =========================================================
    # BUILD PDF
    # =========================================================

    doc.build(story)

    buffer.seek(0)

    filename = (
        f"Autovex_Profit_Loss_"
        f"{start_date.strftime('%Y%m%d')}_"
        f"{end_date.strftime('%Y%m%d')}.pdf"
    )

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )

@app.route("/procurement")
@require_roles("admin", "accounts", "superadmin")
def procurement():

    suppliers = Supplier.query.order_by(
        Supplier.supplier_name.asc()
    ).all()
    supplier_bills = (
        SupplierBill.query
        .join(Supplier)
        .order_by(SupplierBill.bill_date.desc())
        .all()
    )
    purchase_orders = PurchaseOrder.query.order_by(
        PurchaseOrder.order_date.desc()
    ).all()
    goods_receipts = GoodsReceipt.query.order_by(
        GoodsReceipt.received_date.desc()
    ).all()
    # =====================================================
    # PROCUREMENT OVERVIEW STATISTICS
    # =====================================================

    active_suppliers_count = Supplier.query.filter_by(
        status="Active"
    ).count()


    pending_quotations_count = 0
    # Keep this at 0 for now because quotations
    # have not yet been converted to a database model.


    open_lpos_count = PurchaseOrder.query.filter(
        PurchaseOrder.status.in_([
            "Draft",
            "Ordered",
            "Confirmed",
            "Partially Received"
        ])
    ).count()


    outstanding_purchases = db.session.query(
        func.coalesce(
            func.sum(SupplierBill.balance),
            0
        )
    ).filter(
        SupplierBill.balance > 0
    ).scalar() or 0


    # =====================================================
    # GOODS RECEIVED THIS MONTH
    # =====================================================

    now = datetime.utcnow()

    month_start = datetime(
        now.year,
        now.month,
        1
    )

    goods_received_this_month = GoodsReceipt.query.filter(
        GoodsReceipt.received_date >= month_start
    ).count()

    recent_purchase_orders = PurchaseOrder.query.order_by(
        PurchaseOrder.order_date.desc()
    ).limit(5).all()

    # =====================================================
    # PENDING PURCHASE INVOICES
    # =====================================================

    pending_purchase_invoices = SupplierBill.query.filter(
        SupplierBill.balance > 0
    ).count()

    return render_template(
        "procurement/procurement.html",
        user=session.get("user"),
        role=session.get("role"),
        supplier_bills=supplier_bills,
        suppliers=suppliers,
        purchase_orders=purchase_orders,
        goods_receipts=goods_receipts,
        active_suppliers_count=active_suppliers_count,
        pending_quotations_count=pending_quotations_count,
        open_lpos_count=open_lpos_count,
        outstanding_purchases=outstanding_purchases,
        goods_received_this_month=goods_received_this_month,
        pending_purchase_invoices=pending_purchase_invoices,
        recent_purchase_orders=recent_purchase_orders
        )

@app.route("/procurement/suppliers/new", methods=["GET", "POST"])
@require_roles("admin", "accounts", "superadmin")
def new_supplier():

    if request.method == "POST":

        supplier_name = request.form.get("supplier_name", "").strip()
        contact_person = request.form.get("contact_person", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()
        tax_pin = request.form.get("tax_pin", "").strip()

        if not supplier_name:
            flash("Supplier name is required.", "danger")
            return redirect(url_for("new_supplier"))

        supplier = Supplier(
            supplier_name=supplier_name,
            contact_person=contact_person or None,
            phone=phone or None,
            email=email or None,
            address=address or None,
            tax_pin=tax_pin or None,
            status="Active"
        )

        db.session.add(supplier)
        db.session.commit()

        flash("Supplier added successfully.", "success")

        return redirect(
            url_for("procurement")
        )

    return render_template(
        "procurement/supplier_form.html",
        user=session.get("user"),
        role=session.get("role")
    )

@app.route("/procurement/suppliers/<int:supplier_id>/edit", methods=["GET", "POST"])
@require_roles("admin", "accounts", "superadmin")
def edit_supplier(supplier_id):

    supplier = Supplier.query.get_or_404(supplier_id)

    if request.method == "POST":

        supplier_name = request.form.get(
            "supplier_name", ""
        ).strip()

        if not supplier_name:
            flash(
                "Supplier name is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "edit_supplier",
                    supplier_id=supplier.id
                )
            )

        supplier.supplier_name = supplier_name

        supplier.contact_person = (
            request.form.get("contact_person", "").strip()
            or None
        )

        supplier.phone = (
            request.form.get("phone", "").strip()
            or None
        )

        supplier.email = (
            request.form.get("email", "").strip()
            or None
        )

        supplier.address = (
            request.form.get("address", "").strip()
            or None
        )

        supplier.tax_pin = (
            request.form.get("tax_pin", "").strip()
            or None
        )

        db.session.commit()

        flash(
            "Supplier updated successfully.",
            "success"
        )

        return redirect(
            url_for("procurement")
        )

    return render_template(
        "procurement/supplier_form.html",
        supplier=supplier,
        user=session.get("user"),
        role=session.get("role")
    )

@app.route(
    "/procurement/suppliers/<int:supplier_id>/toggle-status",
    methods=["POST"]
)
@require_roles("admin", "accounts", "superadmin")
def toggle_supplier_status(supplier_id):

    supplier = Supplier.query.get_or_404(supplier_id)

    if supplier.status == "Active":
        supplier.status = "Inactive"
    else:
        supplier.status = "Active"

    db.session.commit()

    flash(
        f"Supplier marked as {supplier.status.lower()}.",
        "success"
    )

    return redirect(
        url_for("procurement")
    )

@app.route("/procurement/lpos/new", methods=["GET", "POST"])
@require_roles("admin", "accounts", "superadmin")
def new_purchase_order():

    suppliers = Supplier.query.filter_by(
        status="Active"
    ).order_by(
        Supplier.supplier_name.asc()
    ).all()

    if request.method == "POST":

        # =================================================
        # BASIC FORM DATA
        # =================================================

        supplier_id = request.form.get("supplier_id")

        order_date = request.form.get("order_date")

        expected_date = request.form.get(
            "expected_date"
        )

        description = request.form.get(
            "description",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()


        # =================================================
        # SUPPLIER VALIDATION
        # =================================================

        if not supplier_id:

            flash(
                "Please select a supplier.",
                "danger"
            )

            return render_template(
                "procurement/purchase_order_form.html",
                suppliers=suppliers,
                user=session.get("user"),
                role=session.get("role")
            )


        try:

            supplier_id = int(supplier_id)

        except (TypeError, ValueError):

            flash(
                "Invalid supplier selected.",
                "danger"
            )

            return render_template(
                "procurement/purchase_order_form.html",
                suppliers=suppliers,
                user=session.get("user"),
                role=session.get("role")
            )


        supplier = Supplier.query.get(
            supplier_id
        )


        if not supplier:

            flash(
                "Selected supplier was not found.",
                "danger"
            )

            return render_template(
                "procurement/purchase_order_form.html",
                suppliers=suppliers,
                user=session.get("user"),
                role=session.get("role")
            )


        # =================================================
        # DATE PROCESSING
        # =================================================

        order_date_value = datetime.utcnow()

        expected_date_value = None


        if order_date:

            try:

                order_date_value = datetime.strptime(
                    order_date,
                    "%Y-%m-%d"
                )

            except ValueError:

                flash(
                    "Invalid order date.",
                    "danger"
                )

                return render_template(
                    "procurement/purchase_order_form.html",
                    suppliers=suppliers,
                    user=session.get("user"),
                    role=session.get("role")
                )


        if expected_date:

            try:

                expected_date_value = datetime.strptime(
                    expected_date,
                    "%Y-%m-%d"
                )

            except ValueError:

                flash(
                    "Invalid expected delivery date.",
                    "danger"
                )

                return render_template(
                    "procurement/purchase_order_form.html",
                    suppliers=suppliers,
                    user=session.get("user"),
                    role=session.get("role")
                )


        # =================================================
        # GET ITEM ARRAYS
        # =================================================

        item_descriptions = request.form.getlist(
            "item_description[]"
        )

        quantities = request.form.getlist(
            "quantity[]"
        )

        unit_prices = request.form.getlist(
            "unit_price[]"
        )


        # =================================================
        # VALIDATE ITEMS
        # =================================================

        if not item_descriptions:

            flash(
                "Please add at least one purchase item.",
                "danger"
            )

            return render_template(
                "procurement/purchase_order_form.html",
                suppliers=suppliers,
                user=session.get("user"),
                role=session.get("role")
            )


        if not (
            len(item_descriptions)
            == len(quantities)
            == len(unit_prices)
        ):

            flash(
                "There was a problem with the purchase items. Please try again.",
                "danger"
            )

            return render_template(
                "procurement/purchase_order_form.html",
                suppliers=suppliers,
                user=session.get("user"),
                role=session.get("role")
            )


        # =================================================
        # PREPARE ITEMS
        # =================================================

        prepared_items = []

        grand_total = 0.0


        for index in range(
            len(item_descriptions)
        ):

            item_description = (
                item_descriptions[index]
                or ""
            ).strip()


            quantity_raw = (
                quantities[index]
                or ""
            ).strip()


            unit_price_raw = (
                unit_prices[index]
                or ""
            ).strip()


            # ---------------------------------------------
            # DESCRIPTION
            # ---------------------------------------------

            if not item_description:

                flash(
                    f"Item {index + 1}: description is required.",
                    "danger"
                )

                return render_template(
                    "procurement/purchase_order_form.html",
                    suppliers=suppliers,
                    user=session.get("user"),
                    role=session.get("role")
                )


            # ---------------------------------------------
            # QUANTITY
            # ---------------------------------------------

            try:

                quantity = float(
                    quantity_raw
                )

            except (TypeError, ValueError):

                flash(
                    f"Item {index + 1}: please enter a valid quantity.",
                    "danger"
                )

                return render_template(
                    "procurement/purchase_order_form.html",
                    suppliers=suppliers,
                    user=session.get("user"),
                    role=session.get("role")
                )


            if quantity <= 0:

                flash(
                    f"Item {index + 1}: quantity must be greater than zero.",
                    "danger"
                )

                return render_template(
                    "procurement/purchase_order_form.html",
                    suppliers=suppliers,
                    user=session.get("user"),
                    role=session.get("role")
                )


            # ---------------------------------------------
            # UNIT PRICE
            # ---------------------------------------------

            try:

                unit_price = float(
                    unit_price_raw
                )

            except (TypeError, ValueError):

                flash(
                    f"Item {index + 1}: please enter a valid unit price.",
                    "danger"
                )

                return render_template(
                    "procurement/purchase_order_form.html",
                    suppliers=suppliers,
                    user=session.get("user"),
                    role=session.get("role")
                )


            if unit_price < 0:

                flash(
                    f"Item {index + 1}: unit price cannot be negative.",
                    "danger"
                )

                return render_template(
                    "procurement/purchase_order_form.html",
                    suppliers=suppliers,
                    user=session.get("user"),
                    role=session.get("role")
                )


            # ---------------------------------------------
            # CALCULATE ITEM TOTAL
            # ---------------------------------------------

            item_total = (
                quantity * unit_price
            )


            grand_total += item_total


            prepared_items.append({

                "description": item_description,

                "quantity": quantity,

                "unit_price": unit_price,

                "total_price": item_total

            })


        # =================================================
        # GENERATE LPO NUMBER
        # =================================================

        today = datetime.utcnow().strftime(
            "%Y%m%d"
        )


        existing_count = PurchaseOrder.query.filter(
            PurchaseOrder.lpo_number.like(
                f"LPO-{today}-%"
            )
        ).count()


        lpo_number = (
            f"LPO-{today}-{existing_count + 1:04d}"
        )


        # =================================================
        # CREATE PURCHASE ORDER
        # =================================================

        purchase_order = PurchaseOrder(

            supplier_id=supplier_id,

            lpo_number=lpo_number,

            order_date=order_date_value,

            expected_date=expected_date_value,

            description=description or None,

            total_amount=grand_total,

            status="Draft",

            notes=notes or None

        )


        db.session.add(
            purchase_order
        )


        # =================================================
        # CREATE PURCHASE ORDER ITEMS
        # =================================================

        for item in prepared_items:

            purchase_order_item = PurchaseOrderItem(

                purchase_order=purchase_order,

                item_description=item["description"],

                quantity=item["quantity"],

                unit_price=item["unit_price"],

                total_price=item["total_price"]

            )

            db.session.add(
                purchase_order_item
            )


        # =================================================
        # SAVE EVERYTHING
        # =================================================

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "Unable to create the LPO. Please try again.",
                "danger"
            )

            return render_template(
                "procurement/purchase_order_form.html",
                suppliers=suppliers,
                user=session.get("user"),
                role=session.get("role")
            )


        # =================================================
        # SUCCESS
        # =================================================

        flash(
            f"LPO {lpo_number} created successfully.",
            "success"
        )


        return redirect(
            url_for(
                "purchase_order_detail",
                order_id=purchase_order.id
            )
        )


    # =====================================================
    # GET
    # =====================================================

    return render_template(
        "procurement/purchase_order_form.html",
        suppliers=suppliers,
        user=session.get("user"),
        role=session.get("role")
    )


@app.route("/procurement/lpos/<int:order_id>")
@require_roles("admin", "accounts", "superadmin")
def purchase_order_detail(order_id):

    purchase_order = PurchaseOrder.query.get_or_404(
        order_id
    )

    return render_template(
        "procurement/purchase_order_detail.html",
        purchase_order=purchase_order,
        user=session.get("user"),
        role=session.get("role")
    )

@app.route(
    "/procurement/lpos/<int:order_id>/items/add",
    methods=["POST"]
)
@require_roles("admin", "accounts", "superadmin")
def add_purchase_order_item(order_id):

    purchase_order = PurchaseOrder.query.get_or_404(
        order_id
    )

    item_description = request.form.get(
        "item_description",
        ""
    ).strip()

    quantity_raw = request.form.get(
        "quantity",
        ""
    ).strip()

    unit_price_raw = request.form.get(
        "unit_price",
        ""
    ).strip()

    notes = request.form.get(
        "notes",
        ""
    ).strip()


    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    if not item_description:

        flash(
            "Please enter an item description.",
            "danger"
        )

        return redirect(
            url_for(
                "purchase_order_detail",
                order_id=order_id
            )
        )


    try:

        quantity = float(
            quantity_raw
        )

    except (TypeError, ValueError):

        flash(
            "Please enter a valid quantity.",
            "danger"
        )

        return redirect(
            url_for(
                "purchase_order_detail",
                order_id=order_id
            )
        )


    if quantity <= 0:

        flash(
            "Quantity must be greater than zero.",
            "danger"
        )

        return redirect(
            url_for(
                "purchase_order_detail",
                order_id=order_id
            )
        )


    try:

        unit_price = float(
            unit_price_raw
        )

    except (TypeError, ValueError):

        flash(
            "Please enter a valid unit price.",
            "danger"
        )

        return redirect(
            url_for(
                "purchase_order_detail",
                order_id=order_id
            )
        )


    if unit_price < 0:

        flash(
            "Unit price cannot be negative.",
            "danger"
        )

        return redirect(
            url_for(
                "purchase_order_detail",
                order_id=order_id
            )
        )


    # ---------------------------------------------------------
    # CALCULATE ITEM TOTAL
    # ---------------------------------------------------------

    total_price = quantity * unit_price


    # ---------------------------------------------------------
    # CREATE ITEM
    # ---------------------------------------------------------

    item = PurchaseOrderItem(

        purchase_order_id=purchase_order.id,

        item_description=item_description,

        quantity=quantity,

        unit_price=unit_price,

        total_price=total_price,

        notes=notes or None

    )

    db.session.add(item)


    # ---------------------------------------------------------
    # UPDATE LPO TOTAL
    # ---------------------------------------------------------

    purchase_order.total_amount = sum(
        existing_item.total_price or 0
        for existing_item in purchase_order.items
    ) + total_price


    db.session.commit()


    flash(
        "LPO item added successfully.",
        "success"
    )


    return redirect(
        url_for(
            "purchase_order_detail",
            order_id=order_id
        )
    )


@app.route(
    "/procurement/lpos/<int:order_id>/items/<int:item_id>/delete",
    methods=["POST"]
)
@require_roles("admin", "accounts", "superadmin")
def delete_purchase_order_item(
    order_id,
    item_id
):

    purchase_order = PurchaseOrder.query.get_or_404(
        order_id
    )

    item = PurchaseOrderItem.query.filter_by(
        id=item_id,
        purchase_order_id=purchase_order.id
    ).first_or_404()


    db.session.delete(item)

    db.session.flush()

    purchase_order.total_amount = sum(
        existing_item.total_price or 0
        for existing_item in purchase_order.items
    )

    db.session.commit()

    # ---------------------------------------------------------
    # RECALCULATE TOTAL
    # ---------------------------------------------------------

    purchase_order.total_amount = sum(
        existing_item.total_price or 0
        for existing_item in purchase_order.items
        if existing_item.id != item_id
    )


    db.session.commit()


    flash(
        "LPO item removed successfully.",
        "success"
    )


    return redirect(
        url_for(
            "purchase_order_detail",
            order_id=order_id
        )
    )

@app.route(
    "/procurement/goods-received/new",
    methods=["GET", "POST"]
)
@require_roles("admin", "accounts", "superadmin")
def new_goods_receipt():

    purchase_orders = PurchaseOrder.query.filter(
        PurchaseOrder.status.in_([
            "Draft",
            "Ordered",
            "Confirmed",
            "Partially Received"
        ])
    ).order_by(
        PurchaseOrder.order_date.desc()
    ).all()

    if request.method == "POST":

        purchase_order_id = request.form.get(
            "purchase_order_id"
        )

        received_date = request.form.get(
            "received_date"
        )

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        # -------------------------------------------------
        # VALIDATE LPO
        # -------------------------------------------------

        if not purchase_order_id:

            flash(
                "Please select an LPO.",
                "danger"
            )

            return render_template(
                "procurement/goods_receipt_form.html",
                purchase_orders=purchase_orders,
                user=session.get("user"),
                role=session.get("role")
            )

        purchase_order = PurchaseOrder.query.get(
            int(purchase_order_id)
        )

        if not purchase_order:

            flash(
                "Selected LPO was not found.",
                "danger"
            )

            return render_template(
                "procurement/goods_receipt_form.html",
                purchase_orders=purchase_orders,
                user=session.get("user"),
                role=session.get("role")
            )

        # -------------------------------------------------
        # DATE
        # -------------------------------------------------

        received_date_value = datetime.utcnow()

        if received_date:

            try:

                received_date_value = datetime.strptime(
                    received_date,
                    "%Y-%m-%d"
                )

            except ValueError:

                flash(
                    "Invalid received date.",
                    "danger"
                )

                return render_template(
                    "procurement/goods_receipt_form.html",
                    purchase_orders=purchase_orders,
                    user=session.get("user"),
                    role=session.get("role")
                )

        # -------------------------------------------------
        # GENERATE GRN NUMBER
        # -------------------------------------------------

        today = datetime.utcnow().strftime("%Y%m%d")

        existing_count = GoodsReceipt.query.filter(
            GoodsReceipt.grn_number.like(
                f"GRN-{today}-%"
            )
        ).count()

        grn_number = (
            f"GRN-{today}-{existing_count + 1:04d}"
        )

        # -------------------------------------------------
        # CREATE GRN
        # -------------------------------------------------

        goods_receipt = GoodsReceipt(

            purchase_order_id=purchase_order.id,

            grn_number=grn_number,

            received_date=received_date_value,

            received_by=session.get("user_id"),

            status="Received",

            notes=notes or None

        )

        db.session.add(
            goods_receipt
        )

        db.session.flush()

        # -------------------------------------------------
        # PROCESS LPO ITEMS
        # -------------------------------------------------

        has_received_items = False

        for item in purchase_order.items:

            quantity_raw = request.form.get(
                f"quantity_{item.id}",
                "0"
            ).strip()

            try:

                quantity_received = float(
                    quantity_raw
                )

            except (TypeError, ValueError):

                quantity_received = 0

            if quantity_received <= 0:
                continue

            # ---------------------------------------------
            # CHECK PREVIOUSLY RECEIVED
            # ---------------------------------------------

            previously_received = db.session.query(
                db.func.coalesce(
                    db.func.sum(
                        GoodsReceiptItem.quantity_received
                    ),
                    0
                )
            ).filter(
                GoodsReceiptItem.purchase_order_item_id
                == item.id
            ).scalar()

            previously_received = float(
                previously_received or 0
            )

            outstanding = (
                float(item.quantity)
                - previously_received
            )

            if quantity_received > outstanding:

                db.session.rollback()

                flash(
                    f"Received quantity for "
                    f"{item.item_description} cannot exceed "
                    f"the outstanding quantity of "
                    f"{outstanding:g}.",
                    "danger"
                )

                return render_template(
                    "procurement/goods_receipt_form.html",
                    purchase_orders=purchase_orders,
                    selected_order=purchase_order,
                    user=session.get("user"),
                    role=session.get("role")
                )

            # ---------------------------------------------
            # CREATE RECEIPT ITEM
            # ---------------------------------------------

            receipt_item = GoodsReceiptItem(

                goods_receipt_id=goods_receipt.id,

                purchase_order_item_id=item.id,

                quantity_received=quantity_received

            )

            db.session.add(
                receipt_item
            )

            has_received_items = True

        # -------------------------------------------------
        # REQUIRE AT LEAST ONE ITEM
        # -------------------------------------------------

        if not has_received_items:

            db.session.rollback()

            flash(
                "Please enter a quantity for at least one item.",
                "danger"
            )

            return render_template(
                "procurement/goods_receipt_form.html",
                purchase_orders=purchase_orders,
                selected_order=purchase_order,
                user=session.get("user"),
                role=session.get("role")
            )

        db.session.flush()

        # -------------------------------------------------
        # DETERMINE LPO RECEIVING STATUS
        # -------------------------------------------------

        fully_received = True

        for item in purchase_order.items:

            previously_received = db.session.query(
                db.func.coalesce(
                    db.func.sum(
                        GoodsReceiptItem.quantity_received
                    ),
                    0
                )
            ).filter(
                GoodsReceiptItem.purchase_order_item_id
                == item.id
            ).scalar()

            total_received = float(
                previously_received or 0
            )

            if total_received < float(item.quantity):

                fully_received = False

                break

        if fully_received:

            purchase_order.status = "Received"

        else:

            purchase_order.status = "Partially Received"

        db.session.commit()

        flash(
            f"{grn_number} recorded successfully.",
            "success"
        )

        return redirect(
            url_for(
                "goods_receipt_detail",
                receipt_id=goods_receipt.id
            )
        )

    return render_template(
        "procurement/goods_receipt_form.html",
        purchase_orders=purchase_orders,
        user=session.get("user"),
        role=session.get("role")
    )



@app.route(
    "/procurement/goods-received/<int:receipt_id>"
)
@require_roles("admin", "accounts", "superadmin")
def goods_receipt_detail(receipt_id):

    goods_receipt = GoodsReceipt.query.get_or_404(
        receipt_id
    )

    return render_template(
        "procurement/goods_receipt_detail.html",
        goods_receipt=goods_receipt,
        user=session.get("user"),
        role=session.get("role")
    )


@app.route("/procurement/supplier-bills/new", methods=["GET", "POST"])
@require_roles("admin", "accounts", "superadmin")
def new_supplier_bill():

    suppliers = Supplier.query.filter_by(
        status="Active"
    ).order_by(
        Supplier.supplier_name.asc()
    ).all()

    if request.method == "POST":

        supplier_id = request.form.get("supplier_id")
        bill_number = request.form.get(
            "bill_number", ""
        ).strip()

        bill_date = request.form.get("bill_date")
        due_date = request.form.get("due_date")

        description = request.form.get(
            "description", ""
        ).strip()

        amount_raw = request.form.get(
            "amount", ""
        ).strip()

        notes = request.form.get(
            "notes", ""
        ).strip()

        # -----------------------------------------
        # VALIDATION
        # -----------------------------------------

        if not supplier_id:
            flash(
                "Please select a supplier.",
                "danger"
            )
            return render_template(
                "procurement/supplier_bill_form.html",
                suppliers=suppliers,
                user=session.get("user"),
                role=session.get("role")
            )

        if not bill_number:
            flash(
                "Supplier invoice number is required.",
                "danger"
            )
            return render_template(
                "procurement/supplier_bill_form.html",
                suppliers=suppliers,
                user=session.get("user"),
                role=session.get("role")
            )

        existing_bill = SupplierBill.query.filter_by(
            bill_number=bill_number
        ).first()

        if existing_bill:
            flash(
                "A supplier bill with this invoice number already exists.",
                "danger"
            )
            return render_template(
                "procurement/supplier_bill_form.html",
                suppliers=suppliers,
                user=session.get("user"),
                role=session.get("role")
            )

        try:
            amount = float(amount_raw)
        except (TypeError, ValueError):
            flash(
                "Please enter a valid invoice amount.",
                "danger"
            )
            return render_template(
                "procurement/supplier_bill_form.html",
                suppliers=suppliers,
                user=session.get("user"),
                role=session.get("role")
            )

        if amount <= 0:
            flash(
                "Invoice amount must be greater than zero.",
                "danger"
            )
            return render_template(
                "procurement/supplier_bill_form.html",
                suppliers=suppliers,
                user=session.get("user"),
                role=session.get("role")
            )

        # -----------------------------------------
        # DATE CONVERSION
        # -----------------------------------------

        bill_date_value = None
        due_date_value = None

        if bill_date:
            try:
                bill_date_value = datetime.strptime(
                    bill_date,
                    "%Y-%m-%d"
                )
            except ValueError:
                flash(
                    "Invalid invoice date.",
                    "danger"
                )
                return render_template(
                    "procurement/supplier_bill_form.html",
                    suppliers=suppliers,
                    user=session.get("user"),
                    role=session.get("role")
                )

        if due_date:
            try:
                due_date_value = datetime.strptime(
                    due_date,
                    "%Y-%m-%d"
                )
            except ValueError:
                flash(
                    "Invalid due date.",
                    "danger"
                )
                return render_template(
                    "procurement/supplier_bill_form.html",
                    suppliers=suppliers,
                    user=session.get("user"),
                    role=session.get("role")
                )

        # -----------------------------------------
        # CREATE SUPPLIER BILL
        # -----------------------------------------

        bill = SupplierBill(
            supplier_id=int(supplier_id),
            bill_number=bill_number,
            bill_date=bill_date_value or datetime.utcnow(),
            due_date=due_date_value,
            description=description or None,
            amount=amount,
            amount_paid=0.0,
            balance=amount,
            status="Unpaid",
            notes=notes or None
        )

        db.session.add(bill)
        db.session.commit()

        return redirect(
            url_for(
                "procurement",
                tab="procurement-invoices",
                notification="Supplier invoice recorded successfully."
            )
        )

    return render_template(
        "procurement/supplier_bill_form.html",
        suppliers=suppliers,
        user=session.get("user"),
        role=session.get("role")
    )


@app.route(
    "/procurement/supplier-bills/<int:bill_id>/payment",
    methods=["GET", "POST"]
)
@require_roles("admin", "accounts", "superadmin")
def supplier_bill_payment(bill_id):

    bill = SupplierBill.query.get_or_404(bill_id)

    balance = (
        bill.amount -
        (bill.amount_paid or 0.0)
    )

    # ---------------------------------------------------------
    # ALREADY PAID
    # ---------------------------------------------------------

    if balance <= 0:

        flash(
            "This supplier invoice has already been fully paid.",
            "warning"
        )

        return redirect(
            url_for(
                "procurement",
                tab="procurement-invoices"
            )
        )


    # ---------------------------------------------------------
    # GENERATE PAYMENT REFERENCE
    # ---------------------------------------------------------

    today = datetime.utcnow().strftime("%Y%m%d")

    payment_count = SupplierPayment.query.filter(
        SupplierPayment.payment_reference.like(
            f"PAY-{today}-%"
        )
    ).count()

    payment_reference = (
        f"PAY-{today}-{payment_count + 1:04d}"
    )


    # ---------------------------------------------------------
    # POST
    # ---------------------------------------------------------

    if request.method == "POST":

        amount_raw = request.form.get(
            "amount",
            ""
        ).strip()

        payment_method = request.form.get(
            "payment_method",
            ""
        ).strip()

        receipt_number = request.form.get(
            "receipt_number",
            ""
        ).strip()

        paid_at_raw = request.form.get(
            "paid_at",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()


        # -----------------------------------------------------
        # AMOUNT
        # -----------------------------------------------------

        try:

            payment_amount = float(
                amount_raw
            )

        except (TypeError, ValueError):

            flash(
                "Please enter a valid payment amount.",
                "danger"
            )

            return render_template(
                "procurement/supplier_payment_form.html",
                bill=bill,
                balance=balance,
                payment_reference=payment_reference,
                user=session.get("user"),
                role=session.get("role")
            )


        if payment_amount <= 0:

            flash(
                "Payment amount must be greater than zero.",
                "danger"
            )

            return render_template(
                "procurement/supplier_payment_form.html",
                bill=bill,
                balance=balance,
                payment_reference=payment_reference,
                user=session.get("user"),
                role=session.get("role")
            )


        # -----------------------------------------------------
        # PREVENT OVERPAYMENT
        # -----------------------------------------------------

        if payment_amount > balance:

            flash(
                "Payment cannot exceed the outstanding balance.",
                "danger"
            )

            return render_template(
                "procurement/supplier_payment_form.html",
                bill=bill,
                balance=balance,
                payment_reference=payment_reference,
                user=session.get("user"),
                role=session.get("role")
            )


        # -----------------------------------------------------
        # PAYMENT METHOD
        # -----------------------------------------------------

        if not payment_method:

            flash(
                "Please select a payment method.",
                "danger"
            )

            return render_template(
                "procurement/supplier_payment_form.html",
                bill=bill,
                balance=balance,
                payment_reference=payment_reference,
                user=session.get("user"),
                role=session.get("role")
            )


        # -----------------------------------------------------
        # PAYMENT DATE
        # -----------------------------------------------------

        paid_at_value = datetime.utcnow()

        if paid_at_raw:

            try:

                paid_at_value = datetime.strptime(
                    paid_at_raw,
                    "%Y-%m-%d"
                )

            except ValueError:

                flash(
                    "Invalid payment date.",
                    "danger"
                )

                return render_template(
                    "procurement/supplier_payment_form.html",
                    bill=bill,
                    balance=balance,
                    payment_reference=payment_reference,
                    user=session.get("user"),
                    role=session.get("role")
                )


        # -----------------------------------------------------
        # CREATE PAYMENT
        # -----------------------------------------------------

        payment = SupplierPayment(

            supplier_bill_id=bill.id,

            amount=payment_amount,

            payment_method=payment_method,

            payment_reference=payment_reference,

            receipt_number=receipt_number or None,

            paid_at=paid_at_value,

            notes=notes or None

        )

        db.session.add(payment)


        # -----------------------------------------------------
        # UPDATE BILL
        # -----------------------------------------------------

        bill.amount_paid = (
            (bill.amount_paid or 0.0)
            + payment_amount
        )

        bill.balance = (
            bill.amount -
            bill.amount_paid
        )


        # -----------------------------------------------------
        # STATUS
        # -----------------------------------------------------

        if bill.balance <= 0:

            bill.balance = 0.0
            bill.status = "Paid"

        elif bill.amount_paid > 0:

            bill.status = "Partial"

        else:

            bill.status = "Unpaid"


        # -----------------------------------------------------
        # SAVE
        # -----------------------------------------------------

        db.session.commit()


        flash(
            "Supplier payment recorded successfully.",
            "success"
        )


        return redirect(
            url_for(
                "supplier_bill_detail",
                bill_id=bill.id
            )
        )


    # ---------------------------------------------------------
    # FORM
    # ---------------------------------------------------------

    return render_template(
        "procurement/supplier_payment_form.html",
        bill=bill,
        balance=balance,
        payment_reference=payment_reference,
        user=session.get("user"),
        role=session.get("role")
    )


@app.route("/inventory")
@require_roles("admin", "accounts", "mechanic", "superadmin")
def inventory():
    return render_template(
    "inventory.html",
    user=session.get("user"),
    role=session.get("role")
    )

@app.route("/procurement/supplier-bills")
@require_roles("admin", "accounts", "superadmin")
def supplier_bills():

    bills = (
        SupplierBill.query
        .join(Supplier)
        .order_by(SupplierBill.bill_date.desc())
        .all()
    )

    return render_template(
        "procurement/supplier_bills.html",
        bills=bills,
        user=session.get("user"),
        role=session.get("role")
    )

@app.route("/procurement/supplier-bills/<int:bill_id>")
@require_roles("admin", "accounts", "superadmin")
def supplier_bill_detail(bill_id):

    bill = SupplierBill.query.get_or_404(bill_id)

    return render_template(
        "procurement/supplier_bill_detail.html",
        bill=bill,
        user=session.get("user"),
        role=session.get("role")
    )

@app.route("/dashboard/accounts")
@require_roles("accounts", "admin", "superadmin")
def accounts_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    role = session["role"]

    # Only accounts users should hit this route
    if role != "accounts":
        abort(403)

    total_jobs = Jobs.query.count()
    open_jobs = Jobs.query.filter_by(status="Open").count()
    completed_jobs = Jobs.query.filter_by(status="Complete").count()

    # 💰 Revenue (Paid invoices)
    revenue = (
        db.session.query(func.coalesce(func.sum(Invoice.total_amount), 0))
        .filter(Invoice.status == "Paid")
        .scalar()
    )

    # 📉 Debt (Unpaid invoices)
    debt = (
        db.session.query(func.coalesce(func.sum(Invoice.total_amount), 0))
        .filter(Invoice.status == "Unpaid")
        .scalar()
    )

    now = datetime.now()   # ✅ current date and time

    return render_template(
        "admin/dashboard.html",  # 👈 different template
        user=session["user"],
        role=role,
        total_jobs=total_jobs,
        open_jobs=open_jobs,
        completed_jobs=completed_jobs,
        revenue=revenue,
        debt=debt,
        now=now
    )
#================user management=========================

@app.route("/users")
@require_roles("admin", "superadmin")
def users():

    users = User.query.order_by(User.username).all()

    return render_template(
        "admin/users/users.html",
        users=users,
        user=session["user"],
        role=session["role"]
    )


@app.route("/admin/users/create", methods=["GET", "POST"])
@require_roles("admin", "superadmin")
def create_user():

    if request.method == "POST":
        user = User(
            username=request.form["username"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            role=request.form["role"]
        )

        db.session.add(user)
        db.session.commit()

        flash("User created successfully", "success")
        return redirect(url_for("users"))

    return render_template(
        "admin/users/create.html",
        role=session.get("role"),
        user=session.get("user")
    )


@app.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@require_roles("admin", "superadmin")
def toggle_user(user_id):

    user = User.query.get_or_404(user_id)

    if user.id == session.get("user_id"):
        flash("You cannot deactivate your own account.", "warning")
        return redirect(url_for("users"))

    user.is_active = not user.is_active
    db.session.commit()

    flash("User status updated", "success")
    return redirect(url_for("users"))

@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@require_roles("admin", "superadmin")
def delete_user(user_id):

    role = session.get("role")
    current_user_id = session.get("user_id")

    # 🔒 Nobody can delete themselves
    if user_id == current_user_id:
        flash("You cannot delete your own account.", "warning")
        return redirect(request.referrer or url_for("users"))

    user = User.query.get_or_404(user_id)

    # 🔒 Admin cannot delete superadmin
    if role == "admin" and user.role == "superadmin":
        flash("Admins cannot delete superadmin accounts.", "danger")
        return redirect(request.referrer or url_for("users"))

    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully.", "success")
    return redirect(request.referrer or url_for("users"))

@app.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@require_roles("admin", "superadmin")
def edit_user(user_id):

    role = session.get("role")
    current_user_id = session.get("user_id")

    # 🔒 Cannot edit yourself
    if user_id == current_user_id:
        flash("You cannot edit your own account.", "warning")
        return redirect(url_for("users"))

    target_user = User.query.get_or_404(user_id)

    # 🔒 Admin cannot edit superadmin
    if role == "admin" and target_user.role == "superadmin":
        flash("Admins cannot edit superadmin accounts.", "danger")
        return redirect(url_for("users"))

    if request.method == "POST":

        new_role = request.form["role"]

        # 🔒 Prevent admin creating superadmin
        if role == "admin" and new_role == "superadmin":
            flash("Admins cannot promote users to superadmin.", "danger")
            return redirect(url_for("users"))

        target_user.username = request.form["username"]
        target_user.role = new_role
        target_user.is_active = True if request.form.get("is_active") else False

        db.session.commit()

        flash("User updated successfully.", "success")
        return redirect(url_for("users"))

    return render_template(
        "admin/users/edit.html",
        u=target_user,
        role=role
    )


@app.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
@require_roles("admin", "superadmin")
def edit_customer(customer_id):

    role = session.get("role")

    target_customer = Customer.query.get_or_404(customer_id)

    if request.method == "POST":

        new_class = request.form["customer_class"]

        target_customer.customer_name = request.form["customer_name"]
        target_customer.telno = request.form["telno"]
        target_customer.email = request.form["email"]
        target_customer.customer_class = new_class
        target_customer.address = request.form["address"]

        db.session.commit()

        flash("Customer updated successfully.", "success")
        return redirect(url_for("customers"))

    return render_template(
        "customers/edit.html",
        customer=target_customer,
        role=role
    )
##### CREATE JOB ROUTE ####

@app.route("/jobs/create", methods=["GET", "POST"])
def create_job():

    if request.method == "POST":

        customer_id = request.form.get("customer_id")
        vehicle_id = request.form.get("vehicle_id")
        service_type = request.form.get("service_type")
        description = request.form.get("description")
        mechanic_id = request.form.get("mechanic_id")
        deadline_str = request.form.get("deadline")

        # -----------------------------
        # VALIDATE CUSTOMER
        # -----------------------------

        if not customer_id:
            flash("Please select a customer", "danger")
            return redirect(url_for("create_job"))

        customer = Customer.query.get(customer_id)

        if not customer:
            flash("Invalid customer selected", "danger")
            return redirect(url_for("create_job"))

        # -----------------------------
        # VALIDATE VEHICLE
        # -----------------------------

        vehicle = Vehicle.query.get(vehicle_id) if vehicle_id else None

        if not vehicle:
            flash("Please select a vehicle", "danger")
            return redirect(url_for("create_job"))

        # -----------------------------
        # VALIDATE SERVICE TYPE
        # -----------------------------

        if not service_type:
            flash("Please select a service type", "danger")
            return redirect(url_for("create_job"))

        # -----------------------------
        # DEADLINE
        # -----------------------------

        deadline = None

        if deadline_str:
            try:
                deadline = datetime.strptime(
                    deadline_str,
                    "%Y-%m-%dT%H:%M"
                )
            except ValueError:
                flash("Invalid deadline.", "danger")
                return redirect(url_for("create_job"))

        # -----------------------------
        # CREATE JOB
        # -----------------------------

        job = Jobs(
            customer_id=customer.id,
            customer_name=customer.customer_name,
            vehicle_id=vehicle.id,
            telno=customer.telno,
            vehicle=vehicle.registration_no,
            vehicle_model=vehicle.model,

            # NEW
            service_type=service_type,

            description=description,
            assigned_to=mechanic_id,
            deadline=deadline,
            status="Open"
        )

        db.session.add(job)
        db.session.commit()

        # -----------------------------
        # SHOW JOB CARD MODAL
        # -----------------------------

        customers = Customer.query.all()
        mechanics = User.query.filter_by(role="mechanic").all()

        return render_template(
            "jobs/create.html",
            customers=customers,
            mechanics=mechanics,
            role=session.get("role"),
            show_job_card_modal=True,
            created_job=job
        )

    # -----------------------------
    # GET
    # -----------------------------

    customers = Customer.query.all()

    mechanics = User.query.filter_by(
        role="mechanic"
    ).all()

    return render_template(
        "jobs/create.html",
        customers=customers,
        mechanics=mechanics,
        role=session.get("role")
    )
## JOB CARD ROUTE ##

@app.route("/jobs/<int:job_id>/create-job-card", methods=["GET", "POST"])
@require_roles("admin", "superadmin", "accounts", "mechanic")
def create_job_card(job_id):

    job = Jobs.query.get_or_404(job_id)

    # Prevent duplicate Job Cards
    if job.job_card:
        flash("A job card already exists for this job.", "warning")
        return redirect(url_for("job_detail", job_id=job.id))

    if request.method == "POST":

        work_description = request.form.get(
            "work_description", ""
        ).strip()

        technician_notes = request.form.get(
            "technician_notes", ""
        ).strip()

        if not work_description:
            flash(
                "Please enter the work description.",
                "danger"
            )

            return render_template(
                "jobs/create_job_card.html",
                job=job,
                role=session.get("role"),
                user=session.get("user")
            )

        try:

            # =========================================
            # CREATE JOB CARD
            # =========================================

            job_card_status = (
                "Completed"
                if job.status.lower() == "complete"
                else "Open"
            )

            job_card = JobCard(
                job_id=job.id,
                job_card_number=generate_job_card_number(),
                work_description=work_description,
                technician_notes=technician_notes,
                status=job_card_status,
                completed_at=(
                    datetime.utcnow()
                    if job_card_status == "Completed"
                    else None
                )
            )

            db.session.add(job_card)

            # =========================================
            # PARTS
            # =========================================

            part_names = request.form.getlist("part_name[]")
            part_numbers = request.form.getlist("part_number[]")
            part_quantities = request.form.getlist("part_quantity[]")

            # Selling price charged to customer
            part_unit_prices = request.form.getlist(
                "part_unit_price[]"
            )

            # Actual cost to garage
            part_unit_costs = request.form.getlist(
                "part_unit_cost[]"
            )


            for i, part_name in enumerate(part_names):

                part_name = part_name.strip()

                if not part_name:
                    continue

                quantity = 0
                unit_price = 0
                unit_cost = 0

                if i < len(part_quantities):
                    quantity = float(
                        part_quantities[i] or 0
                    )

                if i < len(part_unit_prices):
                    unit_price = float(
                        part_unit_prices[i] or 0
                    )

                if i < len(part_unit_costs):
                    unit_cost = float(
                        part_unit_costs[i] or 0
                    )

                part_number = ""

                if i < len(part_numbers):
                    part_number = (
                        part_numbers[i] or ""
                    ).strip()

                # Actual amount paid by the garage
                cost_total = quantity * unit_cost

                # Amount charged to the customer
                selling_total = quantity * unit_price

                part = JobCardPart(
                    job_card=job_card,
                    part_name=part_name,
                    part_number=part_number,
                    quantity=quantity,
                    unit_cost=unit_cost,
                    cost_total=cost_total,
                    unit_price=unit_price,
                    total=selling_total
                )

                db.session.add(part)
            # =========================================
            # LABOUR
            # =========================================

            labour_descriptions = request.form.getlist(
                "labour_description[]"
            )

            labour_hours = request.form.getlist(
                "labour_hours[]"
            )

            # Amount charged to customer per hour
            labour_rates = request.form.getlist(
                "labour_hourly_rate[]"
            )

            # Actual garage labour cost per hour
            labour_costs = request.form.getlist(
                "labour_hourly_cost[]"
            )


            for i, description in enumerate(
                labour_descriptions
            ):

                description = description.strip()

                if not description:
                    continue

                hours = 0
                hourly_rate = 0
                hourly_cost = 0

                if i < len(labour_hours):
                    hours = float(
                        labour_hours[i] or 0
                    )

                if i < len(labour_rates):
                    hourly_rate = float(
                        labour_rates[i] or 0
                    )

                if i < len(labour_costs):
                    hourly_cost = float(
                        labour_costs[i] or 0
                    )

                # Actual labour cost
                cost_total = hours * hourly_cost

                # Amount charged to customer
                selling_total = hours * hourly_rate

                labour = JobCardLabour(
                    job_card=job_card,
                    description=description,
                    hours=hours,
                    hourly_cost=hourly_cost,
                    cost_total=cost_total,
                    hourly_rate=hourly_rate,
                    total=selling_total
                )

                db.session.add(labour)

            # =========================================
            # SAVE EVERYTHING TOGETHER
            # =========================================

            db.session.commit()

            flash(
                f"Job card {job_card.job_card_number} "
                "created successfully!",
                "success"
            )

            return redirect(
                url_for(
                    "job_detail",
                    job_id=job.id
                )
            )

        except (ValueError, TypeError) as e:

            db.session.rollback()

            print(
                "JOB CARD NUMBER/PRICE ERROR:",
                e
            )

            flash(
                "Please check the quantities, hours "
                "and prices.",
                "danger"
            )

            return render_template(
                "jobs/create_job_card.html",
                job=job,
                role=session.get("role"),
                user=session.get("user")
            )

        except Exception as e:

            db.session.rollback()

            print(
                "JOB CARD SAVE ERROR:",
                repr(e)
            )

            flash(
                "An error occurred while creating "
                "the job card.",
                "danger"
            )

            return render_template(
                "jobs/create_job_card.html",
                job=job,
                role=session.get("role"),
                user=session.get("user")
            )

    return render_template(
        "jobs/create_job_card.html",
        job=job,
        role=session.get("role"),
        user=session.get("user")
    )

####EDIT JOB ###

@app.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
def edit_job(job_id):

    if "user" not in session:
        return redirect(url_for("login"))

    job = Jobs.query.get_or_404(job_id)

    if request.method == "POST":

        job.description = request.form.get("description")
        job.status = request.form.get("status")
        job.assigned_to = request.form.get("mechanic_id")

        deadline = request.form.get("deadline")
        if deadline:
            job.deadline = datetime.strptime(deadline, "%Y-%m-%dT%H:%M")

        db.session.commit()

        flash("Job updated successfully!", "success")

        return redirect(url_for("job_detail", job_id=job.id))

    mechanics = User.query.filter_by(role="mechanic").all()

    return render_template(
        "jobs/edit_job.html",
        job=job,
        mechanics=mechanics,
        role=session.get("role")
    )
@app.route("/jobs/<int:job_id>/delete", methods=["POST"])
@require_roles("superadmin")
def delete_job(job_id):

    job = Jobs.query.get_or_404(job_id)

    if job.invoice:
        flash("Cannot delete a job that already has an invoice. Please engage admin", "danger")
        return redirect(url_for("jobs"))

    db.session.delete(job)
    db.session.commit()

    flash("Job deleted successfully.", "success")

    return redirect(url_for("jobs"))

@app.route("/customers")
def customers():

    if "user" not in session:
        return redirect(url_for("login"))

    page = request.args.get("page", 1, type=int)

    search = request.args.get("search", "").strip()

    customer_class = request.args.get(
        "customer_class",
        ""
    ).strip()


    query = Customer.query


    # =====================================================
    # SEARCH
    # =====================================================

    if search:

        search_term = f"%{search}%"

        query = query.filter(
            (Customer.customer_name.ilike(search_term)) |
            (Customer.customer_class.ilike(search_term)) |
            (Customer.telno.ilike(search_term)) |
            (Customer.email.ilike(search_term))
        )


    # =====================================================
    # CUSTOMER CLASS FILTER
    # =====================================================

    if customer_class:

        query = query.filter(
            Customer.customer_class == customer_class
        )


    # =====================================================
    # PAGINATION
    # =====================================================

    customers_paginated = (
        query
        .order_by(Customer.customer_name.asc())
        .paginate(
            page=page,
            per_page=20,
            error_out=False
        )
    )


    # =====================================================
    # CUSTOMER CLASS OPTIONS
    # =====================================================

    customer_classes = [
        row[0]
        for row in (
            db.session.query(Customer.customer_class)
            .filter(Customer.customer_class.isnot(None))
            .filter(Customer.customer_class != "")
            .distinct()
            .order_by(Customer.customer_class.asc())
            .all()
        )
    ]


    return render_template(
        "customers/index.html",

        customers=customers_paginated,

        customer_classes=customer_classes,

        search=search,

        active_class=customer_class,

        user=session["user"],

        role=session["role"],

        now=datetime.now()
    )


@app.route("/customers/export/excel")
def export_customers_excel():

    if "user" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()
    customer_class = request.args.get("customer_class", "").strip()

    query = Customer.query


    # =====================================================
    # SEARCH
    # =====================================================

    if search:

        search_term = f"%{search}%"

        query = query.filter(
            (Customer.customer_name.ilike(search_term)) |
            (Customer.customer_class.ilike(search_term)) |
            (Customer.telno.ilike(search_term)) |
            (Customer.email.ilike(search_term))
        )


    # =====================================================
    # CUSTOMER CLASS FILTER
    # =====================================================

    if customer_class:

        query = query.filter(
            Customer.customer_class == customer_class
        )


    # =====================================================
    # GET CUSTOMERS
    # =====================================================

    customers = (
        query
        .order_by(Customer.customer_name.asc())
        .all()
    )


    # =====================================================
    # BUILD EXPORT DATA
    # =====================================================

    data = []

    for customer in customers:

        data.append({
            "Customer ID": customer.id,
            "Full Name": customer.customer_name or "",
            "Customer Class": customer.customer_class or "",
            "Phone": customer.telno or "",
            "Email": customer.email or "",
            "Address": customer.address or "",
            "Status": customer.status or "",
            "Created": (
                customer.created_at.strftime("%Y-%m-%d")
                if customer.created_at
                else ""
            ),
        })


    # =====================================================
    # CREATE EXCEL FILE
    # =====================================================

    df = pd.DataFrame(data)

    output = io.BytesIO()

    df.to_excel(
        output,
        index=False
    )

    output.seek(0)


    return send_file(
        output,
        download_name="Customers.xlsx",
        as_attachment=True
    )

@app.route("/customers/export/csv")
def export_customers_csv():

    if "user" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()
    customer_class = request.args.get("customer_class", "").strip()

    query = Customer.query


    # =====================================================
    # SEARCH
    # =====================================================

    if search:

        search_term = f"%{search}%"

        query = query.filter(
            (Customer.customer_name.ilike(search_term)) |
            (Customer.customer_class.ilike(search_term)) |
            (Customer.telno.ilike(search_term)) |
            (Customer.email.ilike(search_term))
        )


    # =====================================================
    # CUSTOMER CLASS FILTER
    # =====================================================

    if customer_class:

        query = query.filter(
            Customer.customer_class == customer_class
        )


    # =====================================================
    # GET CUSTOMERS
    # =====================================================

    customers = (
        query
        .order_by(Customer.customer_name.asc())
        .all()
    )


    # =====================================================
    # BUILD EXPORT DATA
    # =====================================================

    data = []

    for customer in customers:

        data.append({
            "Customer ID": customer.id,
            "Full Name": customer.customer_name or "",
            "Customer Class": customer.customer_class or "",
            "Phone": customer.telno or "",
            "Email": customer.email or "",
            "Address": customer.address or "",
            "Status": customer.status or "",
            "Created": (
                customer.created_at.strftime("%Y-%m-%d")
                if customer.created_at
                else ""
            ),
        })


    # =====================================================
    # CREATE CSV FILE
    # =====================================================

    df = pd.DataFrame(data)

    output = io.BytesIO()

    df.to_csv(
        output,
        index=False
    )

    output.seek(0)


    return send_file(
        output,
        mimetype="text/csv",
        download_name="Customers.csv",
        as_attachment=True
    )

#####overdue jobs route
@app.route("/reports/overdue-jobs")

def overdue_jobs_report():

    overdue_jobs = Jobs.query.filter(
        Jobs.deadline < datetime.now(),
        Jobs.status != "Completed"
    ).order_by(Jobs.deadline.asc()).all()
    
    return render_template(
        "admin/reports/overdue_jobs_report.html",
        jobs=overdue_jobs,
        now=datetime.now(),
         current_user= current_user, username=session.get("user")
        
    )
    
@app.route("/vehicles")
def vehicles():
    if "user" not in session:
        return redirect(url_for("login"))

    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")

    query = Vehicle.query

    # 🔍 Apply search filter
    if search:
        query = query.join(Customer).filter(
            (Vehicle.registration_no.ilike(f"%{search}%")) |
            (Vehicle.model.ilike(f"%{search}%")) |
            (Customer.customer_name.ilike(f"%{search}%"))
        )

    vehicles_paginated = query.order_by(Vehicle.id.desc()).paginate(
        page=page,
        per_page=20,
        error_out=False
    )

    return render_template(
        "admin/vehicles/vehicles.html",
        vehicles=vehicles_paginated,
        user=session["user"],
        role=session["role"]
    )

from datetime import datetime

@app.route("/vehicles/<int:vehicle_id>")
def vehicle_details(vehicle_id):
    if "user" not in session:
        return redirect(url_for("login"))

    vehicle = Vehicle.query.get_or_404(vehicle_id)
    customer = Customer.query.get_or_404(vehicle.customer_id)

    jobs = Jobs.query.filter_by(vehicle_id=vehicle.id)\
        .order_by(Jobs.created_at.desc())\
        .all()

    return render_template(
        "admin/vehicles/vehicle_details.html",
        vehicle=vehicle,
        customer=customer,
        jobs=jobs,
        now=datetime.now(),  #added to be  displayed in the table 
        user=session.get("user"),
        role=session.get("role")
    )

@app.route("/customers/vehicle/create", methods=["GET", "POST"])
def create_vehicle():
    # Make sure the customer step was done
    if "new_customer_id" not in session:
        return redirect(url_for("create_customer"))
    
    # Only admin can create vehicle
    if session.get("role") != "admin":
        flash("Access denied: Only admin can register vehicle", "danger")
        return redirect(url_for("customers"))

    if request.method == "POST":
        vehicle = Vehicle(
            customer_id=session["new_customer_id"],
            registration_no=request.form["registration_no"],
            model=request.form["model"],
            color=request.form["color"],
            yom=request.form["yom"]
        )
        db.session.add(vehicle)
        db.session.commit()

        # clear session
        session.pop("new_customer_id", None)

        flash("Customer and vehicle registered successfully", "success")
        return redirect(url_for("customers"))

    return render_template(
        "customers/vehicle_create.html",
         user=session.get("user"),
        role=session.get("role")
    
    )

@app.route("/vehicles/<int:vehicle_id>/edit", methods=["GET", "POST"])
@require_roles("admin", "superadmin")
def edit_vehicle(vehicle_id):

    vehicle = Vehicle.query.get_or_404(vehicle_id)

    if request.method == "POST":
        vehicle.registration_no = request.form["registration_no"]
        vehicle.model = request.form["model"]
        vehicle.color = request.form["color"]
        vehicle.yom = request.form["yom"]

        db.session.commit()

        flash("Vehicle updated successfully.", "success")

        return redirect(url_for("vehicle_details", vehicle_id=vehicle.id))

    return render_template(
        "admin/vehicles/edit.html",
        vehicle=vehicle,
        user=session.get("user"),
        role=session.get("role")
    )

@app.route("/vehicles/<int:vehicle_id>/delete", methods=["POST"])
@require_roles("superadmin")
def delete_vehicle(vehicle_id):

    vehicle = Vehicle.query.get_or_404(vehicle_id)

    if Jobs.query.filter_by(vehicle_id=vehicle.id).first():
        flash("Cannot delete vehicle with existing jobs.", "danger")
        return redirect(url_for("vehicles"))

    db.session.delete(vehicle)
    db.session.commit()

    flash("Vehicle deleted successfully.", "success")
    return redirect(url_for("vehicles"))

@app.route("/vehicles/add", methods=["GET", "POST"])
@require_roles("admin", "accounts", "mechanic")
def add_vehicle():

    customers = Customer.query.order_by(Customer.customer_name).all()

    if request.method == "POST":

        new_vehicle = Vehicle(
            customer_id=request.form.get("customer_id"),
            registration_no=request.form.get("registration_no"),
            model=request.form.get("model"),
            color=request.form.get("color"),
            yom=request.form.get("yom"),
            owner=request.form.get("owner")
        )

        db.session.add(new_vehicle)
        db.session.commit()

        inspection = VehicleInspection(
            vehicle_id=new_vehicle.id,

            front_bumper=request.form.get("front_bumper"),
            rear_bumper=request.form.get("rear_bumper"),
            bonnet=request.form.get("bonnet"),
            roof=request.form.get("roof"),
            boot=request.form.get("boot"),

            left_front_fender=request.form.get("left_front_fender"),
            right_front_fender=request.form.get("right_front_fender"),
            left_rear_fender=request.form.get("left_rear_fender"),
            right_rear_fender=request.form.get("right_rear_fender"),

            left_front_door=request.form.get("left_front_door"),
            right_front_door=request.form.get("right_front_door"),
            left_rear_door=request.form.get("left_rear_door"),
            right_rear_door=request.form.get("right_rear_door"),

            windscreen=request.form.get("windscreen"),
            rear_screen=request.form.get("rear_screen"),
            mirrors=request.form.get("mirrors"),

            headlights=request.form.get("headlights"),
            tail_lights=request.form.get("tail_lights"),

            tyres=request.form.get("tyres"),

            outside_comments=request.form.get("outside_comments"),

            engine_oil=request.form.get("engine_oil"),
            coolant=request.form.get("coolant"),
            brake_fluid=request.form.get("brake_fluid"),
            steering_fluid=request.form.get("steering_fluid"),

            battery=request.form.get("battery"),
            belts=request.form.get("belts"),

            oil_leaks=request.form.get("oil_leaks"),
            coolant_leaks=request.form.get("coolant_leaks"),

            engine_comments=request.form.get("engine_comments"),

            seats=request.form.get("seats"),
            dashboard=request.form.get("dashboard"),
            steering_wheel=request.form.get("steering_wheel"),
            infotainment=request.form.get("infotainment"),
            radio=request.form.get("radio"),
            aircon=request.form.get("aircon"),
            horn=request.form.get("horn"),
            interior_lights=request.form.get("interior_lights"),

            fuel_level=request.form.get("fuel_level"),

            spare_wheel="spare_wheel" in request.form,
            jack="jack" in request.form,
            wheel_spanner="wheel_spanner" in request.form,
            toolkit="toolkit" in request.form,
            fire_extinguisher="fire_extinguisher" in request.form,
            warning_triangle="warning_triangle" in request.form,
            first_aid_kit="first_aid_kit" in request.form,

            interior_comments=request.form.get("interior_comments")
        )

        db.session.add(inspection)

        photos = request.files.getlist("photos")
        camera_photos = request.files.getlist("camera_photos")
        all_photos = photos + camera_photos

        for photo in all_photos:
            if photo and allowed_file(photo.filename):

                filename = secure_filename(photo.filename)
                unique_name = f"{uuid.uuid4().hex}_{filename}"

                photo.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        unique_name
                    )
                )

                db.session.add(
                    VehiclePhoto(
                        vehicle_id=new_vehicle.id,
                        filename=unique_name
                    )
                )

        db.session.commit()

        flash("Vehicle added successfully!", "success")
        return redirect(url_for("vehicles"))

    # GET REQUEST
    return render_template(
        "admin/vehicles/add_vehicle.html",
        customers=customers,
        user=session.get("user"),
        role=session.get("role")
    )


@app.route("/jobs/<int:job_id>/checklist")
@require_roles("admin", "superadmin", "accounts", "mechanic")
def vehicle_checklist(job_id):

    job = Jobs.query.get_or_404(job_id)

    inspection = VehicleInspection.query.filter_by(
        vehicle_id=job.vehicle_id
    ).first()

    if not inspection:
        flash("No inspection checklist found for this vehicle.", "warning")
        return redirect(url_for("job_detail", job_id=job.id))

    return render_template(
        "admin/vehicles/checklist.html",
        job=job,
        inspection=inspection,
        role=session.get("role"),
        user=session.get("user")
    )

@app.route("/inspection/<int:inspection_id>/download")
def download_inspection(inspection_id):

    inspection = VehicleInspection.query.get_or_404(
        inspection_id
    )

    # Find the job associated with this vehicle
    job = Jobs.query.filter_by(
        vehicle_id=inspection.vehicle_id
    ).order_by(
        Jobs.created_at.desc()
    ).first_or_404()

    # Generate the PDF using both inspection and job
    pdf = generate_inspection_pdf(
        inspection,
        job
    )

    return send_file(
        pdf,
        as_attachment=True,
        download_name=f"Job_{job.id}_Inspection.pdf",
        mimetype="application/pdf"
    )


@app.route("/vehicles/export/excel")
def export_vehicles_excel():
    if "user" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()

    query = Vehicle.query

    if search:
        search_term = f"%{search}%"

        query = query.filter(
            (Vehicle.registration_no.ilike(search_term)) |
            (Vehicle.model.ilike(search_term)) |
            (Vehicle.color.ilike(search_term))
        )

    vehicles = query.order_by(Vehicle.id.desc()).all()

    data = []

    for vehicle in vehicles:

        data.append({
            "Vehicle ID": vehicle.id,
            "Registration No.": vehicle.registration_no or "",
            "Model": vehicle.model or "",
            "Year of Manufacture": vehicle.yom or "",
            "Color": vehicle.color or "",
            "Customer": (
                vehicle.customer.customer_name
                if vehicle.customer
                else ""
            ),
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()

    df.to_excel(
        output,
        index=False
    )

    output.seek(0)

    return send_file(
        output,
        download_name="Vehicles.xlsx",
        as_attachment=True
    )

@app.route("/vehicles/export/csv")
def export_vehicles_csv():
    if "user" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()

    query = Vehicle.query

    if search:
        search_term = f"%{search}%"

        query = query.filter(
            (Vehicle.registration_no.ilike(search_term)) |
            (Vehicle.model.ilike(search_term)) |
            (Vehicle.color.ilike(search_term))
        )

    vehicles = query.order_by(Vehicle.id.desc()).all()

    data = []

    for vehicle in vehicles:

        data.append({
            "Vehicle ID": vehicle.id,
            "Registration No.": vehicle.registration_no or "",
            "Model": vehicle.model or "",
            "Year of Manufacture": vehicle.yom or "",
            "Color": vehicle.color or "",
            "Customer": (
                vehicle.customer.customer_name
                if vehicle.customer
                else ""
            ),
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()

    df.to_csv(
        output,
        index=False
    )

    output.seek(0)

    return send_file(
        output,
        mimetype="text/csv",
        download_name="Vehicles.csv",
        as_attachment=True
    )


@app.route("/customers/create", methods=["GET", "POST"]) 
def create_customer():
    # Only allow admin
    if session.get("role") != "admin":
        flash("Access denied: Only admin can create customers", "danger")
        return redirect(url_for("customers"))

    if request.method == "POST":
        customer = Customer(
            customer_name=request.form["customer_name"],
            telno=request.form["telno"],
            email=request.form["email"],
            customer_class=request.form["class"],
            address=request.form["address"]
        )
        db.session.add(customer)
        db.session.commit()

        flash("Customer and vehicle registered successfully", "success")
        return redirect(url_for("customers"))

    return render_template(
        "customers/create.html",
        user=session.get("user"),
        role=session.get("role")
    )

@app.route("/api/customer/<int:customer_id>")
def get_customer_info(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    vehicles = Vehicle.query.filter_by(customer_id=customer_id).all()
    return jsonify({
        "vehicle": [
            {"id": v.id, "registration_no": v.registration_no, "model": v.model}
            for v in vehicles
        ],
        "telno": customer.telno
    })

@app.route("/customers/<int:customer_id>")
def customer_details(customer_id):
    if "user" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        abort(403)

    customer = Customer.query.get_or_404(customer_id)

    vehicles = Vehicle.query.filter_by(customer_id=customer.id).all()

    job_counts = {
        v.id: Jobs.query.filter_by(vehicle_id=v.id).count()
        for v in vehicles
    }

    total_jobs = sum(job_counts.values())

    return render_template(
        "customers/details.html",
        customer=customer,          # ✅ REQUIRED
        vehicles=vehicles,
        job_counts=job_counts,
        total_jobs=total_jobs,
        role=session["role"]
    )

@app.route("/customers/<int:customer_id>/delete", methods=["POST"])
@require_roles("superadmin")
def delete_customer(customer_id):

    customer = Customer.query.get_or_404(customer_id)

    if Jobs.query.filter_by(customer_id=customer.id).first():
        flash("Cannot delete customer with existing jobs.", "danger")
        return redirect(url_for("customers"))

    db.session.delete(customer)
    db.session.commit()

    flash("Customer deleted successfully.", "success")
    return redirect(url_for("customers"))

@app.route("/superadmin/customers/<int:customer_id>/force_delete", methods=["POST"])
@require_roles("superadmin")
def force_delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    # Optional: delete all jobs and invoices associated with the customer
    for job in Jobs.query.filter_by(customer_id=customer.id).all():
        if job.invoice:
            db.session.delete(job.invoice)
        db.session.delete(job)

    # Vehicles will be deleted automatically due to cascade
    db.session.delete(customer)
    db.session.commit()

    flash("Customer and all related records deleted.", "success")
    return redirect(url_for("customers")) 

@app.route("/jobs")
def jobs():
    if "user" not in session:
        return redirect(url_for("login"))

    # ---------------------------------------------------------
    # GET PARAMETERS
    # ---------------------------------------------------------

    page = request.args.get("page", 1, type=int)

    search = request.args.get("search", "").strip()

    active_status = request.args.get("status", "").strip()


    # ---------------------------------------------------------
    # BASE QUERY
    # ---------------------------------------------------------

    query = Jobs.query.join(Customer)


    # ---------------------------------------------------------
    # SEARCH FILTER
    # ---------------------------------------------------------

    if search:

        query = query.filter(
            (Jobs.description.ilike(f"%{search}%")) |
            (Jobs.vehicle.ilike(f"%{search}%")) |
            (Customer.customer_name.ilike(f"%{search}%"))
        )


    # ---------------------------------------------------------
    # STATUS FILTER
    # ---------------------------------------------------------

    if active_status:

        query = query.filter(
            Jobs.status == active_status
        )


    # ---------------------------------------------------------
    # ORDER + PAGINATION
    # ---------------------------------------------------------

    jobs_paginated = (
        query
        .order_by(Jobs.created_at.desc())
        .paginate(
            page=page,
            per_page=20,
            error_out=False
        )
    )


    # ---------------------------------------------------------
    # RENDER
    # ---------------------------------------------------------

    return render_template(
        "jobs/list.html",

        jobs=jobs_paginated,

        user=session["user"],

        role=session["role"],

        active_status=active_status,

        search=search,

        now=datetime.now()
    )

@app.route("/jobs/<int:job_id>")
def job_detail(job_id):

    job = Jobs.query.get_or_404(job_id)

    invoice = Invoice.query.filter_by(job_id=job.id).first()

    job_card = JobCard.query.filter_by(
        job_id=job.id
    ).first()


    # =========================================
    # JOB CARD TOTALS & COSTING
    # =========================================

    parts_total = 0
    labour_total = 0

    parts_cost = 0
    labour_cost = 0

    if job_card:

        # -----------------------------
        # PARTS SELLING TOTAL
        # -----------------------------

        parts_total = sum(
            float(part.total or 0)
            for part in job_card.parts
        )


        # -----------------------------
        # LABOUR SELLING TOTAL
        # -----------------------------

        labour_total = sum(
            float(labour.total or 0)
            for labour in job_card.labour_items
        )


        # -----------------------------
        # PARTS ACTUAL COST
        # -----------------------------

        parts_cost = sum(
            float(part.cost_total or 0)
            for part in job_card.parts
        )


        # -----------------------------
        # LABOUR ACTUAL COST
        # -----------------------------

        labour_cost = sum(
            float(labour.cost_total or 0)
            for labour in job_card.labour_items
        )


    # =========================================
    # JOB CARD TOTAL
    # =========================================

    job_card_total = (
        parts_total +
        labour_total
    )


    # =========================================
    # TOTAL DIRECT JOB COST
    # =========================================

    total_job_cost = (
        parts_cost +
        labour_cost
    )


    # =========================================
    # JOB REVENUE
    # =========================================

    job_revenue = (
        parts_total +
        labour_total
    )


    # =========================================
    # GROSS PROFIT
    # =========================================

    gross_profit = (
        job_revenue -
        total_job_cost
    )


    # =========================================
    # GROSS MARGIN
    # =========================================

    gross_margin = (
        (gross_profit / job_revenue) * 100
        if job_revenue
        else 0
    )
    return render_template(
        "jobs/jobs_detail.html",
        job=job,
        invoice=invoice,
        job_card=job_card,
        parts_total=parts_total,
        labour_total=labour_total,
        job_card_total=job_card_total,
        parts_cost=parts_cost,
        labour_cost=labour_cost,
        total_job_cost=total_job_cost,
        job_revenue=job_revenue,
        gross_profit=gross_profit,
        gross_margin=gross_margin,
        user=session.get("user"),
        role=session.get("role")
    )

@app.route("/jobs/<int:job_id>/toggle_status", methods=["POST"])
@require_roles("admin", "superadmin", "accounts")
def toggle_job_status(job_id):

    job = Jobs.query.get_or_404(job_id)

    if job.status.lower() == "open":

        # Complete the job
        job.status = "Complete"

        # Complete the Job Card if one exists
        if job.job_card:
            job.job_card.status = "Completed"
            job.job_card.completed_at = datetime.utcnow()

    else:

        # Re-open the job
        if job.invoice:
            db.session.delete(job.invoice)

        job.status = "Open"

        # Re-open the Job Card if one exists
        if job.job_card:
            job.job_card.status = "Open"
            job.job_card.completed_at = None

    db.session.commit()

    return jsonify({
        "success": True,
        "new_status": job.status,
        "job_card_status": (
            job.job_card.status
            if job.job_card
            else None
        )
    })


@app.route("/jobs/export/excel")
def export_jobs_excel():

    if "user" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()

    query = Jobs.query

    # Search
    if search:
        query = query.filter(
            (Jobs.vehicle.ilike(f"%{search}%")) |
            (Jobs.customer_name.ilike(f"%{search}%")) |
            (Jobs.vehicle_model.ilike(f"%{search}%")) |
            (Jobs.description.ilike(f"%{search}%"))
        )

    # Status
    if status:
        query = query.filter(Jobs.status == status)

    jobs = query.order_by(Jobs.created_at.desc()).all()

    data = []

    for job in jobs:

        data.append({
            "Job ID": job.id,
            "Registration": job.vehicle or "",
            "Vehicle Model": job.vehicle_model or "",
            "Description": job.description or "",
            "Customer": job.customer_name or "",
            "Date": (
                job.created_at.strftime("%Y-%m-%d")
                if job.created_at
                else ""
            ),
            "Assigned Mechanic": (
                job.mechanic.username
                if job.mechanic
                else "Unassigned"
            ),
            "Deadline": (
                job.deadline.strftime("%Y-%m-%d")
                if job.deadline
                else ""
            ),
            "Status": job.status or "",
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()

    df.to_excel(
        output,
        index=False
    )

    output.seek(0)

    return send_file(
        output,
        download_name="Filtered_Jobs.xlsx",
        as_attachment=True
    )

@app.route("/jobs/export/csv")
def export_jobs_csv():

    if "user" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()

    query = Jobs.query

    # Search
    if search:
        query = query.filter(
            (Jobs.vehicle.ilike(f"%{search}%")) |
            (Jobs.customer_name.ilike(f"%{search}%")) |
            (Jobs.vehicle_model.ilike(f"%{search}%")) |
            (Jobs.description.ilike(f"%{search}%"))
        )

    # Status
    if status:
        query = query.filter(Jobs.status == status)

    jobs = query.order_by(Jobs.created_at.desc()).all()

    data = []

    for job in jobs:

        data.append({
            "Job ID": job.id,
            "Registration": job.vehicle or "",
            "Vehicle Model": job.vehicle_model or "",
            "Description": job.description or "",
            "Customer": job.customer_name or "",
            "Date": (
                job.created_at.strftime("%Y-%m-%d")
                if job.created_at
                else ""
            ),
            "Assigned Mechanic": (
                job.mechanic.username
                if job.mechanic
                else "Unassigned"
            ),
            "Deadline": (
                job.deadline.strftime("%Y-%m-%d")
                if job.deadline
                else ""
            ),
            "Status": job.status or "",
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()

    df.to_csv(
        output,
        index=False
    )

    output.seek(0)

    return send_file(
        output,
        mimetype="text/csv",
        download_name="Filtered_Jobs.csv",
        as_attachment=True
    )


#INVOICE SECRTION

@app.route("/invoices")
def invoices():
    if "user" not in session:
        return redirect(url_for("login"))

    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    customer = request.args.get("customer")
    status = request.args.get("status")

    query = db.session.query(Invoice, Jobs).join(Jobs, Invoice.job_id == Jobs.id)

    # 🔍 SEARCH
    if search:
        query = query.filter(
            (Jobs.vehicle.ilike(f"%{search}%")) |
            (Jobs.customer_name.ilike(f"%{search}%"))
        )

    # 🎯 FILTERS
    if customer:
        query = query.filter(Jobs.customer_name == customer)

    if status:
        query = query.filter(Invoice.status == status)

    invoices_paginated = query.order_by(
        Invoice.issue_date.desc()
    ).paginate(
        page=page,
        per_page=20,
        error_out=False
    )

    customers = db.session.query(Jobs.customer_name).distinct().all()
    customers = [c[0] for c in customers]

    return render_template(
        "admin/invoices/index.html",
        invoices=invoices_paginated,   # ✅ pass full pagination object
        customers=customers,
        role=session.get("role"),
        user=session.get("user")
    )
@app.route("/invoices/export/csv")
def export_invoices_csv():
    return "CSV export"

@app.route("/invoices/export/excel")
def export_invoices_excel():
    # Get filter params from query string
    customer_id = request.args.get("customer_id")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    status = request.args.get("status")

    # Build query
    query = db.session.query(Invoice, Jobs).join(Jobs)

    if customer_id:
        query = query.filter(Jobs.customer_id == customer_id)

    if status:
        query = query.filter(Invoice.status == status)

    invoices = query.all()

    # Prepare data for Excel
    data = []
    for invoice, job in invoices:
        data.append({
            "Invoice #": invoice.id,
            "Customer": job.customer_name,
            "Vehicle Reg": job.vehicle if job.vehicle else "",
            "Total": invoice.total_amount,
            "Status": invoice.status,
            "Date": invoice.issue_date.strftime("%Y-%m-%d"),
        })

    df = pd.DataFrame(data)

    # Export to Excel
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return send_file(
        output,
        download_name="Filtered_Invoices.xlsx",
        as_attachment=True
    )

@app.route("/reports")
def reports():

    return render_template(
        "admin/reports/reports.html",
        user=session.get("user"),
        role=session.get("role")
      )

@app.route("/statements")
def statements():
    if "user" not in session:
        return redirect(url_for("login"))

    query = db.session.query(Invoice, Jobs).join(Jobs, Invoice.job_id == Jobs.id)

    # Filters
    customer = request.args.get("customer")
    status = request.args.get("status")

    if customer:
        query = query.filter(Jobs.customer_name == customer)

    if status:
        query = query.filter(Invoice.status == status)

    invoices = query.order_by(Invoice.issue_date.desc()).all()

    # For customer dropdown
    customers = db.session.query(Jobs.customer_name).distinct().all()
    customers = [c[0] for c in customers]

    return render_template(
        "admin/reports/statement.html",
        invoices=invoices,
        customers=customers,
        role=session.get("role")
    )

            
@app.route("/jobs/<int:job_id>/satisfaction-note")
def satisfaction_note(job_id):

    if "user" not in session:
        return redirect(url_for("login"))

    job = Jobs.query.get_or_404(job_id)

    # Only completed jobs
    if job.status != "Complete":
        flash("Satisfaction notes can only be generated for completed jobs.", "warning")
        return redirect(url_for("job_detail", job_id=job.id))

    pdf = generate_satisfaction_note(job)

    return send_file(
        pdf,
        download_name=f"Satisfaction_Note_{job.id}.pdf",
        as_attachment=True,
        mimetype="application/pdf",
    )

@app.route("/invoice/<int:id>/pay", methods=["GET", "POST"])
def pay_invoice(id):

    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("role") not in ["admin", "accounts"]:
        abort(403)

    invoice = Invoice.query.get_or_404(id)

    # Recalculate before displaying the payment page
    calculate_invoice_payment_status(invoice)
    db.session.commit()

    if request.method == "POST":

        # ---------------------------------
        # PAYMENT AMOUNT
        # ---------------------------------

        try:
            payment_amount = float(
                request.form.get("amount", 0)
            )
        except (ValueError, TypeError):
            flash("Please enter a valid payment amount.", "danger")
            return redirect(url_for("pay_invoice", id=id))

        if payment_amount <= 0:
            flash("Payment amount must be greater than zero.", "danger")
            return redirect(url_for("pay_invoice", id=id))

        balance = float(invoice.Balance or 0)

        if balance <= 0:
            flash("This invoice has already been fully paid.", "info")
            return redirect(url_for("invoice_detail", invoice_id=id))

        # Prevent overpayment
        if payment_amount > balance:
            flash(
                f"Payment cannot exceed the outstanding balance of "
                f"KES {balance:,.2f}.",
                "danger"
            )
            return redirect(url_for("pay_invoice", id=id))

        # ---------------------------------
        # PAYMENT DETAILS
        # ---------------------------------

        method = request.form.get("payment_method")
        reference = request.form.get("payment_reference")
        notes = request.form.get("notes")

        if not method:
            flash("Please select a payment method.", "danger")
            return redirect(url_for("pay_invoice", id=id))

        # ---------------------------------
        # PAYMENT PROOF
        # ---------------------------------

        file = request.files.get("payment_proof")

        filename = None

        if file and file.filename:

            filename = secure_filename(file.filename)

            unique_filename = (
                f"{uuid.uuid4().hex}_{filename}"
            )

            file.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    unique_filename
                )
            )

            filename = unique_filename

        # ---------------------------------
        # CREATE PAYMENT
        # ---------------------------------

        payment = Payment(
            invoice_id=invoice.id,
            amount=payment_amount,
            payment_method=method,
            payment_reference=reference,
            payment_proof=filename,
            paid_at=datetime.utcnow(),
            receipt_number=generate_receipt_number(invoice.id),
            notes=notes
        )

        db.session.add(payment)

        # Flush so the payment becomes part of invoice.payments
        db.session.flush()

        # ---------------------------------
        # UPDATE INVOICE
        # ---------------------------------

        calculate_invoice_payment_status(invoice)

        db.session.commit()

        flash(
            f"Payment of KES {payment_amount:,.2f} recorded successfully.",
            "success"
        )

        return redirect(
            url_for(
                "invoice_detail",
                invoice_id=invoice.id
            )
        )

    return render_template(
        "admin/invoices/pay_invoice.html",
        invoice=invoice,
        role=session.get("role"),
        user=session.get("user")
    )

@app.route("/jobs/<int:job_id>/admin/invoices/create", methods=["GET", "POST"])
@require_roles("admin", "superadmin", "accounts")
def create_invoice(job_id):

    job = Jobs.query.get_or_404(job_id)

    # ---------------------------------------------------------
    # JOB CARD CHECK
    # ---------------------------------------------------------
    job_card = JobCard.query.filter_by(job_id=job.id).first()

    if not job_card:
        flash(
            "This job does not have a Job Card. "
            "Create the Job Card before creating an invoice.",
            "warning"
        )
        return redirect(url_for("job_detail", job_id=job.id))

    # ---------------------------------------------------------
    # PREVENT DUPLICATE INVOICES
    # ---------------------------------------------------------
    if job.invoice:
        flash(
            "This job has already been invoiced.",
            "warning"
        )
        return redirect(url_for("job_detail", job_id=job.id))

    # ---------------------------------------------------------
    # ONLY COMPLETED JOBS CAN BE INVOICED
    # ---------------------------------------------------------
    if (job.status or "").lower() != "complete":
        flash(
            "Only completed jobs can be invoiced.",
            "danger"
        )
        return redirect(url_for("job_detail", job_id=job.id))

    # ---------------------------------------------------------
    # CALCULATE PARTS
    # ---------------------------------------------------------
    parts_total = sum(
        float(part.quantity or 0) *
        float(part.unit_price or 0)
        for part in job_card.parts
    )

    # ---------------------------------------------------------
    # CALCULATE LABOUR
    # ---------------------------------------------------------
    labour_total = sum(
        float(labour.hours or 0) *
        float(labour.hourly_rate or 0)
        for labour in job_card.labour_items
    )

    # ---------------------------------------------------------
    # INVOICE TOTALS
    # ---------------------------------------------------------
    subtotal = parts_total + labour_total

    tax_rate = 16.0

    tax_amount = subtotal * (tax_rate / 100)

    total_amount = subtotal + tax_amount

    # ---------------------------------------------------------
    # CREATE INVOICE
    # ---------------------------------------------------------
    if request.method == "POST":

        try:

            invoice = Invoice(
                job_id=job.id,
                invoice_number=generate_invoice_number(),
                issue_date=datetime.utcnow(),

                subtotal=subtotal,

                tax_rate=tax_rate,
                tax_amount=tax_amount,

                total_amount=total_amount,

                amount=0.0,

                Balance=total_amount,

                status="Unpaid",

                notes=request.form.get(
                    "notes",
                    ""
                ).strip()
            )

            db.session.add(invoice)

            # -------------------------------------------------
            # FLUSH FIRST
            #
            # This gives us invoice.id before commit so that
            # InvoiceItem records can reference this invoice.
            # -------------------------------------------------
            db.session.flush()

            # =================================================
            # CREATE INVOICE ITEMS FROM JOB CARD PARTS
            # =================================================

            for part in job_card.parts:

                quantity = float(
                    part.quantity or 0
                )

                unit_price = float(
                    part.unit_price or 0
                )

                total = quantity * unit_price

                unit_cost = float(
                    part.unit_cost or 0
                )

                cost_total = float(
                    part.cost_total or 0
                )

                invoice_item = InvoiceItem(

                    invoice_id=invoice.id,

                    description=part.part_name,

                    item_type="Parts",

                    revenue_category="Parts & Accessories Sales",

                    quantity=quantity,

                    unit_price=unit_price,

                    total=total,

                    unit_cost=unit_cost,

                    cost_total=cost_total
                )

                db.session.add(invoice_item)

            # =================================================
            # CREATE INVOICE ITEMS FROM JOB CARD LABOUR
            # =================================================

            for labour in job_card.labour_items:

                hours = float(
                    labour.hours or 0
                )

                hourly_rate = float(
                    labour.hourly_rate or 0
                )

                total = hours * hourly_rate

                hourly_cost = float(
                    labour.hourly_cost or 0
                )

                cost_total = float(
                    labour.cost_total or 0
                )

                # ---------------------------------------------
                # MAP JOB SERVICE TYPE TO P&L REVENUE CATEGORY
                # ---------------------------------------------

                service_type = (
                    job.service_type or ""
                ).strip().lower()

                if service_type == "diagnostic services":

                    revenue_category = "Diagnostic Services"

                elif service_type in [
                    "vehicle recovery & towing",
                    "vehicle recovery and towing"
                ]:

                    revenue_category = (
                        "Vehicle Recovery / Towing"
                    )

                elif service_type == (
                    "assessment / valuation services"
                ).lower():

                    revenue_category = (
                        "Inspection Services"
                    )

                elif service_type == "other":

                    revenue_category = (
                        "Other Garage Revenue"
                    )

                else:

                    revenue_category = (
                        "Labour / Service Revenue"
                    )

                invoice_item = InvoiceItem(

                    invoice_id=invoice.id,

                    description=labour.description,

                    item_type="Labour",

                    revenue_category=revenue_category,

                    quantity=hours,

                    unit_price=hourly_rate,

                    total=total,

                    unit_cost=hourly_cost,

                    cost_total=cost_total
                )

                db.session.add(invoice_item)

            # -------------------------------------------------
            # SAVE EVERYTHING
            # -------------------------------------------------

            db.session.commit()

            flash(
                f"Invoice {invoice.invoice_number} "
                f"created successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "print_invoice",
                    invoice_id=invoice.id
                )
            )

        except Exception as e:

            db.session.rollback()

            print(
                "INVOICE CREATION ERROR:",
                repr(e)
            )

            flash(
                "Unable to create invoice. "
                "Please check the application console.",
                "danger"
            )

    # ---------------------------------------------------------
    # RENDER INVOICE CREATION PAGE
    # ---------------------------------------------------------

    return render_template(
        "admin/invoices/create.html",

        job=job,

        job_card=job_card,

        parts=job_card.parts,

        labour_items=job_card.labour_items,

        parts_total=parts_total,

        labour_total=labour_total,

        subtotal=subtotal,

        tax_rate=tax_rate,

        tax_amount=tax_amount,

        total_amount=total_amount,

        user=session.get("user"),

        role=session.get("role")
    )

@app.route("/invoice/<int:invoice_id>")
@require_roles("admin", "superadmin", "accounts")
def invoice_detail(invoice_id):

    invoice = Invoice.query.get_or_404(invoice_id)

    job = invoice.job

    calculate_invoice_payment_status(invoice)

    db.session.commit()

    return render_template(
        "admin/invoices/invoice_details.html",
        invoice=invoice,
        job=job,
        payments=invoice.payments,
        role=session.get("role"),
        user=session.get("user")
    )

@app.route("/invoice/<int:invoice_id>print")
def print_invoice(invoice_id):

    invoice = Invoice.query.get_or_404(invoice_id)

    job = Jobs.query.get_or_404(
        invoice.job_id
    )

    customer = Customer.query.filter_by(
        customer_name=job.customer_name
    ).first()

    job_card = JobCard.query.filter_by(
        job_id=job.id
    ).first()

    parts = (
        job_card.parts
        if job_card
        else []
    )

    labour_items = (
        job_card.labour_items
        if job_card
        else []
    )

    parts_total = sum(
        float(part.quantity or 0) *
        float(part.unit_price or 0)
        for part in parts
    )

    labour_total = sum(
        float(labour.hours or 0) *
        float(labour.hourly_rate or 0)
        for labour in labour_items
    )

    return render_template(
        "admin/invoices/test.html",

        invoice=invoice,

        job=job,

        customer=customer,

        job_card=job_card,

        parts=parts,

        labour_items=labour_items,

        parts_total=parts_total,

        labour_total=labour_total,

        user=session.get("user"),

        role=session.get("role")
    )


@app.route(
    "/invoice/<int:invoice_id>/pdf",
    endpoint="invoice_pdf"
)
@require_roles("admin", "superadmin", "accounts")
def invoice_pdf(invoice_id):

    # ============================================================
    # LOAD INVOICE
    # ============================================================

    invoice = Invoice.query.get_or_404(invoice_id)

    job = Jobs.query.get_or_404(
        invoice.job_id
    )

    # ============================================================
    # CUSTOMER
    # ============================================================

    customer = Customer.query.filter_by(
        customer_name=job.customer_name
    ).first()

    # ============================================================
    # JOB CARD
    # ============================================================

    job_card = JobCard.query.filter_by(
        job_id=job.id
    ).first()

    parts = (
        job_card.parts
        if job_card
        else []
    )

    labour_items = (
        job_card.labour_items
        if job_card
        else []
    )

    # ============================================================
    # DISPLAY TOTALS
    # ============================================================

    parts_total = sum(
        float(part.quantity or 0)
        * float(part.unit_price or 0)
        for part in parts
    )

    labour_total = sum(
        float(labour.hours or 0)
        * float(labour.hourly_rate or 0)
        for labour in labour_items
    )

    # Official invoice values
    subtotal = float(
        invoice.subtotal or 0
    )

    tax_rate = float(
        invoice.tax_rate or 0
    )

    tax_amount = float(
        invoice.tax_amount or 0
    )

    total_amount = float(
        invoice.total_amount or 0
    )

    # ============================================================
    # PDF BUFFER
    # ============================================================

    buffer = BytesIO()

    # ============================================================
    # PAGE / DOCUMENT
    #
    # Reserve the bottom 52mm for:
    #
    #   QR + eTIMS
    #   Footer
    #
    # ============================================================

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,

        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=12 * mm,

        bottomMargin=52 * mm,

        title=f"Invoice {invoice.invoice_number}",
        author="Autovex Garage MS",
    )

    # ============================================================
    # STYLES
    # ============================================================

    styles = getSampleStyleSheet()

    normal = ParagraphStyle(
        "InvoiceNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=10.5,
        textColor=colors.HexColor("#333333"),
        spaceBefore=0,
        spaceAfter=0,
    )

    small = ParagraphStyle(
        "InvoiceSmall",
        parent=normal,
        fontSize=7.5,
        leading=9,
    )

    small_gray = ParagraphStyle(
        "InvoiceSmallGray",
        parent=small,
        textColor=colors.HexColor("#666666"),
    )

    bold = ParagraphStyle(
        "InvoiceBold",
        parent=normal,
        fontName="Helvetica-Bold",
    )

    section_style = ParagraphStyle(
        "InvoiceSection",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#333333"),
        spaceBefore=5,
        spaceAfter=3,
    )

    invoice_title = ParagraphStyle(
        "InvoiceTitle",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=24,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#222222"),
    )

    total_style = ParagraphStyle(
        "InvoiceTotal",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=15,
        textColor=colors.HexColor("#111111"),
    )

    # ============================================================
    # STORY
    # ============================================================

    story = []

    # ============================================================
    # HEADER
    #
    # Logo left
    # INVOICE right
    # Blue line
    # ============================================================

    logo_path = os.path.join(
        app.root_path,
        "static",
        "assets",
        "images",
        "logo.png"
    )

    if os.path.exists(logo_path):

        logo = Image(
            logo_path,
            width=24 * mm,
            height=24 * mm,
            kind="proportional"
        )

    else:

        logo = Paragraph(
            "<b>AUTOVEX GARAGE MS</b>",
            bold
        )

    header_right = Table(
        [
            [
                Paragraph(
                    "INVOICE",
                    invoice_title
                )
            ]
        ],
        colWidths=[
            70 * mm
        ]
    )

    header_right.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "RIGHT"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0
            ),
        ])
    )

    header = Table(
        [
            [
                logo,
                header_right
            ]
        ],
        colWidths=[
            100 * mm,
            70 * mm
        ]
    )

    header.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "LINEBELOW",
                (0, 0),
                (-1, -1),
                1.5,
                colors.HexColor("#F54927")
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
        ])
    )

    story.append(header)

    story.append(
        Spacer(1, 7)
    )

    # ============================================================
    # CUSTOMER + INVOICE DETAILS
    # ============================================================

    customer_name = (
        customer.customer_name
        if customer
        else job.customer_name
    )

    customer_lines = [
        f"<b>{customer_name}</b>"
    ]

    if customer and customer.address:
        customer_lines.append(
            str(customer.address)
        )

    if customer and customer.email:
        customer_lines.append(
            str(customer.email)
        )

    if job.telno:
        customer_lines.append(
            str(job.telno)
        )

    bill_to = Paragraph(
        "<br/>".join(customer_lines),
        normal
    )

    invoice_details = [
        [
            Paragraph(
                "Invoice number:",
                small_gray
            ),
            Paragraph(
                f"<b>{invoice.invoice_number}</b>",
                small
            ),
        ],

        [
            Paragraph(
                "Invoice date:",
                small_gray
            ),
            Paragraph(
                invoice.issue_date.strftime("%d/%m/%Y")
                if invoice.issue_date
                else "-",
                small
            ),
        ],

        [
            Paragraph(
                "Payment terms:",
                small_gray
            ),
            Paragraph(
                "Due on receipt",
                small
            ),
        ],

        [
            Paragraph(
                "Status:",
                small_gray
            ),
            Paragraph(
                f"<b>{invoice.status}</b>",
                small
            ),
        ],
    ]

    invoice_info = Table(
        invoice_details,
        colWidths=[
            32 * mm,
            38 * mm
        ]
    )

    invoice_info.setStyle(
        TableStyle([
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "RIGHT"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                1
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                2
            ),
        ])
    )

    intro = Table(
        [
            [
                bill_to,
                invoice_info
            ]
        ],
        colWidths=[
            85 * mm,
            85 * mm
        ]
    )

    intro.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0
            ),
        ])
    )

    story.append(intro)

    story.append(
        Spacer(1, 5)
    )

    # ============================================================
    # VEHICLE INFORMATION
    # ============================================================

    mechanic_name = (
        job.mechanic.username
        if job.mechanic
        else "-"
    )

    vehicle_table = Table(
        [
            [
                Paragraph(
                    "<b>Vehicle</b>",
                    small
                ),

                Paragraph(
                    "<b>Model</b>",
                    small
                ),

                Paragraph(
                    "<b>Mechanic</b>",
                    small
                ),
            ],

            [
                Paragraph(
                    str(job.vehicle or "-"),
                    small_gray
                ),

                Paragraph(
                    str(job.vehicle_model or "-"),
                    small_gray
                ),

                Paragraph(
                    str(mechanic_name),
                    small_gray
                ),
            ]
        ],
        colWidths=[
            56 * mm,
            56 * mm,
            58 * mm
        ]
    )

    vehicle_table.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                4
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                1
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                1
            ),
        ])
    )

    story.append(vehicle_table)

    story.append(
        Spacer(1, 6)
    )

    story.append(
        Paragraph(
            "Thank you for your business!",
            small
        )
    )

    # ============================================================
    # PARTS
    # ============================================================

    if parts:

        story.append(
            Paragraph(
                "PARTS",
                section_style
            )
        )

        parts_data = [
            [
                Paragraph(
                    "<b>Description</b>",
                    small
                ),

                Paragraph(
                    "<b>Part Number</b>",
                    small
                ),

                Paragraph(
                    "<b>Qty</b>",
                    small
                ),

                Paragraph(
                    "<b>Unit Price</b>",
                    small
                ),

                Paragraph(
                    "<b>Total</b>",
                    small
                ),
            ]
        ]

        for part in parts:

            quantity = float(
                part.quantity or 0
            )

            unit_price = float(
                part.unit_price or 0
            )

            line_total = (
                quantity *
                unit_price
            )

            description = (
                f"<b>{part.part_name}</b>"
            )

            if part.notes:

                description += (
                    "<br/>"
                    f"<font color='#6f6f6f'>"
                    f"{part.notes}"
                    "</font>"
                )

            parts_data.append(
                [
                    Paragraph(
                        description,
                        small
                    ),

                    Paragraph(
                        str(
                            part.part_number
                            or "-"
                        ),
                        small
                    ),

                    Paragraph(
                        f"{quantity:.2f}",
                        small
                    ),

                    Paragraph(
                        f"{unit_price:,.2f}",
                        small
                    ),

                    Paragraph(
                        f"<b>{line_total:,.2f}</b>",
                        small
                    ),
                ]
            )

        parts_table = Table(
            parts_data,
            colWidths=[
                57 * mm,
                32 * mm,
                17 * mm,
                30 * mm,
                34 * mm
            ],
            repeatRows=1
        )

        parts_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#525252")
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.HexColor("#d4d4d4")
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
            ])
        )

        story.append(parts_table)

        parts_subtotal = Table(
            [
                [
                    Paragraph(
                        "Parts Total",
                        small
                    ),

                    Paragraph(
                        f"<b>{parts_total:,.2f} KES</b>",
                        small
                    )
                ]
            ],
            colWidths=[
                130 * mm,
                40 * mm
            ]
        )

        parts_subtotal.setStyle(
            TableStyle([
                (
                    "ALIGN",
                    (1, 0),
                    (1, 0),
                    "RIGHT"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
            ])
        )

        story.append(
            parts_subtotal
        )

    # ============================================================
    # LABOUR
    # ============================================================

    if labour_items:

        story.append(
            Paragraph(
                "LABOUR",
                section_style
            )
        )

        labour_data = [
            [
                Paragraph(
                    "<b>Description</b>",
                    small
                ),

                Paragraph(
                    "<b>Hours</b>",
                    small
                ),

                Paragraph(
                    "<b>Hourly Rate</b>",
                    small
                ),

                Paragraph(
                    "<b>Total</b>",
                    small
                ),
            ]
        ]

        for labour in labour_items:

            hours = float(
                labour.hours or 0
            )

            hourly_rate = float(
                labour.hourly_rate or 0
            )

            line_total = (
                hours *
                hourly_rate
            )

            description = (
                f"<b>{labour.description}</b>"
            )

            if labour.notes:

                description += (
                    "<br/>"
                    "<font color='#6f6f6f'>"
                    f"{labour.notes}"
                    "</font>"
                )

            labour_data.append(
                [
                    Paragraph(
                        description,
                        small
                    ),

                    Paragraph(
                        f"{hours:.2f}",
                        small
                    ),

                    Paragraph(
                        f"{hourly_rate:,.2f}",
                        small
                    ),

                    Paragraph(
                        f"<b>{line_total:,.2f}</b>",
                        small
                    ),
                ]
            )

        labour_table = Table(
            labour_data,
            colWidths=[
                76 * mm,
                25 * mm,
                34 * mm,
                35 * mm
            ],
            repeatRows=1
        )

        labour_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#525252")
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.HexColor("#d4d4d4")
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
            ])
        )

        story.append(
            labour_table
        )

        labour_subtotal = Table(
            [
                [
                    Paragraph(
                        "Labour Total",
                        small
                    ),

                    Paragraph(
                        f"<b>{labour_total:,.2f} KES</b>",
                        small
                    )
                ]
            ],
            colWidths=[
                130 * mm,
                40 * mm
            ]
        )

        labour_subtotal.setStyle(
            TableStyle([
                (
                    "ALIGN",
                    (1, 0),
                    (1, 0),
                    "RIGHT"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
            ])
        )

        story.append(
            labour_subtotal
        )

    # ============================================================
    # JOB DESCRIPTION
    # ============================================================

    if job.description:

        story.append(
            Spacer(1, 3)
        )

        description_table = Table(
            [
                [
                    Paragraph(
                        "<b>Job Description</b>",
                        small
                    )
                ],

                [
                    Paragraph(
                        str(job.description),
                        small_gray
                    )
                ]
            ],
            colWidths=[
                170 * mm
            ]
        )

        description_table.setStyle(
            TableStyle([
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#dddddd")
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#fafafa")
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
            ])
        )

        story.append(
            description_table
        )

    # ============================================================
    # TOTALS
    # ============================================================

    story.append(
        Spacer(1, 7)
    )

    totals_data = [

        [
            Paragraph(
                "Parts Total",
                small
            ),

            Paragraph(
                f"{parts_total:,.2f} KES",
                small
            )
        ],

        [
            Paragraph(
                "Labour Total",
                small
            ),

            Paragraph(
                f"{labour_total:,.2f} KES",
                small
            )
        ],

        [
            Paragraph(
                "Total excl. VAT",
                small
            ),

            Paragraph(
                f"{subtotal:,.2f} KES",
                small
            )
        ],

        [
            Paragraph(
                f"VAT {tax_rate:.1f}%",
                small
            ),

            Paragraph(
                f"{tax_amount:,.2f} KES",
                small
            )
        ],

        [
            Paragraph(
                "<b>Total amount due</b>",
                total_style
            ),

            Paragraph(
                f"<b>{total_amount:,.2f} KES</b>",
                total_style
            )
        ],
    ]

    totals_table = Table(
        totals_data,
        colWidths=[
            125 * mm,
            45 * mm
        ],
        hAlign="RIGHT"
    )

    totals_table.setStyle(
        TableStyle([
            (
                "ALIGN",
                (1, 0),
                (1, -1),
                "RIGHT"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                2
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                2
            ),

            (
                "LINEABOVE",
                (0, 4),
                (-1, 4),
                1.5,
                colors.HexColor("#333333")
            ),

            (
                "TOPPADDING",
                (0, 4),
                (-1, 4),
                5
            ),

            (
                "BOTTOMPADDING",
                (0, 4),
                (-1, 4),
                2
            ),
        ])
    )

    story.append(
        totals_table
    )

    # ============================================================
    # FIXED BOTTOM SECTION
    #
    # QR + eTIMS + FOOTER
    #
    # This is deliberately drawn on the canvas rather than
    # appended to the story.
    # ============================================================

    def draw_bottom_section(
        canvas,
        doc
    ):

        page_width, page_height = A4

        canvas.saveState()

        # ========================================================
        # eTIMS DIVIDER
        # ========================================================

        etims_line_y = 52 * mm

        canvas.setStrokeColor(
            colors.HexColor("#d0d0d0")
        )

        canvas.setLineWidth(
            0.6
        )

        canvas.line(
            15 * mm,
            etims_line_y,
            page_width - 15 * mm,
            etims_line_y
        )

        # ========================================================
        # QR CODE
        # ========================================================

        qr_buffer = BytesIO()

        qr = qrcode.QRCode(
            version=1,
            box_size=5,
            border=2
        )

        qr.add_data(
            f"Invoice: {invoice.invoice_number}"
        )

        qr.make(
            fit=True
        )

        qr_image = qr.make_image(
            fill_color="black",
            back_color="white"
        )

        qr_image.save(
            qr_buffer,
            format="PNG"
        )

        qr_buffer.seek(0)

        # --------------------------------------------------------
        # CENTER GROUP
        # --------------------------------------------------------

        qr_size = 27 * mm

        qr_x = (
            page_width / 2
            - 39 * mm
        )

        qr_y = 25 * mm

        canvas.drawImage(
            ImageReader(qr_buffer),
            qr_x,
            qr_y,
            width=qr_size,
            height=qr_size,
            preserveAspectRatio=True,
            mask="auto"
        )

        # ========================================================
        # eTIMS INFORMATION
        # ========================================================

        etims_x = (
            page_width / 2
            + 4 * mm
        )

        canvas.setFillColor(
            colors.HexColor("#333333")
        )

        canvas.setFont(
            "Helvetica-Bold",
            8.5
        )

        canvas.drawString(
            etims_x,
            42 * mm,
            "eTIMS INFORMATION"
        )

        canvas.setFont(
            "Helvetica",
            7.5
        )

        canvas.drawString(
            etims_x,
            35.5 * mm,
            "CU Number:"
        )

        canvas.setFont(
            "Helvetica-Bold",
            7.5
        )

        canvas.drawString(
            etims_x + 18 * mm,
            35.5 * mm,
            "CU123456789"
        )

        canvas.setFont(
            "Helvetica",
            7.5
        )

        canvas.drawString(
            etims_x,
            30.5 * mm,
            "Invoice verification information"
        )

        # ========================================================
        # FOOTER DIVIDER
        # ========================================================

        footer_line_y = 21 * mm

        canvas.setStrokeColor(
            colors.HexColor("#d0d0d0")
        )

        canvas.setLineWidth(
            0.7
        )

        canvas.line(
            15 * mm,
            footer_line_y,
            page_width - 15 * mm,
            footer_line_y
        )

        # ========================================================
        # FOOTER
        # ========================================================

        footer_y = 17 * mm

        canvas.setFillColor(
            colors.HexColor("#444444")
        )

        # --------------------------------------------------------
        # COMPANY
        # --------------------------------------------------------

        company_x = 15 * mm

        canvas.setFont(
            "Helvetica-Bold",
            7.5
        )

        canvas.drawString(
            company_x,
            footer_y,
            "Hillance Enterprises"
        )

        canvas.setFont(
            "Helvetica",
            7
        )

        canvas.drawString(
            company_x,
            footer_y - 4 * mm,
            "Professional Vehicle Service Centre"
        )

        canvas.drawString(
            company_x,
            footer_y - 8 * mm,
            "P.O Box 1234-00100, Nairobi"
        )

        canvas.drawString(
            company_x,
            footer_y - 12 * mm,
            "KRA PIN: P051234567A"
        )

        # --------------------------------------------------------
        # CONTACT
        # --------------------------------------------------------

        contact_x = 75 * mm

        canvas.setFont(
            "Helvetica-Bold",
            7.5
        )

        canvas.drawString(
            contact_x,
            footer_y,
            "Contact information"
        )

        canvas.setFont(
            "Helvetica",
            7
        )

        canvas.drawString(
            contact_x,
            footer_y - 4 * mm,
            "0723523109 / 0783644648"
        )

        canvas.drawString(
            contact_x,
            footer_y - 8 * mm,
            "info@hillance.com"
        )

        # --------------------------------------------------------
        # PAYMENT
        # --------------------------------------------------------

        payment_x = 135 * mm

        canvas.setFont(
            "Helvetica-Bold",
            7.5
        )

        canvas.drawString(
            payment_x,
            footer_y,
            "Payment details"
        )

        canvas.setFont(
            "Helvetica",
            7
        )

        canvas.drawString(
            payment_x,
            footer_y - 4 * mm,
            "Bank: I&M Bank"
        )

        canvas.drawString(
            payment_x,
            footer_y - 8 * mm,
            "Account: 00207958476150"
        )

        canvas.drawString(
            payment_x,
            footer_y - 12 * mm,
            "Currency: KES"
        )

        canvas.restoreState()

    # ============================================================
    # PAID STAMP
    # ============================================================

    def draw_paid_stamp(
        canvas,
        doc
    ):

        if invoice.status != "Paid":
            return

        canvas.saveState()

        canvas.setStrokeColor(
            colors.HexColor("#16a34a")
        )

        canvas.setFillColor(
            colors.HexColor("#16a34a")
        )

        canvas.setLineWidth(
            3
        )

        canvas.translate(
            155 * mm,
            240 * mm
        )

        canvas.rotate(
            -14
        )

        canvas.setFillAlpha(
            0.18
        )

        canvas.setStrokeAlpha(
            0.18
        )

        canvas.rect(
            -25 * mm,
            -9 * mm,
            50 * mm,
            18 * mm
        )

        canvas.setFillAlpha(
            1
        )

        canvas.setStrokeAlpha(
            1
        )

        canvas.setFont(
            "Helvetica-Bold",
            22
        )

        canvas.drawCentredString(
            0,
            -6,
            "PAID"
        )

        canvas.restoreState()

    # ============================================================
    # PAGE CALLBACK
    # ============================================================

    def draw_page(
        canvas,
        doc
    ):

        # Bottom QR + eTIMS + footer
        draw_bottom_section(
            canvas,
            doc
        )

        # Paid stamp
        draw_paid_stamp(
            canvas,
            doc
        )

    # ============================================================
    # BUILD
    # ============================================================

    doc.build(
        story,
        onFirstPage=draw_page
    )

    # ============================================================
    # RETURN PDF
    # ============================================================

    buffer.seek(0)

    filename = (
        f"{invoice.invoice_number}.pdf"
    )

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )


@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        # Check current password
        if not check_password_hash(user.password, current_password):
            flash("Current password is incorrect", "danger")
            return redirect(url_for("change_password"))

        # Check new password confirmation
        if new_password != confirm_password:
            flash("New passwords do not match", "danger")
            return redirect(url_for("change_password"))

        # Update password
        user.password = generate_password_hash(new_password)
        db.session.commit()

        flash("Password changed successfully", "success")
        return redirect(url_for("dashboard"))

    return render_template("change_password.html", user=session.get("user"), role=session.get("role"))

# ===================== RUN =====================

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=5000)
