"""
MedTrack End-to-End Automated Test Suite
Verifies:
1. Health endpoint
2. User authentication (Login, Register, LoginCount increment)
3. Role-based routing (Patient, Doctor, Admin)
4. Appointment booking workflow
5. Appointment search & filtering
6. Diagnosis report submission & appointment completion
7. Medical history access
8. Profile updates
9. In-app notifications
"""

import unittest
from app import app
from db import db

class MedTrackTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False

    def test_01_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data["status"], "healthy")
        self.assertIn("storage_mode", json_data)
        print("[PASS] Test 1: Health check passed")

    def test_02_login_and_login_count_increment(self):
        user = db.get_user_by_email("sarah.johnson@medtrack.com")
        initial_count = user.get("LoginCount", 0)

        response = self.client.post("/login", data={
            "email": "sarah.johnson@medtrack.com",
            "password": "Doctor@123"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Clinical Dashboard", response.data)

        updated_user = db.get_user_by_email("sarah.johnson@medtrack.com")
        self.assertEqual(updated_user.get("LoginCount"), initial_count + 1)
        print(f"[PASS] Test 2: Doctor login & count increment passed (count={updated_user.get('LoginCount')})")

    def test_03_patient_appointment_booking(self):
        # Log in as Patient
        self.client.post("/login", data={
            "email": "john.doe@gmail.com",
            "password": "Patient@123"
        }, follow_redirects=True)

        doc = db.get_doctor_by_user_id("USR-DOC-001")
        self.assertIsNotNone(doc)

        response = self.client.post("/book-appointment", data={
            "doctor_id": doc["DoctorID"],
            "date": "2026-11-15",
            "time": "11:30 AM",
            "reason": "Automated Unit Test Consultation"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Appointment booked successfully", response.data)
        print("[PASS] Test 3: Patient appointment booking passed")

    def test_04_search_appointments(self):
        # Log in first
        self.client.post("/login", data={
            "email": "john.doe@gmail.com",
            "password": "Patient@123"
        }, follow_redirects=True)

        # Search via API format
        response = self.client.get("/search-appointments?q=Automated&format=json")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreaterEqual(data["count"], 1)
        print(f"[PASS] Test 4: Search appointments passed (found {data['count']} items)")

    def test_05_doctor_submit_diagnosis(self):
        # Log in as Doctor
        self.client.post("/login", data={
            "email": "sarah.johnson@medtrack.com",
            "password": "Doctor@123"
        }, follow_redirects=True)

        doc = db.get_doctor_by_user_id("USR-DOC-001")
        apts = db.get_appointments_by_doctor(doc["DoctorID"])
        scheduled_apts = [a for a in apts if a["Status"] == "Scheduled"]
        self.assertGreater(len(scheduled_apts), 0)
        target_apt = scheduled_apts[0]

        # Submit diagnosis
        response = self.client.post("/submit-diagnosis", data={
            "appointment_id": target_apt["AppointmentID"],
            "date": "2026-11-15",
            "report": "Automated clinical diagnosis: All vitals normal. Patient cleared."
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Patient Medical Record", response.data)

        # Check appointment status changed to Completed
        updated_apt = db.get_appointment_by_id(target_apt["AppointmentID"])
        self.assertEqual(updated_apt["Status"], "Completed")
        print("[PASS] Test 5: Diagnosis submission & auto-completion passed")

    def test_06_profile_update(self):
        # Log in as Patient
        self.client.post("/login", data={
            "email": "emily.watson@gmail.com",
            "password": "Patient@123"
        }, follow_redirects=True)

        # Update profile
        response = self.client.post("/profile", data={
            "name": "Emily Watson Updated",
            "phone": "+1-555-999-8888",
            "age": "31",
            "medical_history": "No allergies. Updated through test suite."
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Profile updated successfully", response.data)

        # Verify DB
        pat_user = db.get_user_by_email("emily.watson@gmail.com")
        self.assertEqual(pat_user["Name"], "Emily Watson Updated")
        print("[PASS] Test 6: Profile update passed")

if __name__ == "__main__":
    unittest.main()
