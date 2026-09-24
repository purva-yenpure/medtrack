import json
import os
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

# Try importing boto3
try:
    import boto3
    from boto3.dynamodb.conditions import Key, Attr
    from botocore.exceptions import BotoCoreError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class DatabaseManager:
    """
    Intelligent Hybrid Data Layer for MedTrack:
    - Automatically detects AWS credentials (from .env, environment, or EC2 IAM Role).
    - If AWS credentials are valid and DynamoDB is accessible, connects to AWS Cloud Mode.
    - If AWS credentials are not configured, expired, or network is offline, automatically
      and gracefully falls back to Local Storage (local_db.json) with ZERO interruption!
    """

    def __init__(self):
        self.use_aws = False
        self.aws_reason = "Local mode by default"
        self.local_file = Config.LOCAL_DB_FILE
        self.local_db = {
            "Users": {},
            "Doctors": {},
            "Patients": {},
            "Appointments": {},
            "Diagnosis": {},
            "Notifications": {}
        }
        
        # 1. Always load local DB first so fallback is instant with pre-seeded data
        self._load_local_db()

        # 2. Check if we should attempt AWS connection
        if BOTO3_AVAILABLE and self._should_attempt_aws():
            self._init_aws()
        else:
            self.aws_reason = "No AWS credentials detected in environment. Using Local Storage."
            print(f"[MedTrack DB] {self.aws_reason}")

    def _should_attempt_aws(self):
        """Check if AWS credentials are provided or AWS mode is explicitly requested"""
        if Config.USE_AWS in ("false", "0", "no"):
            return False

        if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
            return True

        if Config.USE_AWS in ("true", "1", "yes"):
            return True

        # Check if environment / IAM role on EC2 provides credentials
        try:
            session = boto3.Session(region_name=Config.AWS_REGION)
            creds = session.get_credentials()
            if creds and creds.access_key:
                return True
        except Exception:
            pass

        return False

    def _init_aws(self):
        """Attempt connection to AWS DynamoDB with graceful fallback if unavailable"""
        try:
            from botocore.config import Config as BotoConfig
            probe_config = BotoConfig(connect_timeout=2, read_timeout=2, retries={"max_attempts": 1})

            boto_kwargs = {"region_name": Config.AWS_REGION, "config": probe_config}
            if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
                boto_kwargs["aws_access_key_id"] = Config.AWS_ACCESS_KEY_ID
                boto_kwargs["aws_secret_access_key"] = Config.AWS_SECRET_ACCESS_KEY
                if Config.AWS_SESSION_TOKEN:
                    boto_kwargs["aws_session_token"] = Config.AWS_SESSION_TOKEN

            dynamodb = boto3.resource("dynamodb", **boto_kwargs)
            client = dynamodb.meta.client

            # Probe AWS connection by listing tables (timeout after 4 seconds)
            existing_tables = client.list_tables().get("TableNames", [])
            
            # Check if required tables exist
            required = [Config.DYNAMODB_TABLE_USERS, Config.DYNAMODB_TABLE_APPOINTMENTS]
            has_tables = any(t in existing_tables for t in required)

            if has_tables:
                self.dynamodb = dynamodb
                self.table_users = dynamodb.Table(Config.DYNAMODB_TABLE_USERS)
                self.table_doctors = dynamodb.Table(Config.DYNAMODB_TABLE_DOCTORS)
                self.table_patients = dynamodb.Table(Config.DYNAMODB_TABLE_PATIENTS)
                self.table_appointments = dynamodb.Table(Config.DYNAMODB_TABLE_APPOINTMENTS)
                self.table_diagnosis = dynamodb.Table(Config.DYNAMODB_TABLE_DIAGNOSIS)
                self.table_notifications = dynamodb.Table(Config.DYNAMODB_TABLE_NOTIFICATIONS)
                
                self.use_aws = True
                self.aws_reason = f"Connected to AWS DynamoDB in {Config.AWS_REGION}"
                print(f"[MedTrack DB] [AWS MODE ACTIVE] Successfully connected to AWS DynamoDB ({Config.AWS_REGION})!")
            else:
                self.use_aws = False
                self.aws_reason = f"AWS credentials valid, but DynamoDB tables are not yet created. Run 'python create_tables.py'. Falling back to Local Storage."
                print(f"[MedTrack DB] [AUTO-FALLBACK] {self.aws_reason}")

        except Exception as e:
            self.use_aws = False
            self.aws_reason = f"AWS connection probe failed ({e}). Falling back to Local Storage."
            print(f"[MedTrack DB] [AUTO-FALLBACK] {self.aws_reason}")

    # -------------------------------------------------------------
    # Local Storage Management
    # -------------------------------------------------------------
    def _load_local_db(self):
        if os.path.exists(self.local_file):
            try:
                with open(self.local_file, "r") as f:
                    self.local_db = json.load(f)
            except Exception as e:
                print(f"[MedTrack DB] Error reading local DB file: {e}")
                self.local_db = {
                    "Users": {}, "Doctors": {}, "Patients": {},
                    "Appointments": {}, "Diagnosis": {}, "Notifications": {}
                }
        else:
            self._seed_default_data()
            self._save_local_db()

    def _save_local_db(self):
        try:
            with open(self.local_file, "w") as f:
                json.dump(self.local_db, f, indent=2)
        except Exception as e:
            print(f"[MedTrack DB] Error saving local DB: {e}")

    def _seed_default_data(self):
        """Seed default accounts: Admin, 2 Doctors, 2 Patients"""
        print("[MedTrack DB] Seeding starter demo data into local storage...")
        
        # Admin User
        admin_uid = "USR-ADMIN-001"
        self.local_db["Users"][admin_uid] = {
            "UserID": admin_uid,
            "Name": "MedTrack Administrator",
            "Email": "admin@medtrack.com",
            "Role": "Admin",
            "Password": generate_password_hash("Admin@123"),
            "Phone": "+1-800-555-0199",
            "LoginCount": 0,
            "CreatedAt": datetime.now().isoformat()
        }

        # Doctor 1: Dr. Sarah Johnson
        doc1_uid = "USR-DOC-001"
        doc1_id = "DOC-001"
        self.local_db["Users"][doc1_uid] = {
            "UserID": doc1_uid,
            "Name": "Dr. Sarah Johnson, MD",
            "Email": "sarah.johnson@medtrack.com",
            "Role": "Doctor",
            "Password": generate_password_hash("Doctor@123"),
            "Phone": "+1-555-012-3456",
            "LoginCount": 0,
            "CreatedAt": datetime.now().isoformat()
        }
        self.local_db["Doctors"][doc1_id] = {
            "DoctorID": doc1_id,
            "UserID": doc1_uid,
            "Specialization": "Cardiology",
            "Experience": "12 Years"
        }

        # Doctor 2: Dr. Michael Chen
        doc2_uid = "USR-DOC-002"
        doc2_id = "DOC-002"
        self.local_db["Users"][doc2_uid] = {
            "UserID": doc2_uid,
            "Name": "Dr. Michael Chen, MD",
            "Email": "michael.chen@medtrack.com",
            "Role": "Doctor",
            "Password": generate_password_hash("Doctor@123"),
            "Phone": "+1-555-012-7890",
            "LoginCount": 0,
            "CreatedAt": datetime.now().isoformat()
        }
        self.local_db["Doctors"][doc2_id] = {
            "DoctorID": doc2_id,
            "UserID": doc2_uid,
            "Specialization": "Neurology & General Practice",
            "Experience": "9 Years"
        }

        # Patient 1: Johnathan Doe
        pat1_uid = "USR-PAT-001"
        pat1_id = "PAT-001"
        self.local_db["Users"][pat1_uid] = {
            "UserID": pat1_uid,
            "Name": "Johnathan Doe",
            "Email": "john.doe@gmail.com",
            "Role": "Patient",
            "Password": generate_password_hash("Patient@123"),
            "Phone": "+1-555-987-6543",
            "LoginCount": 0,
            "CreatedAt": datetime.now().isoformat()
        }
        self.local_db["Patients"][pat1_id] = {
            "PatientID": pat1_id,
            "UserID": pat1_uid,
            "Age": 38,
            "MedicalHistory": "Mild hypertension diagnosed in 2022. Allergic to penicillin. Regular annual checkups."
        }

        # Patient 2: Emily Watson
        pat2_uid = "USR-PAT-002"
        pat2_id = "PAT-002"
        self.local_db["Users"][pat2_uid] = {
            "UserID": pat2_uid,
            "Name": "Emily Watson",
            "Email": "emily.watson@gmail.com",
            "Role": "Patient",
            "Password": generate_password_hash("Patient@123"),
            "Phone": "+1-555-654-3210",
            "LoginCount": 0,
            "CreatedAt": datetime.now().isoformat()
        }
        self.local_db["Patients"][pat2_id] = {
            "PatientID": pat2_id,
            "UserID": pat2_uid,
            "Age": 29,
            "MedicalHistory": "Occasional migraines. No known drug allergies. Active lifestyle."
        }

        # Sample Appointment 1
        apt1_id = "APT-1001"
        self.local_db["Appointments"][apt1_id] = {
            "AppointmentID": apt1_id,
            "PatientID": pat1_id,
            "DoctorID": doc1_id,
            "Date": "2026-10-05",
            "Time": "10:30 AM",
            "Status": "Scheduled",
            "Reason": "Routine cardiology follow-up & BP monitoring",
            "CreatedAt": datetime.now().isoformat()
        }

        # Sample Appointment 2
        apt2_id = "APT-1002"
        self.local_db["Appointments"][apt2_id] = {
            "AppointmentID": apt2_id,
            "PatientID": pat2_id,
            "DoctorID": doc2_id,
            "Date": "2026-09-18",
            "Time": "02:00 PM",
            "Status": "Completed",
            "Reason": "Recurring headache assessment",
            "CreatedAt": datetime.now().isoformat()
        }

        # Sample Diagnosis for Appointment 2
        dia1_id = "DIA-5001"
        self.local_db["Diagnosis"][dia1_id] = {
            "DiagnosisID": dia1_id,
            "AppointmentID": apt2_id,
            "DoctorID": doc2_id,
            "PatientID": pat2_id,
            "Report": "Patient evaluated for tension-type headache. Neurological exam normal. Recommended lifestyle adjustments and hydration.",
            "Date": "2026-09-18"
        }

        # Notifications
        notif1_id = "NOTIF-001"
        self.local_db["Notifications"][notif1_id] = {
            "NotificationID": notif1_id,
            "UserID": pat1_uid,
            "Message": "Welcome to MedTrack! Your appointment with Dr. Sarah Johnson is scheduled for Oct 5, 2026.",
            "Timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            "Read": False
        }

    # -------------------------------------------------------------
    # User Operations with Auto-Fallback
    # -------------------------------------------------------------
    def get_user_by_email(self, email):
        email_clean = email.strip().lower()
        if self.use_aws:
            try:
                response = self.table_users.scan(
                    FilterExpression=Attr("Email").eq(email_clean)
                )
                items = response.get("Items", [])
                if items:
                    return items[0]
            except Exception as e:
                print(f"[AWS Warning] get_user_by_email fallback to local: {e}")

        # Local fallback
        for u in self.local_db["Users"].values():
            if u.get("Email", "").strip().lower() == email_clean:
                return u
        return None

    def get_user_by_id(self, user_id):
        if self.use_aws:
            try:
                response = self.table_users.get_item(Key={"UserID": user_id})
                item = response.get("Item")
                if item:
                    return item
            except Exception as e:
                print(f"[AWS Warning] get_user_by_id fallback to local: {e}")

        return self.local_db["Users"].get(user_id)

    def create_user(self, name, email, role, password, phone, **extra):
        email_clean = email.strip().lower()
        if self.get_user_by_email(email_clean):
            return None, "An account with this email address already exists."

        user_id = "USR-" + str(uuid.uuid4())[:8].upper()
        hashed_password = generate_password_hash(password)
        now_iso = datetime.now().isoformat()

        user_item = {
            "UserID": user_id,
            "Name": name.strip(),
            "Email": email_clean,
            "Role": role,
            "Password": hashed_password,
            "Phone": phone.strip(),
            "LoginCount": 0,
            "CreatedAt": now_iso
        }

        child_item = None
        if role == "Doctor":
            doctor_id = "DOC-" + str(uuid.uuid4())[:6].upper()
            child_item = {
                "DoctorID": doctor_id,
                "UserID": user_id,
                "Specialization": extra.get("specialization", "General Medicine"),
                "Experience": extra.get("experience", "1 Year")
            }
        elif role == "Patient":
            patient_id = "PAT-" + str(uuid.uuid4())[:6].upper()
            child_item = {
                "PatientID": patient_id,
                "UserID": user_id,
                "Age": int(extra.get("age", 25)),
                "MedicalHistory": extra.get("medical_history", "None recorded.")
            }

        if self.use_aws:
            try:
                self.table_users.put_item(Item=user_item)
                if role == "Doctor" and child_item:
                    self.table_doctors.put_item(Item=child_item)
                elif role == "Patient" and child_item:
                    self.table_patients.put_item(Item=child_item)
            except Exception as e:
                print(f"[AWS Warning] create_user writing to local due to: {e}")

        # Always maintain local copy
        self.local_db["Users"][user_id] = user_item
        if role == "Doctor" and child_item:
            self.local_db["Doctors"][child_item["DoctorID"]] = child_item
        elif role == "Patient" and child_item:
            self.local_db["Patients"][child_item["PatientID"]] = child_item
        self._save_local_db()

        return user_item, None

    def verify_password(self, stored_hash, password):
        return check_password_hash(stored_hash, password)

    def increment_login_count(self, user_id):
        if self.use_aws:
            try:
                self.table_users.update_item(
                    Key={"UserID": user_id},
                    UpdateExpression="SET LoginCount = if_not_exists(LoginCount, :start) + :inc",
                    ExpressionAttributeValues={":inc": 1, ":start": 0}
                )
            except Exception as e:
                print(f"[AWS Warning] increment_login_count fallback: {e}")

        # Local update
        if user_id in self.local_db["Users"]:
            self.local_db["Users"][user_id]["LoginCount"] = (
                self.local_db["Users"][user_id].get("LoginCount", 0) + 1
            )
            self._save_local_db()

    def update_profile(self, user_id, updates):
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "User not found."

        if self.use_aws:
            try:
                user_updates = []
                attr_values = {}
                for key in ["Name", "Phone"]:
                    if key in updates:
                        user_updates.append(f"{key} = :{key.lower()}")
                        attr_values[f":{key.lower()}"] = updates[key]

                if user_updates:
                    self.table_users.update_item(
                        Key={"UserID": user_id},
                        UpdateExpression="SET " + ", ".join(user_updates),
                        ExpressionAttributeValues=attr_values
                    )
            except Exception as e:
                print(f"[AWS Warning] update_profile fallback: {e}")

        # Local update
        if "Name" in updates and user_id in self.local_db["Users"]:
            self.local_db["Users"][user_id]["Name"] = updates["Name"]
        if "Phone" in updates and user_id in self.local_db["Users"]:
            self.local_db["Users"][user_id]["Phone"] = updates["Phone"]

        role = user.get("Role")
        if role == "Patient":
            pat = self.get_patient_by_user_id(user_id)
            if pat:
                pid = pat["PatientID"]
                if "Age" in updates:
                    self.local_db["Patients"][pid]["Age"] = int(updates["Age"])
                if "MedicalHistory" in updates:
                    self.local_db["Patients"][pid]["MedicalHistory"] = updates["MedicalHistory"]
        elif role == "Doctor":
            doc = self.get_doctor_by_user_id(user_id)
            if doc:
                did = doc["DoctorID"]
                if "Specialization" in updates:
                    self.local_db["Doctors"][did]["Specialization"] = updates["Specialization"]
                if "Experience" in updates:
                    self.local_db["Doctors"][did]["Experience"] = updates["Experience"]

        self._save_local_db()
        return True, "Profile updated successfully."

    # -------------------------------------------------------------
    # Doctor & Patient Lookups
    # -------------------------------------------------------------
    def get_doctor_by_id(self, doctor_id):
        if self.use_aws:
            try:
                res = self.table_doctors.get_item(Key={"DoctorID": doctor_id})
                doc = res.get("Item")
                if doc:
                    user = self.get_user_by_id(doc["UserID"])
                    if user:
                        doc["Name"] = user.get("Name")
                        doc["Email"] = user.get("Email")
                        doc["Phone"] = user.get("Phone")
                    return doc
            except Exception as e:
                print(f"[AWS Warning] get_doctor_by_id fallback: {e}")

        doc = self.local_db["Doctors"].get(doctor_id)
        if doc:
            res = dict(doc)
            user = self.get_user_by_id(res.get("UserID"))
            if user:
                res["Name"] = user.get("Name")
                res["Email"] = user.get("Email")
                res["Phone"] = user.get("Phone")
            return res
        return None

    def get_doctor_by_user_id(self, user_id):
        if self.use_aws:
            try:
                res = self.table_doctors.scan(FilterExpression=Attr("UserID").eq(user_id))
                items = res.get("Items", [])
                if items:
                    return items[0]
            except Exception as e:
                print(f"[AWS Warning] get_doctor_by_user_id fallback: {e}")

        for doc in self.local_db["Doctors"].values():
            if doc.get("UserID") == user_id:
                return doc
        return None

    def get_all_doctors(self):
        doctors = []
        if self.use_aws:
            try:
                res = self.table_doctors.scan()
                for d in res.get("Items", []):
                    user = self.get_user_by_id(d.get("UserID"))
                    doc_copy = dict(d)
                    if user:
                        doc_copy["Name"] = user.get("Name")
                        doc_copy["Email"] = user.get("Email")
                        doc_copy["Phone"] = user.get("Phone")
                    doctors.append(doc_copy)
                if doctors:
                    return doctors
            except Exception as e:
                print(f"[AWS Warning] get_all_doctors fallback: {e}")

        # Local
        for d in self.local_db["Doctors"].values():
            doc_copy = dict(d)
            user = self.get_user_by_id(d.get("UserID"))
            if user:
                doc_copy["Name"] = user.get("Name")
                doc_copy["Email"] = user.get("Email")
                doc_copy["Phone"] = user.get("Phone")
            doctors.append(doc_copy)
        return doctors

    def get_patient_by_id(self, patient_id):
        if self.use_aws:
            try:
                res = self.table_patients.get_item(Key={"PatientID": patient_id})
                pat = res.get("Item")
                if pat:
                    user = self.get_user_by_id(pat["UserID"])
                    if user:
                        pat["Name"] = user.get("Name")
                        pat["Email"] = user.get("Email")
                        pat["Phone"] = user.get("Phone")
                    return pat
            except Exception as e:
                print(f"[AWS Warning] get_patient_by_id fallback: {e}")

        pat = self.local_db["Patients"].get(patient_id)
        if pat:
            res = dict(pat)
            user = self.get_user_by_id(res.get("UserID"))
            if user:
                res["Name"] = user.get("Name")
                res["Email"] = user.get("Email")
                res["Phone"] = user.get("Phone")
            return res
        return None

    def get_patient_by_user_id(self, user_id):
        if self.use_aws:
            try:
                res = self.table_patients.scan(FilterExpression=Attr("UserID").eq(user_id))
                items = res.get("Items", [])
                if items:
                    return items[0]
            except Exception as e:
                print(f"[AWS Warning] get_patient_by_user_id fallback: {e}")

        for pat in self.local_db["Patients"].values():
            if pat.get("UserID") == user_id:
                return pat
        return None

    # -------------------------------------------------------------
    # Appointments with Auto-Fallback
    # -------------------------------------------------------------
    def create_appointment(self, patient_id, doctor_id, date, time, reason="General Consultation"):
        appointment_id = "APT-" + str(uuid.uuid4())[:8].upper()
        appointment_item = {
            "AppointmentID": appointment_id,
            "PatientID": patient_id,
            "DoctorID": doctor_id,
            "Date": date,
            "Time": time,
            "Status": "Scheduled",
            "Reason": reason.strip(),
            "CreatedAt": datetime.now().isoformat()
        }

        if self.use_aws:
            try:
                self.table_appointments.put_item(Item=appointment_item)
            except Exception as e:
                print(f"[AWS Warning] create_appointment writing locally: {e}")

        # Always save locally
        self.local_db["Appointments"][appointment_id] = appointment_item
        self._save_local_db()

        return appointment_item, None

    def get_appointment_by_id(self, appointment_id):
        item = None
        if self.use_aws:
            try:
                res = self.table_appointments.get_item(Key={"AppointmentID": appointment_id})
                item = res.get("Item")
            except Exception as e:
                print(f"[AWS Warning] get_appointment_by_id fallback: {e}")

        if not item:
            item = self.local_db["Appointments"].get(appointment_id)

        if item:
            item_copy = dict(item)
            doc = self.get_doctor_by_id(item_copy.get("DoctorID"))
            pat = self.get_patient_by_id(item_copy.get("PatientID"))
            item_copy["DoctorName"] = doc.get("Name", "Unknown Doctor") if doc else "Unknown Doctor"
            item_copy["DoctorSpecialization"] = doc.get("Specialization", "") if doc else ""
            item_copy["PatientName"] = pat.get("Name", "Unknown Patient") if pat else "Unknown Patient"
            item_copy["PatientAge"] = pat.get("Age", "") if pat else ""
            return item_copy
        return None

    def get_appointments_by_patient(self, patient_id):
        all_apts = []
        if self.use_aws:
            try:
                res = self.table_appointments.scan(FilterExpression=Attr("PatientID").eq(patient_id))
                all_apts = res.get("Items", [])
            except Exception as e:
                print(f"[AWS Warning] get_appointments_by_patient fallback: {e}")

        if not all_apts:
            all_apts = [a for a in self.local_db["Appointments"].values() if a.get("PatientID") == patient_id]

        enriched = []
        for apt in sorted(all_apts, key=lambda x: (x.get("Date", ""), x.get("Time", "")), reverse=True):
            apt_copy = dict(apt)
            doc = self.get_doctor_by_id(apt.get("DoctorID"))
            pat = self.get_patient_by_id(apt.get("PatientID"))
            apt_copy["DoctorName"] = doc.get("Name", "Unknown Doctor") if doc else "Unknown Doctor"
            apt_copy["DoctorSpecialization"] = doc.get("Specialization", "") if doc else ""
            apt_copy["PatientName"] = pat.get("Name", "Unknown Patient") if pat else "Unknown Patient"
            enriched.append(apt_copy)
        return enriched

    def get_appointments_by_doctor(self, doctor_id):
        all_apts = []
        if self.use_aws:
            try:
                res = self.table_appointments.scan(FilterExpression=Attr("DoctorID").eq(doctor_id))
                all_apts = res.get("Items", [])
            except Exception as e:
                print(f"[AWS Warning] get_appointments_by_doctor fallback: {e}")

        if not all_apts:
            all_apts = [a for a in self.local_db["Appointments"].values() if a.get("DoctorID") == doctor_id]

        enriched = []
        for apt in sorted(all_apts, key=lambda x: (x.get("Date", ""), x.get("Time", "")), reverse=True):
            apt_copy = dict(apt)
            doc = self.get_doctor_by_id(apt.get("DoctorID"))
            pat = self.get_patient_by_id(apt.get("PatientID"))
            apt_copy["DoctorName"] = doc.get("Name", "Unknown Doctor") if doc else "Unknown Doctor"
            apt_copy["PatientName"] = pat.get("Name", "Unknown Patient") if pat else "Unknown Patient"
            apt_copy["PatientAge"] = pat.get("Age", "") if pat else ""
            enriched.append(apt_copy)
        return enriched

    def get_all_appointments(self):
        all_apts = []
        if self.use_aws:
            try:
                res = self.table_appointments.scan()
                all_apts = res.get("Items", [])
            except Exception as e:
                print(f"[AWS Warning] get_all_appointments fallback: {e}")

        if not all_apts:
            all_apts = list(self.local_db["Appointments"].values())

        enriched = []
        for apt in sorted(all_apts, key=lambda x: (x.get("Date", ""), x.get("Time", "")), reverse=True):
            apt_copy = dict(apt)
            doc = self.get_doctor_by_id(apt.get("DoctorID"))
            pat = self.get_patient_by_id(apt.get("PatientID"))
            apt_copy["DoctorName"] = doc.get("Name", "Unknown Doctor") if doc else "Unknown Doctor"
            apt_copy["PatientName"] = pat.get("Name", "Unknown Patient") if pat else "Unknown Patient"
            enriched.append(apt_copy)
        return enriched

    def update_appointment_status(self, appointment_id, new_status):
        if self.use_aws:
            try:
                self.table_appointments.update_item(
                    Key={"AppointmentID": appointment_id},
                    UpdateExpression="SET #st = :s",
                    ExpressionAttributeNames={"#st": "Status"},
                    ExpressionAttributeValues={":s": new_status}
                )
            except Exception as e:
                print(f"[AWS Warning] update_appointment_status fallback: {e}")

        if appointment_id in self.local_db["Appointments"]:
            self.local_db["Appointments"][appointment_id]["Status"] = new_status
            self._save_local_db()
            return True
        return False

    def search_appointments(self, query="", date_filter="", status_filter="", role=None, entity_id=None):
        if role == "Patient":
            apts = self.get_appointments_by_patient(entity_id)
        elif role == "Doctor":
            apts = self.get_appointments_by_doctor(entity_id)
        else:
            apts = self.get_all_appointments()

        results = []
        q = query.strip().lower()
        d = date_filter.strip()
        s = status_filter.strip().lower()

        for a in apts:
            if d and a.get("Date") != d:
                continue
            if s and a.get("Status", "").lower() != s:
                continue
            if q:
                match = (
                    q in a.get("AppointmentID", "").lower() or
                    q in a.get("DoctorName", "").lower() or
                    q in a.get("PatientName", "").lower() or
                    q in a.get("Reason", "").lower()
                )
                if not match:
                    continue
            results.append(a)

        return results

    # -------------------------------------------------------------
    # Diagnosis
    # -------------------------------------------------------------
    def create_diagnosis(self, appointment_id, doctor_id, patient_id, report, date=None):
        diagnosis_id = "DIA-" + str(uuid.uuid4())[:8].upper()
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        item = {
            "DiagnosisID": diagnosis_id,
            "AppointmentID": appointment_id,
            "DoctorID": doctor_id,
            "PatientID": patient_id,
            "Report": report.strip(),
            "Date": date,
            "CreatedAt": datetime.now().isoformat()
        }

        if self.use_aws:
            try:
                self.table_diagnosis.put_item(Item=item)
                self.update_appointment_status(appointment_id, "Completed")
            except Exception as e:
                print(f"[AWS Warning] create_diagnosis fallback: {e}")

        self.local_db["Diagnosis"][diagnosis_id] = item
        self.update_appointment_status(appointment_id, "Completed")
        self._save_local_db()

        return item, None

    def get_diagnoses_by_patient(self, patient_id):
        items = []
        if self.use_aws:
            try:
                res = self.table_diagnosis.scan(FilterExpression=Attr("PatientID").eq(patient_id))
                items = res.get("Items", [])
            except Exception as e:
                print(f"[AWS Warning] get_diagnoses_by_patient fallback: {e}")

        if not items:
            items = [d for d in self.local_db["Diagnosis"].values() if d.get("PatientID") == patient_id]

        enriched = []
        for d in sorted(items, key=lambda x: x.get("Date", ""), reverse=True):
            d_copy = dict(d)
            doc = self.get_doctor_by_id(d.get("DoctorID"))
            pat = self.get_patient_by_id(d.get("PatientID"))
            d_copy["DoctorName"] = doc.get("Name", "Unknown Doctor") if doc else "Unknown Doctor"
            d_copy["DoctorSpecialization"] = doc.get("Specialization", "") if doc else ""
            d_copy["PatientName"] = pat.get("Name", "Unknown Patient") if pat else "Unknown Patient"
            enriched.append(d_copy)
        return enriched

    def get_diagnoses_by_doctor(self, doctor_id):
        items = []
        if self.use_aws:
            try:
                res = self.table_diagnosis.scan(FilterExpression=Attr("DoctorID").eq(doctor_id))
                items = res.get("Items", [])
            except Exception as e:
                print(f"[AWS Warning] get_diagnoses_by_doctor fallback: {e}")

        if not items:
            items = [d for d in self.local_db["Diagnosis"].values() if d.get("DoctorID") == doctor_id]

        enriched = []
        for d in sorted(items, key=lambda x: x.get("Date", ""), reverse=True):
            d_copy = dict(d)
            doc = self.get_doctor_by_id(d.get("DoctorID"))
            pat = self.get_patient_by_id(d.get("PatientID"))
            d_copy["DoctorName"] = doc.get("Name", "Unknown Doctor") if doc else "Unknown Doctor"
            d_copy["PatientName"] = pat.get("Name", "Unknown Patient") if pat else "Unknown Patient"
            enriched.append(d_copy)
        return enriched

    # -------------------------------------------------------------
    # Notifications
    # -------------------------------------------------------------
    def create_notification(self, user_id, message):
        notif_id = "NOTIF-" + str(uuid.uuid4())[:8].upper()
        item = {
            "NotificationID": notif_id,
            "UserID": user_id,
            "Message": message.strip(),
            "Timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            "Read": False
        }

        if self.use_aws:
            try:
                self.table_notifications.put_item(Item=item)
            except Exception as e:
                print(f"[AWS Warning] create_notification fallback: {e}")

        self.local_db["Notifications"][notif_id] = item
        self._save_local_db()
        return item

    def get_notifications(self, user_id):
        items = []
        if self.use_aws:
            try:
                res = self.table_notifications.scan(FilterExpression=Attr("UserID").eq(user_id))
                items = res.get("Items", [])
            except Exception as e:
                print(f"[AWS Warning] get_notifications fallback: {e}")

        if not items:
            items = [n for n in self.local_db["Notifications"].values() if n.get("UserID") == user_id]

        return sorted(items, key=lambda x: x.get("Timestamp", ""), reverse=True)

    def mark_notification_read(self, notification_id):
        if self.use_aws:
            try:
                self.table_notifications.update_item(
                    Key={"NotificationID": notification_id},
                    UpdateExpression="SET #rd = :val",
                    ExpressionAttributeNames={"#rd": "Read"},
                    ExpressionAttributeValues={":val": True}
                )
            except Exception as e:
                print(f"[AWS Warning] mark_notification_read fallback: {e}")

        if notification_id in self.local_db["Notifications"]:
            self.local_db["Notifications"][notification_id]["Read"] = True
            self._save_local_db()

    # -------------------------------------------------------------
    # System Stats
    # -------------------------------------------------------------
    def get_system_stats(self):
        return {
            "total_users": len(self.local_db["Users"]),
            "total_doctors": len(self.local_db["Doctors"]),
            "total_patients": len(self.local_db["Patients"]),
            "total_appointments": len(self.local_db["Appointments"]),
            "total_diagnoses": len(self.local_db["Diagnosis"]),
            "storage_mode": "AWS DynamoDB (Cloud Active)" if self.use_aws else "Local Storage (Fallback Active)",
            "aws_status": self.aws_reason,
            "region": Config.AWS_REGION if self.use_aws else "Local (Offline)"
        }


# Global database singleton
db = DatabaseManager()
