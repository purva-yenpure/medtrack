import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "medtrack-secret-key-2026-cloud-healthcare")
    
    # Auto-detection: If True, MedTrack automatically uses AWS when credentials exist,
    # otherwise it gracefully falls back to local storage without any errors.
    AUTO_DETECT_AWS = os.getenv("AUTO_DETECT_AWS", "true").lower() in ("true", "1", "yes")
    USE_AWS = os.getenv("USE_AWS", "auto").lower()
    
    # AWS Configuration (from .env or Troven Labs temporary credentials)
    AWS_REGION = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-1"))
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
    AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN", "").strip()
    
    # DynamoDB Table Names
    DYNAMODB_TABLE_USERS = os.getenv("DYNAMODB_TABLE_USERS", "MedTrack_Users")
    DYNAMODB_TABLE_DOCTORS = os.getenv("DYNAMODB_TABLE_DOCTORS", "MedTrack_Doctors")
    DYNAMODB_TABLE_PATIENTS = os.getenv("DYNAMODB_TABLE_PATIENTS", "MedTrack_Patients")
    DYNAMODB_TABLE_APPOINTMENTS = os.getenv("DYNAMODB_TABLE_APPOINTMENTS", "MedTrack_Appointments")
    DYNAMODB_TABLE_DIAGNOSIS = os.getenv("DYNAMODB_TABLE_DIAGNOSIS", "MedTrack_Diagnosis")
    DYNAMODB_TABLE_NOTIFICATIONS = os.getenv("DYNAMODB_TABLE_NOTIFICATIONS", "MedTrack_Notifications")
    
    # AWS SNS Configuration
    SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "").strip()
    
    # Optional SMTP Fallback Configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "").strip()
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "").strip()
    
    # Local Storage Path (Persistent JSON database)
    LOCAL_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_db.json")
