#!/bin/bash

SERVICE_FILE="/etc/systemd/system/logextracter.service"

echo "Creating systemd service for log extraction..."

# Create the systemd service file
cat <<EOF | sudo tee $SERVICE_FILE
[Unit]
Description=CloudPulse Systemd Log Extractor
After=network.target

[Service]
ExecStart=/bin/bash $(pwd)/extract_systemd_logs.sh
Restart=always
User=root
Group=root
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=logextracter

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable logextracter.service
sudo systemctl start logextracter.service

echo "Systemd service 'logextracter' is now running."
