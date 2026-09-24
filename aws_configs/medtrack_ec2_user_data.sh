#!/bin/bash
# ==============================================================================
# MedTrack EC2 User Data / Launch Script (Amazon Linux 2023 / Ubuntu 22.04)
# Automates Python, Gunicorn, Nginx, and Systemd Service setup
# ==============================================================================

set -e
echo "Starting MedTrack EC2 Provisioning..."

# Update OS and install prerequisites
if command -v dnf &> /dev/null; then
    # Amazon Linux 2023
    dnf update -y
    dnf install -y python3 python3-pip git nginx
elif command -v apt-get &> /dev/null; then
    # Ubuntu / Debian
    apt-get update -y
    apt-get install -y python3 python3-pip python3-venv git nginx
fi

# Directory setup
mkdir -p /var/www/medtrack
cd /var/www/medtrack

# Install python virtual environment & dependencies
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service for Gunicorn
cat << 'EOF' > /etc/systemd/system/medtrack.service
[Unit]
Description=MedTrack Cloud Healthcare Flask Application
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/var/www/medtrack
Environment="PATH=/var/www/medtrack/venv/bin"
EnvironmentFile=/var/www/medtrack/.env
ExecStart=/var/www/medtrack/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Nginx reverse proxy configuration
cat << 'EOF' > /etc/nginx/conf.d/medtrack.conf
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/medtrack/static;
        expires 30d;
    }
}
EOF

# Enable and start services
systemctl daemon-reload
systemctl enable medtrack
systemctl start medtrack
systemctl enable nginx
systemctl restart nginx

echo "MedTrack deployment completed successfully!"
