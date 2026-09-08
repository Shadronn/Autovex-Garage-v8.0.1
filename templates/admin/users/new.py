from flask import Flask, jsonify, render_template, request, redirect, url_for, session,flash,abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask_login import logout_user,login_required, current_user
from sqlalchemy import func
import os
import uuid
import io
import csv
import pandas as pd
from flask import send_file, Response
from functools import wraps


# APP CONFIG
# ------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.permanent_session_lifetime = timedelta(minutes=3)  # session expires after 3 min of inactivity

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Fix for SQLAlchemy compatibility
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///garage.db"

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

# ===================== MODELS =====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    photos = db.relationship("VehiclePhoto", backref="vehicle", lazy=True)

class VehiclePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))
    image_path = db.Column(db.String(255))
    filename = db.Column(db.String(255), nullable=False)  # <--- Add this


class Jobs(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"), nullable=False)
    telno = db.Column(db.String(20), nullable=False)
    vehicle = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Open")
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoice = db.relationship(
        "Invoice",
        backref="job",
        uselist=False,
        cascade="all, delete-orphan"
    )

class Invoice(db.Model):
    __tablename__ = "invoice"

    id = db.Column(db.Integer, primary_key=True)

    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id"),
        nullable=False,
        unique=True
    )

    subtotal = db.Column(db.Float, nullable=False)
    tax_rate = db.Column(db.Float, default=0.16)
    tax_amount = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)

    status = db.Column(db.String(20), default="Unpaid")

    # Payment fields
    payment_method = db.Column(db.String(120))
    payment_reference = db.Column(db.String(120))
    payment_proof = db.Column(db.String(200))
    paid_at = db.Column(db.DateTime)

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ===================== INIT =====================
def init_db():
    db.create_all()

    if not User.query.first():
        users = [
            User(username="superadmin", password=generate_password_hash("super@admin?2026"), role="superadmin"),
            User(username="admin", password=generate_password_hash("admin@2026??"), role="admin"),
            User(username="accounts", password=generate_password_hash("accounts@2026??"), role="accounts"),
            User(username="mechanic", password=generate_password_hash("mechanic@2026?"), role="mechanic"),
        ]
        db.session.add_all(users)
        db.session.commit()


#create tables
with app.app_context():
    db.create_all()
    init_db()

#=================helpers==================

def require_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user" not in session or session.get("role") not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return wrapper
# ===================== AUTH =====================

@app.route("/")
def start():
    return render_template("start.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()

        if user and user.is_active and check_password_hash(
            user.password, request.form["password"]
        ):

            session.clear()
            session.permanent = True

            session["user_id"] = user.id
            session["user"] = user.username
            session["role"] = user.role

            return redirect(url_for("dashboard"))


        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

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
            "superadmin/dashboard.html",
            user=session["user"],
            role=role,
            total_jobs=total_jobs,
            open_jobs=open_jobs,
            completed_jobs=completed_jobs,
            revenue=revenue,
            debt=debt,
            now=now
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
        "accounts/dashboard.html",  # 👈 different template
        user=session["user"],
        role=role,
        total_jobs=total_jobs,
        open_jobs=open_jobs,
        completed_jobs=completed_jobs,
        revenue=revenue,
        debt=debt,
        now=now
    )

