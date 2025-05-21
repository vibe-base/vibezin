#!/bin/bash

# Script to fix Google OAuth configuration on the production server

# Navigate to the project directory
cd /root/vibezin

# Activate the virtual environment
source venv/bin/activate

# Run the setup_social_auth management command
python manage.py setup_social_auth

# Restart the Django application
systemctl restart gunicorn

echo "Google OAuth configuration fixed and application restarted."
