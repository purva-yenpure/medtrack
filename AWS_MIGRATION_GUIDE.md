# MedTrack: AWS Cloud Deployment & Troven Labs Migration Guide

This step-by-step guide walks you through migrating the local MedTrack Flask application to AWS once your **Troven Labs 3-hour access window** or AWS account is activated.

---

## 📋 Epic Checklist Overview

| Epic | Description | Status | Command / Artifact |
|---|---|---|---|
| **Epic 1** | Local Backend & UI Development | ✅ Complete | `app.py`, `templates/`, `db.py` |
| **Epic 2** | AWS Account Setup & Login | ⏳ Ready for Activation | AWS Console Login |
| **Epic 3** | DynamoDB Tables Setup | ⚙️ Automated Script | `python create_tables.py` |
| **Epic 4** | AWS SNS Notification Setup | ⚙️ Automated Script | SNS Topic Creation & Subscriptions |
| **Epic 5** | IAM Role & Policy Setup | 📄 Policy Defined | `aws_configs/medtrack_iam_policy.json` |
| **Epic 6** | EC2 Instance Provisioning | 🌐 Config Ready | EC2 Launch (Security Groups: 80, 22) |
| **Epic 7** | Application Deployment on EC2 | 🚀 Shell Script Ready | `aws_configs/medtrack_ec2_user_data.sh` |
| **Epic 8** | Cloud Testing & Monitoring | 📊 Health & CloudWatch | `/health` endpoint & CloudWatch Logs |

---

## 🛠️ Step-by-Step Instructions

### Epic 1: Local Backend & UI Verification (Already Completed)
1. Run local test suite:
   ```bash
   python test_app.py
   ```
2. Verify all 6 tests pass `[PASS]` and all core routes (`/`, `/login`, `/register`, `/book-appointment`, `/submit-diagnosis`, `/profile`, `/search-appointments`, `/health`) function with `local_db.json`.

---

### Epic 2: AWS Account Setup & Temporary Credentials
Once Troven Labs access is launched:
1. Copy the temporary credentials provided in the Troven dashboard:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_SESSION_TOKEN`
   - `AWS_DEFAULT_REGION` (typically `us-east-1` or `us-west-2`)
2. Edit `.env` file in the project folder:
   ```ini
   USE_AWS=true
   AWS_DEFAULT_REGION=us-east-1
   AWS_ACCESS_KEY_ID=ASIA...YOUR_KEY...
   AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY...
   AWS_SESSION_TOKEN=IQoJb3JpZ2lu...YOUR_SESSION_TOKEN...
   ```

---

### Epic 3: DynamoDB Database Provisioning
Run the automated table provisioner:
```bash
python create_tables.py
```
This provisions:
- `MedTrack_Users` (Partition Key: `UserID` [String])
- `MedTrack_Doctors` (Partition Key: `DoctorID` [String])
- `MedTrack_Patients` (Partition Key: `PatientID` [String])
- `MedTrack_Appointments` (Partition Key: `AppointmentID` [String])
- `MedTrack_Diagnosis` (Partition Key: `DiagnosisID` [String])
- `MedTrack_Notifications` (Partition Key: `NotificationID` [String])

All tables are created with `PAY_PER_REQUEST` (On-Demand) billing to avoid provisioning costs.

---

### Epic 4: SNS Notification Setup & Subscriptions
The script `create_tables.py` automatically generates the SNS topic:
`arn:aws:sns:us-east-1:xxxxxx:MedTrack_Healthcare_Alerts`

1. Copy the generated ARN into `.env`:
   ```ini
   SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:MedTrack_Healthcare_Alerts
   ```
2. In the AWS SNS Console:
   - Open **Topics** -> `MedTrack_Healthcare_Alerts`
   - Click **Create subscription**
   - Protocol: `Email`
   - Endpoint: Enter your personal email
   - Click **Create subscription** and check your email inbox to click **Confirm subscription**.
3. Now, whenever an appointment is booked or diagnosis is submitted, AWS SNS will dispatch notifications to your email!

---

### Epic 5: IAM Role & Security Setup
1. In AWS IAM Console, go to **Roles** -> **Create role**.
2. Select **AWS service** -> **EC2**.
3. Attach a custom inline policy using `aws_configs/medtrack_iam_policy.json`.
4. Name the role `MedTrack_EC2_Role` and save.
5. If using an EC2 instance, attach `MedTrack_EC2_Role` to your EC2 instance so credentials do not need to be hardcoded in `.env` on the server!

---

### Epic 6: EC2 Instance Setup
1. Launch an EC2 Instance:
   - **AMI**: Amazon Linux 2023 AMI (or Ubuntu 22.04 LTS)
   - **Instance Type**: `t2.micro` or `t3.micro` (Free Tier eligible)
   - **Key Pair**: Select or create an SSH key pair
   - **IAM Instance Profile**: Attach `MedTrack_EC2_Role`
2. **Security Group Rules**:
   - Inbound HTTP (Port 80) -> Source: `0.0.0.0/0` (Anywhere)
   - Inbound SSH (Port 22) -> Source: Your IP / `0.0.0.0/0`
   - Inbound Custom TCP (Port 5000) -> Optional for direct testing

---

### Epic 7: Deployment on EC2
1. SSH into your EC2 instance:
   ```bash
   ssh -i your-key.pem ec2-user@<EC2-PUBLIC-IP>
   ```
2. Upload or clone the `medtrack` repository onto EC2:
   ```bash
   git clone <your-medtrack-repo-url> /var/www/medtrack
   ```
3. Run the automated setup script:
   ```bash
   chmod +x /var/www/medtrack/aws_configs/medtrack_ec2_user_data.sh
   sudo /var/www/medtrack/aws_configs/medtrack_ec2_user_data.sh
   ```
4. Verify services:
   ```bash
   sudo systemctl status medtrack
   sudo systemctl status nginx
   ```
5. Open `http://<EC2-PUBLIC-IP>` in your browser!

---

### Epic 8: Testing & CloudWatch Monitoring
1. Visit `http://<EC2-PUBLIC-IP>/health` to verify JSON health response:
   ```json
   {
     "status": "healthy",
     "service": "MedTrack Cloud-Based Healthcare Management System",
     "storage_mode": "AWS DynamoDB",
     "region": "us-east-1",
     "database_status": "connected"
   }
   ```
2. In AWS CloudWatch:
   - View EC2 CPU Utilization & Network In/Out.
   - Configure a CloudWatch Alarm for CPU > 80%.
   - Stream Gunicorn error logs to CloudWatch Log Groups.
