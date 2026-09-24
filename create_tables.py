"""
MedTrack AWS Resource Provisioning Script
Use this script once Troven Labs or AWS account access is provided to create:
1. DynamoDB Tables: Users, Doctors, Patients, Appointments, Diagnosis, Notifications
2. SNS Topic: MedTrack_Notifications_Topic
"""

import sys
import boto3
from config import Config

def create_dynamodb_tables():
    print(f"Connecting to AWS DynamoDB in region: {Config.AWS_REGION}...")
    boto_kwargs = {"region_name": Config.AWS_REGION}
    if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
        boto_kwargs["aws_access_key_id"] = Config.AWS_ACCESS_KEY_ID
        boto_kwargs["aws_secret_access_key"] = Config.AWS_SECRET_ACCESS_KEY
        if Config.AWS_SESSION_TOKEN:
            boto_kwargs["aws_session_token"] = Config.AWS_SESSION_TOKEN

    dynamodb = boto3.resource("dynamodb", **boto_kwargs)
    client = boto3.client("dynamodb", **boto_kwargs)
    existing_tables = client.list_tables().get("TableNames", [])

    tables_to_create = [
        {
            "name": Config.DYNAMODB_TABLE_USERS,
            "key": "UserID",
            "key_type": "HASH"
        },
        {
            "name": Config.DYNAMODB_TABLE_DOCTORS,
            "key": "DoctorID",
            "key_type": "HASH"
        },
        {
            "name": Config.DYNAMODB_TABLE_PATIENTS,
            "key": "PatientID",
            "key_type": "HASH"
        },
        {
            "name": Config.DYNAMODB_TABLE_APPOINTMENTS,
            "key": "AppointmentID",
            "key_type": "HASH"
        },
        {
            "name": Config.DYNAMODB_TABLE_DIAGNOSIS,
            "key": "DiagnosisID",
            "key_type": "HASH"
        },
        {
            "name": Config.DYNAMODB_TABLE_NOTIFICATIONS,
            "key": "NotificationID",
            "key_type": "HASH"
        }
    ]

    for t in tables_to_create:
        name = t["name"]
        if name in existing_tables:
            print(f"[-] Table {name} already exists. Skipping.")
            continue

        print(f"[+] Creating table {name} with Partition Key '{t['key']}'...")
        table = dynamodb.create_table(
            TableName=name,
            KeySchema=[
                {"AttributeName": t["key"], "KeyType": t["key_type"]}
            ],
            AttributeDefinitions=[
                {"AttributeName": t["key"], "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        print(f"[+] Waiting for table {name} to become ACTIVE...")
        table.meta.client.get_waiter("table_exists").wait(TableName=name)
        print(f"[✓] Table {name} created successfully!")

    print("\n--- All DynamoDB Tables are ready! ---\n")

def create_sns_topic():
    print(f"Creating AWS SNS Topic in region: {Config.AWS_REGION}...")
    boto_kwargs = {"region_name": Config.AWS_REGION}
    if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
        boto_kwargs["aws_access_key_id"] = Config.AWS_ACCESS_KEY_ID
        boto_kwargs["aws_secret_access_key"] = Config.AWS_SECRET_ACCESS_KEY
        if Config.AWS_SESSION_TOKEN:
            boto_kwargs["aws_session_token"] = Config.AWS_SESSION_TOKEN

    sns = boto3.client("sns", **boto_kwargs)
    try:
        response = sns.create_topic(Name="MedTrack_Healthcare_Alerts")
        topic_arn = response.get("TopicArn")
        print(f"[✓] SNS Topic Created: {topic_arn}")
        print(f"[*] Update your .env with: SNS_TOPIC_ARN={topic_arn}")
        return topic_arn
    except Exception as e:
        print(f"[!] Error creating SNS Topic: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print(" MedTrack AWS Cloud Resource Provisioner")
    print("=" * 60)
    try:
        create_dynamodb_tables()
        create_sns_topic()
    except Exception as e:
        print(f"[!] Provisioning failed: {e}")
        sys.exit(1)