@app.route("/dashboard/mechanic")
def mechanic_dashboard():
    if session.get("role") != "mechanic":
        abort(403)

    mechanic = User.query.filter_by(username=session["user"]).first()

    jobs = Jobs.query.filter_by(
        assigned_to=mechanic.id
    ).order_by(Jobs.created_at.desc()).all()

    open_jobs = [j for j in jobs if j.status == "Open"]
    completed_jobs = [j for j in jobs if j.status == "Complete"]

    return render_template(
        "mechanic/dashboard.html",
        jobs=jobs,
        open_jobs=open_jobs,
        completed_jobs=completed_jobs,
        role="mechanic"
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

# ===================== JOBS MODULE =====================

@app.route("/jobs/create", methods=["GET", "POST"])

def create_job():
    if request.method == "POST":
        # Use .get() to avoid KeyErrors
        customer_id = request.form.get('customer_id')
        vehicle_id = request.form.get('vehicle_id')
        description = request.form.get('description')

        if not customer_id:
            flash("Please select a customer")
            return redirect(url_for("create_job"))

        customer = Customer.query.get(customer_id)
        if not customer:
            flash("Invalid customer selected")
            return redirect(url_for("create_job"))

        # Vehicle may be None if not selected
        vehicle = Vehicle.query.get(vehicle_id) if vehicle_id else None

        job = Jobs(
            customer_id=customer.id,
            customer_name=customer.customer_name,
            vehicle_id=vehicle.id,
            telno=customer.telno,
            vehicle=f"{vehicle.registration_no} - {vehicle.model}" if vehicle else "",
            description=description,
            status="Open"
        )

        db.session.add(job)
        db.session.commit()
        flash("Job created successfully!")
        return redirect(url_for("jobs"))

    # GET request: render form
    customers = Customer.query.all()
    mechanics = User.query.filter_by(role="mechanic").all()
    return render_template("jobs/create.html", customers=customers, mechanics=mechanics, role=session.get("role"))

@app.route("/jobs/<int:job_id>/delete", methods=["POST"])
@require_roles("admin", "superadmin")
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

    customers = Customer.query.all()

    return render_template(
    "customers/index.html",
    customers=customers,
    user=session["user"],
    role=session["role"]
)

@app.route("/admin/vehicles")
def vehicles():
    if "user" not in session:
        return redirect(url_for("login"))

    vehicles = Vehicle.query.order_by(Vehicle.created_at.desc()).all()
    
    return render_template(
        "admin/vehicles/vehicles.html",
        vehicles=vehicles,
        user=session.get("user"),
        role=session.get("role")
)

@app.route("/vehicles/<int:vehicle_id>")
def vehicle_details(vehicle_id):
    if "user" not in session:
        return redirect(url_for("login"))

    vehicle = Vehicle.query.get_or_404(vehicle_id)
    customer = Customer.query.get_or_404(vehicle.customer_id)

    jobs = Jobs.query.filter_by(vehicle_id=vehicle.id).order_by(Jobs.created_at.desc()).all()

    return render_template(
        "admin/vehicles/vehicle_details.html",
        vehicle=vehicle,
        customer=customer,
        jobs=jobs,
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
        "vehicles/edit.html",
        vehicle=vehicle,
        user=session.get("user"),
        role=session.get("role")
    )

@app.route("/vehicles/<int:vehicle_id>/delete", methods=["POST"])
@require_roles("admin", "superadmin")
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
def add_vehicle():
    if request.method == "POST":
        customer_id = request.form.get("customer_id")
        registration_no = request.form.get("registration_no")
        model = request.form.get("model")
        color = request.form.get("color")
        yom = request.form.get("yom")

        # Create new vehicle record
        new_vehicle = Vehicle(
            customer_id=customer_id,
            registration_no=registration_no,
            model=model,
            color=color,
            yom=yom
        )
        db.session.add(new_vehicle)
        db.session.commit()  # must commit first to get new_vehicle.id

        # Handle photos
        files = request.files.getlist("photos")
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
                file.save(file_path)

                # Save each photo to DB if you have a VehiclePhoto table
                new_photo = VehiclePhoto(
                    vehicle_id=new_vehicle.id,
                    filename=unique_name
                )
                db.session.add(new_photo)

        db.session.commit()
        flash("Vehicle added successfully!")
        return redirect(url_for("vehicles"))

    # GET request: show form
    customers = Customer.query.all()
    return render_template(
        "admin/vehicles/add_vehicle.html",
        customers=customers,
        user=session.get("user"),
        role=session.get("role")
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
@require_roles("admin", "superadmin")
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

    status = request.args.get("status")

    query = Jobs.query

    if status:
        query = query.filter(Jobs.status.ilike(status))

    jobs = query.order_by(Jobs.created_at.desc()).all()

    return render_template(
        "jobs/list.html",
        jobs=jobs,
        user=session["user"],
        role=session["role"],
        active_status=status
    )

@app.route("/jobs/<int:job_id>")
def job_detail(job_id):
    job = Jobs.query.get_or_404(job_id)

    invoice = Invoice.query.filter_by(job_id=job.id).first()

    return render_template(
        "jobs/jobs_detail.html",
        job=job,
        invoice=invoice,
        user=session.get("user"),
        role=session.get("role")
    )

@app.route("/jobs/<int:job_id>/toggle_status", methods=["POST"])
@require_roles("admin", "superadmin","accounts")
def toggle_job_status(job_id):
    job = Jobs.query.get_or_404(job_id)

    if job.status.lower() == "open":
        job.status = "Complete"
    else:
        # 🔥 Re-opening job → delete invoice
        if job.invoice:
            db.session.delete(job.invoice)
        job.status = "Open"

    db.session.commit()

    return jsonify({"success": True, "new_status": job.status})

#INVOICE SECRTION

@app.route("/invoices")
def invoices():
    if "user" not in session:
        return redirect(url_for("login"))

    query = db.session.query(Invoice, Jobs).join(Jobs, Invoice.job_id == Jobs.id)

    # Filters
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    customer = request.args.get("customer")
    status = request.args.get("status")

    if start_date:
        query = query.filter(Invoice.created_at >= start_date)

    if end_date:
        query = query.filter(Invoice.created_at <= end_date)

    if customer:
        query = query.filter(Jobs.customer_name == customer)

    if status:
        query = query.filter(Invoice.status == status)

    invoices = query.order_by(Invoice.created_at.desc()).all()

    # For customer dropdown
    customers = db.session.query(Jobs.customer_name).distinct().all()
    customers = [c[0] for c in customers]

    return render_template(
        "admin/invoices/index.html",
        invoices=invoices,
        customers=customers,
        role=session.get("role")
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
            "Date": invoice.created_at.strftime("%Y-%m-%d"),
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

    invoices = query.order_by(Invoice.created_at.desc()).all()

    # For customer dropdown
    customers = db.session.query(Jobs.customer_name).distinct().all()
    customers = [c[0] for c in customers]

    return render_template(
        "admin/reports/statement.html",
        invoices=invoices,
        customers=customers,
        role=session.get("role")
    )

            

@app.route("/invoice/<int:id>/pay", methods=["GET", "POST"])
def pay_invoice(id):

    if "user" not in session:
        return redirect(url_for("login"))

    # 🔒 Only admin and accounts allowed
    if session.get("role") not in ["admin", "accounts"]:
        abort(403)

    invoice = Invoice.query.get_or_404(id)

    if request.method == "POST":

        method = request.form.get("payment_method")
        ref = request.form.get("payment_reference")
        file = request.files.get("payment_proof")

        filename = None

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        invoice.payment_method = method
        invoice.payment_reference = ref
        invoice.payment_proof = filename
        invoice.payment_date = datetime.utcnow()
        invoice.status = "Paid"

        db.session.commit()

        flash("Payment recorded successfully")
        return redirect(url_for("invoices"))

    return render_template(
    "admin/invoices/pay_invoice.html",
    invoice=invoice,
    role=session.get("role"),
    user=session.get("user")
)

@app.route("/jobs/<int:job_id>/admin/invoices/create", methods=["GET", "POST"])
def create_invoice(job_id):
    if "user" not in session:
        return redirect(url_for("login"))

    job = Jobs.query.get_or_404(job_id)

    # 🔒 HARD STOP: already invoiced
    if job.invoice:
        flash("This job has already been invoiced.", "warning")
        return redirect(url_for("job_detail", job_id=job.id))

    # Optional safety: only completed jobs
    if job.status != "Complete":
        flash("Only completed jobs can be invoiced.", "danger")
        return redirect(url_for("job_detail", job_id=job.id))

    if request.method == "POST":
        subtotal = float(request.form["subtotal"])
        tax_rate = float(request.form.get("tax_rate", 0.16))
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount

        invoice = Invoice(
            job=job,  # ✅ relationship binding
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
            notes=request.form.get("notes")
        )

        db.session.add(invoice)
        db.session.commit()

        return redirect(url_for("print_invoice", invoice_id=invoice.id))

    return render_template(
        "admin/invoices/create.html",
        job=job,
        tax_rate=0.16,
        user=session.get("user"),
        role=session.get("role")
    )

@app.route("/invoice/<int:invoice_id>")
def print_invoice(invoice_id):

    invoice = Invoice.query.get_or_404(invoice_id)
    job = Jobs.query.get_or_404(invoice.job_id)

    # 👇 FIX: fetch customer
    customer = Customer.query.filter_by(
        customer_name=job.customer_name
    ).first()

    return render_template(
        "admin/invoices/test.html",
        invoice=invoice,
        job=job,
        customer=customer,   # ✅ NOW AVAILABLE
        user=session.get("user"),
        role=session.get("role")
    )

@app.route("/invoice/<int:invoice_id>")
def invoice_detail(invoice_id):

    invoice = Invoice.query.get_or_404(invoice_id)

    job = invoice.job

    return render_template(
        "admin/invoices/invoice_details.html",
        invoice=invoice,
        job=job
    )


# ===================== RUN =====================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)