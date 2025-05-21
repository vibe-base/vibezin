#!/bin/bash

# Script to set up social authentication on the production server

# Navigate to the project directory
cd /root/vibezin

# Activate the virtual environment
source venv/bin/activate

# Run the setup_social_auth management command
python manage.py setup_social_auth

echo "Social authentication setup complete."
