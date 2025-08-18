# PowerShell Deployment Script for Simple Project Manager
# Usage: .\deploy.ps1 [-Environment prod|staging] [-SkipBackup] [-Force]

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("prod", "staging", "dev")]
    [string]$Environment = "prod",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBackup = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false
)

# Configuration
$AppName = "Simple Project Manager"
$BackupDir = "backups"
$LogDir = "logs"
$DeploymentLog = "$LogDir\deployment_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Colors for output
$ErrorColor = "Red"
$WarningColor = "Yellow" 
$SuccessColor = "Green"
$InfoColor = "Cyan"

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Create logs directory if it doesn't exist
    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    }
    
    # Write to log file
    Add-Content -Path $DeploymentLog -Value $logMessage
    
    # Write to console with color
    switch ($Level) {
        "ERROR"   { Write-Host $logMessage -ForegroundColor $ErrorColor }
        "WARNING" { Write-Host $logMessage -ForegroundColor $WarningColor }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor $SuccessColor }
        "INFO"    { Write-Host $logMessage -ForegroundColor $InfoColor }
        default   { Write-Host $logMessage }
    }
}

# Check prerequisites
function Test-Prerequisites {
    Write-Log "Checking deployment prerequisites..." "INFO"
    
    # Check if Python is installed
    try {
        $pythonVersion = python --version 2>$null
        Write-Log "Python version: $pythonVersion" "SUCCESS"
    } catch {
        Write-Log "Python is not installed or not in PATH" "ERROR"
        return $false
    }
    
    # Check if virtual environment exists
    if (-not (Test-Path "venv")) {
        Write-Log "Virtual environment not found. Run setup.bat first." "ERROR"
        return $false
    }
    
    # Check if .env file exists
    if (-not (Test-Path ".env")) {
        Write-Log ".env file not found. Please configure environment variables." "ERROR"
        return $false
    }
    
    Write-Log "Prerequisites check passed" "SUCCESS"
    return $true
}

# Create database backup
function Backup-Database {
    if ($SkipBackup) {
        Write-Log "Skipping database backup as requested" "WARNING"
        return $true
    }
    
    Write-Log "Creating database backup..." "INFO"
    
    # Create backup directory
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    }
    
    # Activate virtual environment and run backup
    try {
        & "venv\Scripts\Activate.ps1"
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupFile = "$BackupDir\backup_$timestamp.sql"
        
        # Run Python backup script
        python -c @"
import subprocess, config
db_config = config.DB_CONFIG
cmd = [
    'mysqldump',
    '-h', db_config['host'],
    '-u', db_config['user'], 
    f'-p{db_config["password"]}',
    db_config['database']
]
with open('$backupFile', 'w') as f:
    result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        print('Backup created successfully')
    else:
        print(f'Backup failed: {result.stderr}')
        exit(1)
"@
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Database backup created: $backupFile" "SUCCESS"
            return $true
        } else {
            Write-Log "Database backup failed" "ERROR"
            return $false
        }
    } catch {
        Write-Log "Error creating database backup: $_" "ERROR"
        return $false
    }
}

# Update application
function Update-Application {
    Write-Log "Updating application..." "INFO"
    
    try {
        # Activate virtual environment
        & "venv\Scripts\Activate.ps1"
        
        # Update dependencies
        Write-Log "Installing/updating dependencies..." "INFO"
        pip install -r requirements.txt --upgrade
        
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Failed to update dependencies" "ERROR"
            return $false
        }
        
        # Run database migrations if needed
        Write-Log "Running database initialization..." "INFO"
        python -c @"
from utils.db_helper import DatabaseHelper
import config
try:
    db = DatabaseHelper(config.DB_CONFIG)
    db.init_database()
    print('Database initialization completed')
except Exception as e:
    print(f'Database initialization failed: {e}')
    exit(1)
"@
        
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Database initialization failed" "ERROR"
            return $false
        }
        
        Write-Log "Application updated successfully" "SUCCESS"
        return $true
        
    } catch {
        Write-Log "Error updating application: $_" "ERROR"
        return $false
    }
}

# Run health checks
function Test-ApplicationHealth {
    Write-Log "Running post-deployment health checks..." "INFO"
    
    try {
        & "venv\Scripts\Activate.ps1"
        pip show requests >$null 2>&1
        if ($LASTEXITCODE -ne 0) {
            pip install requests
        }
        
        python health_check.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Health checks passed" "SUCCESS"
            return $true
        } else {
            Write-Log "Health checks failed" "WARNING"
            return $false
        }
    } catch {
        Write-Log "Error running health checks: $_" "ERROR"
        return $false
    }
}

# Set environment configuration
function Set-EnvironmentConfig {
    Write-Log "Configuring environment: $Environment" "INFO"
    
    # Set environment variables based on deployment target
    switch ($Environment) {
        "prod" {
            $env:FLASK_ENV = "production"
            $env:DEBUG = "False"
            Write-Log "Production environment configured" "SUCCESS"
        }
        "staging" {
            $env:FLASK_ENV = "staging"
            $env:DEBUG = "False"
            Write-Log "Staging environment configured" "SUCCESS"
        }
        "dev" {
            $env:FLASK_ENV = "development"
            $env:DEBUG = "True"
            Write-Log "Development environment configured" "SUCCESS"
        }
    }
}

# Main deployment process
function Start-Deployment {
    Write-Log "========================================" "INFO"
    Write-Log "Starting deployment of $AppName" "INFO"
    Write-Log "Environment: $Environment" "INFO"
    Write-Log "Timestamp: $(Get-Date)" "INFO"
    Write-Log "========================================" "INFO"
    
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        Write-Log "Prerequisites check failed. Aborting deployment." "ERROR"
        exit 1
    }
    
    # Confirm production deployment
    if ($Environment -eq "prod" -and -not $Force) {
        Write-Log "PRODUCTION DEPLOYMENT - This will affect live users!" "WARNING"
        $confirmation = Read-Host "Are you sure you want to continue? (yes/no)"
        if ($confirmation -ne "yes") {
            Write-Log "Deployment cancelled by user" "INFO"
            exit 0
        }
    }
    
    # Create backup
    if (-not (Backup-Database)) {
        Write-Log "Database backup failed. Aborting deployment." "ERROR"
        exit 1
    }
    
    # Update application
    if (-not (Update-Application)) {
        Write-Log "Application update failed. Check logs for details." "ERROR"
        exit 1
    }
    
    # Set environment configuration
    Set-EnvironmentConfig
    
    # Run health checks
    Test-ApplicationHealth
    
    Write-Log "========================================" "INFO"
    Write-Log "Deployment completed successfully!" "SUCCESS"
    Write-Log "Environment: $Environment" "INFO"
    Write-Log "Log file: $DeploymentLog" "INFO"
    Write-Log "========================================" "INFO"
    
    # Show next steps
    Write-Log "Next steps:" "INFO"
    Write-Log "1. Start the application: .\start.bat" "INFO"
    Write-Log "2. Verify application is running: http://localhost:5000" "INFO"
    Write-Log "3. Run health check: .\health.bat" "INFO"
}

# Run deployment
try {
    Start-Deployment
} catch {
    Write-Log "Deployment failed with error: $_" "ERROR"
    Write-Log "Check the log file for details: $DeploymentLog" "ERROR"
    exit 1
}
