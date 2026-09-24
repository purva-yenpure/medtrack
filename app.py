from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify, abort
)
from config import Config
from db import db
from notifier import notifier

app = Flask(__name__)
app.config.from_object(Config)


# -----------------------------------------------------------------------------
# Authentication & Authorization Decorators
# -----------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in first.", "warning")
                return redirect(url_for("login"))
            user_role = session.get("role")
            if user_role not in allowed_roles:
                flash(f"Access denied: This page is restricted to {', '.join(allowed_roles)}s.", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Context Processor to provide user & unread notifications globally to templates
@app.context_processor
def inject_global_data():
    current_user = None
    unread_notifs_count = 0
    if "user_id" in session:
        current_user = db.get_user_by_id(session["user_id"])
        notifs = db.get_notifications(session["user_id"])
        unread_notifs_count = sum(1 for n in notifs if not n.get("Read", False))
    return {
        "current_user": current_user,
        "unread_notifs_count": unread_notifs_count,
        "storage_mode": "AWS DynamoDB" if db.use_aws else "Local Storage",
        "current_year": datetime.now().year
    }


# -----------------------------------------------------------------------------
# Home & Info Routes
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    doctors = db.get_all_doctors()[:3]
    return render_template("index.html", doctors=doctors)


# -----------------------------------------------------------------------------
# Authentication: Register, Login, Logout
# -----------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "Patient")

        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        extra_fields = {}
        if role == "Patient":
            extra_fields["age"] = request.form.get("age", 25)
            extra_fields["medical_history"] = request.form.get("medical_history", "None recorded.")
        elif role == "Doctor":
            extra_fields["specialization"] = request.form.get("specialization", "General Medicine")
            extra_fields["experience"] = request.form.get("experience", "1 Year")

        user, err = db.create_user(name, email, role, password, phone, **extra_fields)
        if err:
            flash(err, "danger")
            return render_template("register.html")

        # Create welcome notification
        db.create_notification(
            user["UserID"],
            f"Welcome to MedTrack, {name}! Your {role} account has been registered successfully."
        )

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = db.get_user_by_email(email)
        if not user or not db.verify_password(user.get("Password", ""), password):
            flash("Invalid email or password. Please try again.", "danger")
            return render_template("login.html")

        # Increment login count in DB as per requirement
        db.increment_login_count(user["UserID"])
        updated_user = db.get_user_by_id(user["UserID"])
        login_count = updated_user.get("LoginCount", 1) if updated_user else 1

        # Populate session
        session["user_id"] = user["UserID"]
        session["name"] = user.get("Name", "User")
        session["email"] = user.get("Email", "")
        session["role"] = user.get("Role", "Patient")

        # Entity ID resolution
        if user["Role"] == "Patient":
            pat = db.get_patient_by_user_id(user["UserID"])
            session["entity_id"] = pat["PatientID"] if pat else None
        elif user["Role"] == "Doctor":
            doc = db.get_doctor_by_user_id(user["UserID"])
            session["entity_id"] = doc["DoctorID"] if doc else None
        else:
            session["entity_id"] = user["UserID"]

        flash(f"Welcome back, {user.get('Name')}! (Session #{login_count})", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been safely logged out.", "info")
    return redirect(url_for("login"))


# -----------------------------------------------------------------------------
# Dashboards (Role-Based Redirection)
# -----------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    role = session.get("role")
    if role == "Patient":
        return redirect(url_for("patient_dashboard"))
    elif role == "Doctor":
        return redirect(url_for("doctor_dashboard"))
    elif role == "Admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("index"))


@app.route("/dashboard/patient")
@role_required("Patient")
def patient_dashboard():
    patient_id = session.get("entity_id")
    if not patient_id:
        pat = db.get_patient_by_user_id(session["user_id"])
        if pat:
            patient_id = pat["PatientID"]
            session["entity_id"] = patient_id

    patient = db.get_patient_by_id(patient_id)
    appointments = db.get_appointments_by_patient(patient_id) if patient_id else []
    diagnoses = db.get_diagnoses_by_patient(patient_id) if patient_id else []
    notifications = db.get_notifications(session["user_id"])

    upcoming_apts = [a for a in appointments if a.get("Status") == "Scheduled"]
    completed_apts = [a for a in appointments if a.get("Status") == "Completed"]

    return render_template(
        "patient_dashboard.html",
        patient=patient,
        upcoming_appointments=upcoming_apts,
        completed_appointments=completed_apts,
        recent_diagnoses=diagnoses[:5],
        recent_notifications=notifications[:5]
    )


@app.route("/dashboard/doctor")
@role_required("Doctor")
def doctor_dashboard():
    doctor_id = session.get("entity_id")
    if not doctor_id:
        doc = db.get_doctor_by_user_id(session["user_id"])
        if doc:
            doctor_id = doc["DoctorID"]
            session["entity_id"] = doctor_id

    doctor = db.get_doctor_by_id(doctor_id)
    appointments = db.get_appointments_by_doctor(doctor_id) if doctor_id else []
    diagnoses = db.get_diagnoses_by_doctor(doctor_id) if doctor_id else []
    notifications = db.get_notifications(session["user_id"])

    scheduled_apts = [a for a in appointments if a.get("Status") == "Scheduled"]
    completed_apts = [a for a in appointments if a.get("Status") == "Completed"]

    return render_template(
        "doctor_dashboard.html",
        doctor=doctor,
        scheduled_appointments=scheduled_apts,
        completed_appointments=completed_apts,
        recent_diagnoses=diagnoses[:5],
        recent_notifications=notifications[:5]
    )


@app.route("/dashboard/admin")
@role_required("Admin")
def admin_dashboard():
    stats = db.get_system_stats()
    all_users = list(db.local_db["Users"].values()) if not db.use_aws else []
    all_appointments = db.get_all_appointments()[:10]
    return render_template(
        "admin_dashboard.html",
        stats=stats,
        all_users=all_users,
        recent_appointments=all_appointments
    )


# -----------------------------------------------------------------------------
# Appointments: Booking, Listing, Status Update, Search
# -----------------------------------------------------------------------------
@app.route("/book-appointment", methods=["GET", "POST"])
@role_required("Patient")
def book_appointment():
    patient_id = session.get("entity_id")
    doctors = db.get_all_doctors()

    if request.method == "POST":
        doctor_id = request.form.get("doctor_id")
        date = request.form.get("date")
        time = request.form.get("time")
        reason = request.form.get("reason", "Consultation")

        if not doctor_id or not date or not time:
            flash("Please select a doctor, date, and time slot.", "danger")
            return render_template("book_appointment.html", doctors=doctors)

        # Create appointment record
        apt, err = db.create_appointment(patient_id, doctor_id, date, time, reason)
        if err:
            flash(f"Booking error: {err}", "danger")
            return render_template("book_appointment.html", doctors=doctors)

        # Retrieve entities for notification
        patient = db.get_patient_by_id(patient_id)
        doctor = db.get_doctor_by_id(doctor_id)
        if patient and doctor:
            notifier.notify_appointment_booked(apt, patient, doctor)

        flash("Appointment booked successfully! Notifications have been sent.", "success")
        return redirect(url_for("appointments"))

    return render_template("book_appointment.html", doctors=doctors)


@app.route("/appointments")
@login_required
def appointments():
    role = session.get("role")
    entity_id = session.get("entity_id")

    if role == "Patient":
        apts = db.get_appointments_by_patient(entity_id)
    elif role == "Doctor":
        apts = db.get_appointments_by_doctor(entity_id)
    else:
        apts = db.get_all_appointments()

    return render_template("appointments.html", appointments=apts, role=role)


@app.route("/appointments/<appointment_id>/status", methods=["POST"])
@login_required
def update_appointment_status(appointment_id):
    new_status = request.form.get("status")
    if new_status in ["Scheduled", "Completed", "Cancelled"]:
        success = db.update_appointment_status(appointment_id, new_status)
        if success:
            apt = db.get_appointment_by_id(appointment_id)
            if apt:
                db.create_notification(
                    session["user_id"],
                    f"Appointment {appointment_id} status updated to {new_status}."
                )
            flash(f"Appointment status changed to {new_status}.", "success")
        else:
            flash("Failed to update appointment status.", "danger")
    else:
        flash("Invalid status selected.", "danger")
    return redirect(request.referrer or url_for("appointments"))


@app.route("/search-appointments")
@login_required
def search_appointments():
    query = request.args.get("q", "")
    date_filter = request.args.get("date", "")
    status_filter = request.args.get("status", "")
    role = session.get("role")
    entity_id = session.get("entity_id")

    results = db.search_appointments(
        query=query,
        date_filter=date_filter,
        status_filter=status_filter,
        role=role,
        entity_id=entity_id
    )

    if request.headers.get("Accept") == "application/json" or request.args.get("format") == "json":
        return jsonify({"results": results, "count": len(results)})

    return render_template(
        "search.html",
        results=results,
        query=query,
        date_filter=date_filter,
        status_filter=status_filter
    )


# -----------------------------------------------------------------------------
# Diagnosis & Medical History
# -----------------------------------------------------------------------------
@app.route("/submit-diagnosis", methods=["GET", "POST"])
@login_required
def submit_diagnosis():
    role = session.get("role")
    appointment_id_param = request.args.get("appointment_id", "")

    # Retrieve candidate appointments for diagnosis
    if role == "Doctor":
        doctor_id = session.get("entity_id")
        appointments_list = [
            a for a in db.get_appointments_by_doctor(doctor_id)
            if a.get("Status") in ["Scheduled", "Completed"]
        ]
    else:
        appointments_list = db.get_all_appointments()

    if request.method == "POST":
        appointment_id = request.form.get("appointment_id")
        report = request.form.get("report", "").strip()
        date = request.form.get("date", datetime.now().strftime("%Y-%m-%d"))

        if not appointment_id or not report:
            flash("Appointment selection and diagnosis report text are required.", "danger")
            return render_template(
                "submit_diagnosis.html",
                appointments=appointments_list,
                preselected_apt=appointment_id_param
            )

        apt = db.get_appointment_by_id(appointment_id)
        if not apt:
            flash("Appointment not found.", "danger")
            return render_template("submit_diagnosis.html", appointments=appointments_list)

        doctor_id = apt.get("DoctorID")
        patient_id = apt.get("PatientID")

        diagnosis, err = db.create_diagnosis(appointment_id, doctor_id, patient_id, report, date)
        if err:
            flash(f"Error submitting diagnosis: {err}", "danger")
            return render_template("submit_diagnosis.html", appointments=appointments_list)

        # Notify patient
        patient = db.get_patient_by_id(patient_id)
        doctor = db.get_doctor_by_id(doctor_id)
        if patient and doctor:
            notifier.notify_diagnosis_submitted(diagnosis, patient, doctor)

        flash("Medical diagnosis report submitted successfully!", "success")
        return redirect(url_for("medical_history", patient_id=patient_id))

    return render_template(
        "submit_diagnosis.html",
        appointments=appointments_list,
        preselected_apt=appointment_id_param
    )


@app.route("/medical-history")
@app.route("/medical-history/<patient_id>")
@login_required
def medical_history(patient_id=None):
    role = session.get("role")

    if not patient_id:
        if role == "Patient":
            patient_id = session.get("entity_id")
        else:
            flash("Please specify a patient to view medical history.", "warning")
            return redirect(url_for("dashboard"))

    patient = db.get_patient_by_id(patient_id)
    if not patient:
        flash("Patient records not found.", "danger")
        return redirect(url_for("dashboard"))

    diagnoses = db.get_diagnoses_by_patient(patient_id)
    past_appointments = [
        a for a in db.get_appointments_by_patient(patient_id)
        if a.get("Status") == "Completed"
    ]

    return render_template(
        "medical_history.html",
        patient=patient,
        diagnoses=diagnoses,
        past_appointments=past_appointments
    )


# -----------------------------------------------------------------------------
# User Profile
# -----------------------------------------------------------------------------
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = db.get_user_by_id(session["user_id"])
    role = session.get("role")
    patient = db.get_patient_by_user_id(session["user_id"]) if role == "Patient" else None
    doctor = db.get_doctor_by_user_id(session["user_id"]) if role == "Doctor" else None

    if request.method == "POST":
        updates = {
            "Name": request.form.get("name", user.get("Name")),
            "Phone": request.form.get("phone", user.get("Phone"))
        }

        if role == "Patient":
            if request.form.get("age"):
                updates["Age"] = request.form.get("age")
            if request.form.get("medical_history"):
                updates["MedicalHistory"] = request.form.get("medical_history")
        elif role == "Doctor":
            if request.form.get("specialization"):
                updates["Specialization"] = request.form.get("specialization")
            if request.form.get("experience"):
                updates["Experience"] = request.form.get("experience")

        success, msg = db.update_profile(session["user_id"], updates)
        if success:
            session["name"] = updates["Name"]
            flash(msg, "success")
        else:
            flash(msg, "danger")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user, patient=patient, doctor=doctor)


# -----------------------------------------------------------------------------
# Notifications
# -----------------------------------------------------------------------------
@app.route("/notifications")
@login_required
def notifications():
    user_notifs = db.get_notifications(session["user_id"])
    return render_template("notifications.html", notifications=user_notifs)


@app.route("/notifications/<notification_id>/read", methods=["POST"])
@login_required
def mark_read(notification_id):
    db.mark_notification_read(notification_id)
    return redirect(url_for("notifications"))


# -----------------------------------------------------------------------------
# System Health & AWS Integration Routing
# -----------------------------------------------------------------------------
@app.route("/health")
def health():
    """
    Health check endpoint for AWS EC2 Application Load Balancer,
    CloudWatch monitoring, and local testing.
    """
    stats = db.get_system_stats()
    return jsonify({
        "status": "healthy",
        "service": "MedTrack Cloud-Based Healthcare Management System",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "storage_mode": stats["storage_mode"],
        "aws_connected": db.use_aws,
        "aws_telemetry": stats.get("aws_status"),
        "region": stats["region"],
        "total_appointments": stats["total_appointments"],
        "total_users": stats["total_users"],
        "fallback_active": not db.use_aws
    }), 200


# -----------------------------------------------------------------------------
# Application Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print(" MedTrack: Cloud-Based Healthcare Management System")
    print(f" Storage Mode: {'AWS DynamoDB' if db.use_aws else 'Local Storage (local_db.json)'}")
    print(" Local URL: http://127.0.0.1:5000")
    print(" Health Endpoint: http://127.0.0.1:5000/health")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
