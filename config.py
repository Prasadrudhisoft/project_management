"""
Configuration file for Simple Project Manager
Now uses environment variables for secure production deployment
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'project_management_app'),
    'charset': 'utf8mb4'
}

# Flask Configuration
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application Settings
APP_NAME = os.getenv('APP_NAME', 'Simple Project Manager')
APP_VERSION = '1.0.0'

# Demo Data Settings
CREATE_DEMO_DATA = os.getenv('CREATE_DEMO_DATA', 'False').lower() == 'true'

# Validate critical configuration
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

if not DB_CONFIG['password']:
    raise ValueError("DB_PASSWORD environment variable is required")
