#!/bin/bash

# Script to restore Google OAuth configuration on the production server

# Navigate to the project directory
cd /root/vibezin

# Activate the virtual environment
source venv/bin/activate

# Run the setup_social_auth management command to ensure the Google OAuth provider is configured
python manage.py setup_social_auth

# Restart the Django application
systemctl restart gunicorn

echo "Google OAuth configuration restored and application restarted."
