from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    jobs = db.relationship("Job", backref="mechanic", lazy=True)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vehicles = db.relationship(
        "Vehicle",
        backref="customer",
        cascade="all, delete-orphan",
        lazy=True
    )

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customer.id"),
        nullable=False
    )
    registration_no = db.Column(db.String(20), unique=True, nullable=False)
    model = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    jobs = db.relationship("Job", backref="vehicle", lazy=True)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customer.id"),
        nullable=False
    )

    vehicle_id = db.Column(
        db.Integer,
        db.ForeignKey("vehicle.id"),
        nullable=False
    )

    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Open")

    assigned_to = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer")

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    job_id = db.Column(
        db.Integer,
        db.ForeignKey("job.id"),
        nullable=False,
        unique=True   # 🚫 One invoice per job
    )

    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="Unpaid")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship("Job")

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50))
    action = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
