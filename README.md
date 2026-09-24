# MedTrack - Cloud-Based Healthcare Management System

MedTrack is a modern healthcare management platform designed to streamline patient-doctor interactions. It centralizes appointment booking, clinical diagnosis submissions, medical history management, and automated notifications.

The application is architected with a **Smart Hybrid Data Layer (Auto-Detection & Fallback)**:
- **Automatic AWS Cloud Detection**: When valid AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, or EC2 IAM Role) are detected and DynamoDB is accessible, MedTrack automatically engages AWS DynamoDB and AWS SNS!
- **Zero-Downtime Local Fallback**: If AWS credentials are absent, expired (e.g. Troven Labs 3-hour window ends), or offline, MedTrack automatically and silently falls back to the persistent Local Database (`local_db.json`) with zero crashes or errors!

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Users["Users & Stakeholders"]
        Admin["Admin"]
        Patient["Patient"]
        Doctor["Doctor"]
    end

    subgraph AppLayer["Application Layer (Local or EC2)"]
        UI["Web UI (HTML5, CSS3, Flask Templates)"]
        Flask["Flask Backend (app.py)"]
        DBMgr["Database Manager (db.py)"]
        Notif["Notification Service (notifier.py)"]
    end

    subgraph DataCloud["Storage & Cloud Services"]
        LocalDB[("Local Storage\nlocal_db.json")]
        DynamoDB[("Amazon DynamoDB\n6 Tables")]
        SNS["AWS SNS\nHealthcare Alerts"]
        IAM["AWS IAM\nRole-Based Access"]
    end

    Users --> UI
    UI --> Flask
    Flask --> DBMgr
    Flask --> Notif
    DBMgr -.->|USE_AWS=false| LocalDB
    DBMgr -.->|USE_AWS=true| DynamoDB
    Notif -.->|USE_AWS=true| SNS
    IAM -.->|RBAC Least Privilege| DynamoDB
    IAM -.->|RBAC Least Privilege| SNS
```

---

## 📊 Database Entity Model (Image 2)

```mermaid
erDiagram
    Users ||--o{ Doctors : "1:N"
    Users ||--o{ Patients : "1:N"
    Users ||--o{ Notifications : "1:N"
    Doctors ||--o{ Appointments : "1:N"
    Patients ||--o{ Appointments : "1:N"
    Appointments ||--|| Diagnosis : "1:1"

    Users {
        string UserID PK
        string Name
        string Email
        string Role
        string Password
        string Phone
        int LoginCount
    }
    Doctors {
        string DoctorID PK
        string UserID FK
        string Specialization
        string Experience
    }
    Patients {
        string PatientID PK
        string UserID FK
        int Age
        string MedicalHistory
    }
    Appointments {
        string AppointmentID PK
        string PatientID FK
        string DoctorID FK
        string Date
        string Time
        string Status
        string Reason
    }
    Diagnosis {
        string DiagnosisID PK
        string AppointmentID FK
        string DoctorID FK
        string PatientID FK
        string Report
        string Date
    }
    Notifications {
        string NotificationID PK
        string UserID FK
        string Message
        string Timestamp
        boolean Read
    }
```

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.10+
- Installed libraries: `Flask`, `boto3`, `python-dotenv`, `werkzeug`

### 2. Run the Application
Open your terminal in `C:\Users\User\.gemini\antigravity\scratch\medtrack` and start the server:

```bash
python app.py
```

The application will start on:
- **Web Portal**: [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **Health Check Endpoint**: [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health)

---

## 🔑 Pre-Seeded Demo Credentials

The local database comes pre-populated with ready-to-test accounts:

| Portal | Email | Password | Role | Features Accessible |
|---|---|---|---|---|
| **Patient** | `john.doe@gmail.com` | `Patient@123` | Patient | Book appointments, view medical history, search bookings, alerts |
| **Patient** | `emily.watson@gmail.com` | `Patient@123` | Patient | Profile management, view past consultations |
| **Doctor** | `sarah.johnson@medtrack.com` | `Doctor@123` | Doctor (Cardiology) | Clinical schedule, patient records, submit diagnosis |
| **Doctor** | `michael.chen@medtrack.com` | `Doctor@123` | Doctor (Neurology) | Patient history review, diagnose & complete visits |
| **Admin** | `admin@medtrack.com` | `Admin@123` | Administrator | System telemetry, user directory, login counts, audit |

---

## 🧪 Automated Testing

To run the full end-to-end verification test suite:

```bash
python test_app.py
```

This verifies:
1. `/health` API status and configuration
2. User authentication & `LoginCount` telemetry incrementing
3. Patient appointment booking and real-time alerts
4. Multi-parameter appointment searching
5. Doctor diagnosis submission & appointment status completion
6. Profile updates and medical history timeline

---

## ☁️ Transitioning to AWS (Post Troven Access Activation)

When your Troven Labs or AWS account access (3-hour temporary credentials) is activated:

1. **Open `.env`** in `C:\Users\User\.gemini\antigravity\scratch\medtrack\.env`:
   ```ini
   USE_AWS=true
   AWS_DEFAULT_REGION=us-east-1
   AWS_ACCESS_KEY_ID=<Your_Access_Key_ID>
   AWS_SECRET_ACCESS_KEY=<Your_Secret_Access_Key>
   AWS_SESSION_TOKEN=<Your_Session_Token>
   ```

2. **Provision Cloud DynamoDB Tables & SNS Topic**:
   ```bash
   python create_tables.py
   ```
   This will automatically create all 6 DynamoDB tables (`MedTrack_Users`, `MedTrack_Doctors`, etc.) with `PAY_PER_REQUEST` billing mode, and create the SNS topic.

3. **Paste the generated SNS Topic ARN** into `.env`:
   ```ini
   SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:MedTrack_Healthcare_Alerts
   ```

4. **Restart Flask**:
   ```bash
   python app.py
   ```
   MedTrack will now operate directly against AWS DynamoDB and AWS SNS!

For complete EC2 deployment instructions, Gunicorn & Nginx setup, and IAM role configuration, refer to `AWS_MIGRATION_GUIDE.md`.
