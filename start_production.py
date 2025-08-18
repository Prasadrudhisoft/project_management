#!/usr/bin/env python3
"""
Production Startup Script
Performs all necessary checks and starts the application safely
"""

import os
import sys
from datetime import datetime

def check_environment():
    """Check if all required environment variables are set"""
    # Load environment first
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'SECRET_KEY',
        'DB_PASSWORD',
        'DB_HOST',
        'DB_USER',
        'DB_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please check your .env file or environment configuration.")
        return False
    
    # Check for development settings
    if os.getenv('DEBUG', 'false').lower() == 'true':
        print("⚠️  WARNING: DEBUG mode is enabled in production!")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    if os.getenv('CREATE_DEMO_DATA', 'false').lower() == 'true':
        print("⚠️  WARNING: Demo data creation is enabled!")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    return True

def check_database():
    """Test database connection and schema"""
    try:
        import config
        from utils.db_helper import DatabaseHelper
        
        print("🔍 Testing database connection...")
        db = DatabaseHelper(config.DB_CONFIG)
        
        conn = db.get_connection()
        if not conn:
            print("❌ Database connection failed!")
            return False
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s", 
                      (config.DB_CONFIG['database'],))
        table_count = cursor.fetchone()[0]
        
        if table_count == 0:
            print("⚠️  Database is empty. Initializing...")
            try:
                db.init_database()
                print("✅ Database initialized successfully")
            except Exception as e:
                print(f"❌ Database initialization failed: {e}")
                return False
        else:
            print(f"✅ Database connection successful ({table_count} tables found)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def check_security():
    """Verify security configurations"""
    print("🔒 Checking security configuration...")
    
    # Check bcrypt dependency
    try:
        import bcrypt
        print("✅ bcrypt password hashing available")
    except ImportError:
        print("❌ bcrypt not installed! Run: pip install bcrypt")
        return False
    
    # Check secret key strength
    secret_key = os.getenv('SECRET_KEY', '')
    if len(secret_key) < 32:
        print("⚠️  SECRET_KEY should be at least 32 characters long")
        return False
    
    if secret_key in ['your-secret-key-here', 'super-secure-secret-key-change-this-immediately-in-production-12345']:
        print("⚠️  Please change the default SECRET_KEY!")
        return False
    
    print("✅ Security configuration looks good")
    return True

def main():
    """Main production startup routine"""
    print("🚀 Simple Project Manager - Production Startup")
    print("=" * 50)
    print(f"⏰ Startup time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Environment check
    print("\n1. Checking environment variables...")
    if not check_environment():
        sys.exit(1)
    print("✅ Environment variables OK")
    
    # Security check
    print("\n2. Checking security configuration...")
    if not check_security():
        sys.exit(1)
    
    # Database check
    print("\n3. Checking database connection...")
    if not check_database():
        sys.exit(1)
    
    # Import and start the application
    print("\n4. Starting application...")
    try:
        from app import app
        import config
        
        print("✅ All checks passed - Starting Simple Project Manager")
        print(f"🌐 Running in {'DEBUG' if config.DEBUG else 'PRODUCTION'} mode")
        print(f"📊 Database: {config.DB_CONFIG['host']}:{config.DB_CONFIG['database']}")
        print("=" * 50)
        
        # Start with gunicorn settings for production
        app.run(
            debug=config.DEBUG,
            host='0.0.0.0',
            port=int(os.getenv('PORT', 8000)),
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Application startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
