#!/usr/bin/env python3
"""
Health Check Script for Simple Project Manager
Monitors application health, database connectivity, and system status
"""

import os
import sys
import time
import requests
import subprocess
from datetime import datetime
from utils.db_helper import DatabaseHelper
import config

class HealthChecker:
    def __init__(self):
        self.results = []
        self.status = "HEALTHY"
        self.app_url = "http://localhost:5000"
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_icon = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}
        icon = status_icon.get(status, "ℹ️")
        
        formatted_message = f"[{timestamp}] {icon} {message}"
        print(formatted_message)
        
        self.results.append({
            'timestamp': timestamp,
            'message': message,
            'status': status
        })
        
        if status in ["ERROR", "WARNING"]:
            self.status = "UNHEALTHY" if status == "ERROR" else "WARNING"

    def check_python_version(self):
        """Check Python version compatibility"""
        try:
            version = sys.version_info
            if version.major >= 3 and version.minor >= 7:
                self.log(f"Python version: {version.major}.{version.minor}.{version.micro}", "SUCCESS")
                return True
            else:
                self.log(f"Python version too old: {version.major}.{version.minor}.{version.micro}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Failed to check Python version: {e}", "ERROR")
            return False

    def check_virtual_environment(self):
        """Check if virtual environment is active"""
        try:
            if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
                self.log("Virtual environment: Active", "SUCCESS")
                return True
            else:
                self.log("Virtual environment: Not active", "WARNING")
                return False
        except Exception as e:
            self.log(f"Failed to check virtual environment: {e}", "ERROR")
            return False

    def check_required_packages(self):
        """Check if required packages are installed"""
        required_packages = ['flask', 'pymysql', 'bcrypt', 'python-dotenv']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.log(f"Package {package}: Installed", "SUCCESS")
            except ImportError:
                self.log(f"Package {package}: Missing", "ERROR")
                missing_packages.append(package)
        
        if missing_packages:
            self.log(f"Missing packages: {', '.join(missing_packages)}", "ERROR")
            return False
        return True

    def check_environment_variables(self):
        """Check required environment variables"""
        required_vars = ['SECRET_KEY', 'DB_PASSWORD']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.log(f"Missing environment variables: {', '.join(missing_vars)}", "ERROR")
            return False
        else:
            self.log("Environment variables: All set", "SUCCESS")
            return True

    def check_database_connection(self):
        """Check database connectivity"""
        try:
            db = DatabaseHelper(config.DB_CONFIG)
            connection = db.get_connection()
            if connection:
                connection.close()
                self.log("Database connection: Successful", "SUCCESS")
                return True
            else:
                self.log("Database connection: Failed", "ERROR")
                return False
        except Exception as e:
            self.log(f"Database connection error: {e}", "ERROR")
            return False

    def check_database_tables(self):
        """Check if database tables exist"""
        try:
            db = DatabaseHelper(config.DB_CONFIG)
            connection = db.get_connection()
            cursor = connection.cursor()
            
            # Get list of tables
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            
            required_tables = ['organizations', 'users', 'projects', 'tasks', 'messages', 'milestones']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                self.log(f"Missing database tables: {', '.join(missing_tables)}", "ERROR")
                return False
            else:
                self.log(f"Database tables: All present ({len(tables)} tables)", "SUCCESS")
                return True
                
        except Exception as e:
            self.log(f"Database table check error: {e}", "ERROR")
            return False

    def check_file_permissions(self):
        """Check file and directory permissions"""
        paths_to_check = [
            ('logs', 'directory'),
            ('uploads', 'directory'),
            ('.env', 'file'),
            ('app.py', 'file')
        ]
        
        issues = []
        for path, path_type in paths_to_check:
            if path_type == 'directory':
                if not os.path.exists(path):
                    try:
                        os.makedirs(path)
                        self.log(f"Created missing directory: {path}", "SUCCESS")
                    except Exception as e:
                        issues.append(f"Cannot create directory {path}: {e}")
                elif not os.access(path, os.W_OK):
                    issues.append(f"No write permission for directory {path}")
            elif path_type == 'file':
                if os.path.exists(path):
                    if not os.access(path, os.R_OK):
                        issues.append(f"No read permission for file {path}")
                else:
                    issues.append(f"Missing file: {path}")
        
        if issues:
            for issue in issues:
                self.log(issue, "ERROR")
            return False
        else:
            self.log("File permissions: OK", "SUCCESS")
            return True

    def check_disk_space(self):
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_gb = free // (1024**3)
            
            if free_gb < 1:
                self.log(f"Low disk space: {free_gb}GB available", "ERROR")
                return False
            elif free_gb < 5:
                self.log(f"Disk space warning: {free_gb}GB available", "WARNING")
                return True
            else:
                self.log(f"Disk space: {free_gb}GB available", "SUCCESS")
                return True
        except Exception as e:
            self.log(f"Disk space check error: {e}", "WARNING")
            return True

    def check_application_response(self):
        """Check if application is responding"""
        try:
            response = requests.get(self.app_url, timeout=10)
            if response.status_code == 200:
                self.log(f"Application response: OK (Status: {response.status_code})", "SUCCESS")
                return True
            else:
                self.log(f"Application response: Error (Status: {response.status_code})", "ERROR")
                return False
        except requests.exceptions.ConnectionError:
            self.log("Application not running or not accessible", "WARNING")
            return False
        except Exception as e:
            self.log(f"Application check error: {e}", "ERROR")
            return False

    def generate_report(self):
        """Generate health check report"""
        report = f"""
========================================
HEALTH CHECK REPORT
========================================
Status: {self.status}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Detailed Results:
"""
        for result in self.results:
            report += f"{result['timestamp']} [{result['status']}] {result['message']}\n"
        
        return report

    def run_all_checks(self):
        """Run all health checks"""
        print("🏥 Starting Health Check...")
        print("=" * 50)
        
        checks = [
            ('Python Version', self.check_python_version),
            ('Virtual Environment', self.check_virtual_environment),
            ('Required Packages', self.check_required_packages),
            ('Environment Variables', self.check_environment_variables),
            ('Database Connection', self.check_database_connection),
            ('Database Tables', self.check_database_tables),
            ('File Permissions', self.check_file_permissions),
            ('Disk Space', self.check_disk_space),
            ('Application Response', self.check_application_response)
        ]
        
        for check_name, check_func in checks:
            print(f"\n🔍 Checking {check_name}...")
            try:
                check_func()
            except Exception as e:
                self.log(f"Check '{check_name}' failed with exception: {e}", "ERROR")
        
        print("\n" + "=" * 50)
        print(f"🏥 Health Check Complete - Status: {self.status}")
        
        # Save report to file
        try:
            if not os.path.exists('logs'):
                os.makedirs('logs')
            
            report_file = f"logs/health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w') as f:
                f.write(self.generate_report())
            print(f"📄 Report saved to: {report_file}")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")
        
        return self.status == "HEALTHY"

def main():
    """Main function"""
    checker = HealthChecker()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        print("🔄 Running continuous health monitoring (Ctrl+C to stop)...")
        try:
            while True:
                checker.run_all_checks()
                print(f"\n⏰ Next check in 5 minutes...")
                time.sleep(300)  # Wait 5 minutes
        except KeyboardInterrupt:
            print("\n👋 Continuous monitoring stopped")
    else:
        success = checker.run_all_checks()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
