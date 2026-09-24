import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
from db import db

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class NotificationService:
    """
    Intelligent Hybrid Notification Service for MedTrack:
    - Automatically checks for AWS SNS credentials and topic ARN.
    - If AWS SNS is reachable: publishes real-time cloud messages.
    - If AWS SNS is not configured or offline: automatically and gracefully falls back
      to in-app database alerts and console telemetry without breaking!
    """

    def __init__(self):
        self.sns_client = None
        self.use_sns = False

        if BOTO3_AVAILABLE and Config.SNS_TOPIC_ARN:
            self._init_sns()
        else:
            print("[Notifier] AWS SNS Topic ARN not set. Running in Local In-App Notification Mode.")

    def _init_sns(self):
        try:
            from botocore.config import Config as BotoConfig
            probe_config = BotoConfig(connect_timeout=2, read_timeout=2, retries={"max_attempts": 1})

            boto_kwargs = {"region_name": Config.AWS_REGION, "config": probe_config}
            if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
                boto_kwargs["aws_access_key_id"] = Config.AWS_ACCESS_KEY_ID
                boto_kwargs["aws_secret_access_key"] = Config.AWS_SECRET_ACCESS_KEY
                if Config.AWS_SESSION_TOKEN:
                    boto_kwargs["aws_session_token"] = Config.AWS_SESSION_TOKEN

            self.sns_client = boto3.client("sns", **boto_kwargs)
            # Probe topic
            self.sns_client.get_topic_attributes(TopicArn=Config.SNS_TOPIC_ARN)
            self.use_sns = True
            print(f"[Notifier] [AWS SNS ACTIVE] Successfully connected to SNS Topic: {Config.SNS_TOPIC_ARN}")
        except Exception as e:
            self.use_sns = False
            print(f"[Notifier] [AUTO-FALLBACK] AWS SNS probe failed ({e}). Using local in-app alerts.")

    def send_notification(self, user_id, subject, message, recipient_email=None):
        """
        Dual notification dispatcher:
        1. Always writes in-app notification to MedTrack DB (local or DynamoDB).
        2. If AWS SNS is active, publishes to cloud topic.
        3. If SMTP is configured, sends email.
        """
        # 1. In-App Notification (Always recorded)
        db.create_notification(user_id, f"[{subject}] {message}")
        print(f"[Notifier -> In-App DB] User {user_id}: {subject} | {message}")

        # 2. AWS SNS Publish (If connected)
        if self.use_sns and self.sns_client and Config.SNS_TOPIC_ARN:
            try:
                response = self.sns_client.publish(
                    TopicArn=Config.SNS_TOPIC_ARN,
                    Subject=subject[:100],
                    Message=f"{subject}\n\n{message}\n\n- MedTrack Healthcare Platform"
                )
                print(f"[Notifier -> AWS SNS] Published MessageId: {response.get('MessageId')}")
            except Exception as e:
                print(f"[Notifier -> AWS SNS Warning] Publish failed ({e}). Fallback to in-app.")

        # 3. Optional SMTP Fallback
        if recipient_email and Config.SENDER_EMAIL and Config.SENDER_PASSWORD:
            try:
                msg = MIMEMultipart()
                msg["From"] = Config.SENDER_EMAIL
                msg["To"] = recipient_email
                msg["Subject"] = f"[MedTrack] {subject}"
                msg.attach(MIMEText(message, "plain"))

                server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
                server.starttls()
                server.login(Config.SENDER_EMAIL, Config.SENDER_PASSWORD)
                server.sendmail(Config.SENDER_EMAIL, recipient_email, msg.as_string())
                server.quit()
                print(f"[Notifier -> SMTP] Sent email to {recipient_email}")
            except Exception as e:
                print(f"[Notifier -> SMTP Warning] SMTP failed: {e}")

        return True

    def notify_appointment_booked(self, appointment, patient, doctor):
        date_str = appointment.get("Date")
        time_str = appointment.get("Time")
        doc_name = doctor.get("Name", "Doctor")
        pat_name = patient.get("Name", "Patient")

        pat_subj = "Appointment Confirmation: MedTrack"
        pat_msg = (
            f"Hello {pat_name}, your appointment with {doc_name} is confirmed for "
            f"{date_str} at {time_str}. Reference ID: {appointment.get('AppointmentID')}."
        )
        self.send_notification(patient.get("UserID"), pat_subj, pat_msg, patient.get("Email"))

        doc_subj = "New Appointment Scheduled"
        doc_msg = (
            f"Hello {doc_name}, a new appointment has been scheduled with patient {pat_name} on "
            f"{date_str} at {time_str}. Reference ID: {appointment.get('AppointmentID')}."
        )
        self.send_notification(doctor.get("UserID"), doc_subj, doc_msg, doctor.get("Email"))

    def notify_diagnosis_submitted(self, diagnosis, patient, doctor):
        doc_name = doctor.get("Name", "Doctor")
        pat_name = patient.get("Name", "Patient")
        
        subj = "New Medical Diagnosis Report Available"
        msg = (
            f"Hello {pat_name}, {doc_name} has submitted a medical diagnosis report for your "
            f"appointment on {diagnosis.get('Date')}. Please log in to MedTrack to view your full history."
        )
        self.send_notification(patient.get("UserID"), subj, msg, patient.get("Email"))


# Global notifier instance
notifier = NotificationService()
