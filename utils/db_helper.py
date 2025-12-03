import pymysql
from datetime import datetime, timedelta
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseHelper:
    def __init__(self, config):
        self.config = config
        
    def get_connection(self):
        """Get database connection"""
        try:
            return pymysql.connect(**self.config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
            
    def validate_date_within_project(self, cursor, project_id, date_to_check):
        """Validate if a date falls within project start and end dates"""
        cursor.execute("""
            SELECT id, name, start_date, end_date 
            FROM projects 
            WHERE id = %s
        """, (project_id,))
        project = cursor.fetchone()
        
        if not project:
            return (False, None, None, None, "Project not found")
        
        project_id, project_name, project_start, project_end = project
        
        if not date_to_check:
            return (True, project_name, project_start, project_end, None)  # Allow null dates
            
        if not project_start or not project_end:
            return (True, project_name, project_start, project_end, None)  # Allow any date if project dates are not set
            
        date_to_check = datetime.strptime(date_to_check, '%Y-%m-%d').date() if isinstance(date_to_check, str) else date_to_check
        
        is_valid = project_start <= date_to_check <= project_end
        message = None if is_valid else f"Due date must be between {project_start.strftime('%Y-%m-%d')} and {project_end.strftime('%Y-%m-%d')}"
        
        return (is_valid, project_name, project_start, project_end, message)
    
    def init_database(self):
        """Initialize database and create tables"""
        try:
            # First connect without database to create it
            config_without_db = self.config.copy()
            db_name = config_without_db.pop('database')
            
            conn = pymysql.connect(**config_without_db)
            cursor = conn.cursor()
            
            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute(f"USE `{db_name}`")
            
            # Create tables
            self.create_tables(cursor)
            
            # Insert sample data
            self.insert_sample_data(cursor)
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise e
    
    def create_tables(self, cursor):
        """Create all required tables"""
        
        # Organizations table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """)
        
        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            organization_id INT NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            phone VARCHAR(20),
            role ENUM('admin', 'manager', 'member') DEFAULT 'member',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            avatar_url VARCHAR(512) NULL COMMENT 'Profile picture URL',
            FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
            INDEX idx_users_organization (organization_id),
            INDEX idx_users_role (role),
            INDEX idx_users_active (is_active),
            INDEX idx_users_email (email)
        )
        """)
        
        # Projects table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            organization_id INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            status ENUM('planning', 'active', 'completed', 'on_hold') DEFAULT 'planning',
            visibility ENUM('all', 'specific') DEFAULT 'all',
            start_date DATE,
            end_date DATE,
            created_by INT NOT NULL,
            assigned_manager_id INT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (assigned_manager_id) REFERENCES users(id) ON DELETE SET NULL,
            INDEX idx_projects_organization (organization_id),
            INDEX idx_projects_status (status),
            INDEX idx_projects_creator (created_by),
            INDEX idx_projects_manager (assigned_manager_id),
            INDEX idx_projects_dates (start_date, end_date)
        )
        """)
        
        # Milestones table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS milestones (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_id INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            due_date DATE,
            status ENUM('pending', 'in_progress', 'completed', 'overdue') DEFAULT 'pending',
            completion_date DATE NULL,
            created_by INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_milestones_project (project_id),
            INDEX idx_milestones_status (status),
            INDEX idx_milestones_due_date (due_date),
            INDEX idx_milestones_created_by (created_by)
        )
        """)
        
        # Tasks table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_id INT NOT NULL,
            milestone_id INT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status ENUM('pending', 'in_progress', 'completed') DEFAULT 'pending',
            priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
            assigned_to INT NULL,
            due_date DATE NULL,
            completion_date DATE NULL,
            created_by INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (milestone_id) REFERENCES milestones(id) ON DELETE SET NULL,
            FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_tasks_project (project_id),
            INDEX idx_tasks_milestone (milestone_id),
            INDEX idx_tasks_assignee (assigned_to),
            INDEX idx_tasks_status (status),
            INDEX idx_tasks_priority (priority),
            INDEX idx_tasks_due_date (due_date),
            INDEX idx_tasks_created_by (created_by)
        )
        """)
        
        # Messages table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender_id INT NOT NULL,
            recipient_id INT NOT NULL,
            project_id INT NULL,
            subject VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            read_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
            INDEX idx_messages_sender (sender_id),
            INDEX idx_messages_recipient (recipient_id),
            INDEX idx_messages_project (project_id),
            INDEX idx_messages_read (read_at),
            INDEX idx_messages_created (created_at)
        )
        """)
        
        # Task comments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            task_id INT NOT NULL,
            user_id INT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_task_comments_task (task_id),
            INDEX idx_task_comments_user (user_id),
            INDEX idx_task_comments_created (created_at)
        )
        """)
        
        # Project team members (many-to-many)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_members (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_id INT NOT NULL,
            user_id INT NOT NULL,
            role ENUM('manager', 'member') DEFAULT 'member',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_project_user (project_id, user_id),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_project_members_project (project_id),
            INDEX idx_project_members_user (user_id),
            INDEX idx_project_members_role (role)
        )
        """)

        # Project visibility table (for specific member visibility)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_visibility (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_id INT NOT NULL,
            user_id INT NOT NULL,
            UNIQUE KEY unique_project_user_visibility (project_id, user_id),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_project_visibility_project (project_id),
            INDEX idx_project_visibility_user (user_id)
        )
        """)
        
        # Notifications table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            task_id INT NULL,
            project_id INT NULL,
            type ENUM('task_due_soon', 'task_overdue', 'task_assigned', 'project_update', 'milestone_due') DEFAULT 'task_due_soon',
            title VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            days_until_due INT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            INDEX idx_notifications_user (user_id),
            INDEX idx_notifications_type (type),
            INDEX idx_notifications_read (is_read),
            INDEX idx_notifications_created (created_at)
        )
        """)
        
        # Daily reports table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_reports (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL COMMENT 'User who submitted the report',
            organization_id INT NOT NULL COMMENT 'Reference to organization',
            project_id INT COMMENT 'Reference to project (optional)',
            report_date DATE NOT NULL COMMENT 'Date of the report',
            work_title VARCHAR(255) NOT NULL COMMENT 'Title of work done',
            work_description TEXT COMMENT 'Detailed description of work',
            status ENUM('completed', 'in_progress', 'pending', 'blocked') DEFAULT 'completed' COMMENT 'Work status',
            discussion TEXT COMMENT 'Any discussions or notes',
            visible_to_manager BOOLEAN DEFAULT FALSE COMMENT 'Visible to managers',
            visible_to_admin BOOLEAN DEFAULT FALSE COMMENT 'Visible to admins',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            -- Foreign key constraints
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
            
            -- Indexes
            INDEX idx_daily_reports_user (user_id),
            INDEX idx_daily_reports_organization (organization_id),
            INDEX idx_daily_reports_project (project_id),
            INDEX idx_daily_reports_date (report_date),
            INDEX idx_daily_reports_manager (visible_to_manager),
            INDEX idx_daily_reports_admin (visible_to_admin)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
        COMMENT='Daily work reports submitted by users'
        """)
        
        # Daily report modules table (for structured reporting)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_report_modules (
            id INT AUTO_INCREMENT PRIMARY KEY,
            report_id INT NOT NULL,
            module_name VARCHAR(255) NOT NULL,
            total_hours DECIMAL(5,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES daily_reports(id) ON DELETE CASCADE,
            INDEX idx_daily_report_modules_report (report_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Daily report modules for structured reporting'
        """)
        
        # Daily report tasks table (for detailed task tracking)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_report_tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            report_id INT NOT NULL,
            module_id INT NULL,
            task_name VARCHAR(255) NOT NULL,
            task_hours DECIMAL(5,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES daily_reports(id) ON DELETE CASCADE,
            FOREIGN KEY (module_id) REFERENCES daily_report_modules(id) ON DELETE SET NULL,
            INDEX idx_daily_report_tasks_report (report_id),
            INDEX idx_daily_report_tasks_module (module_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Daily report tasks for detailed tracking'
        """)

        # Documents table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            organization_id INT NOT NULL,
            project_id INT NULL,
            uploaded_by INT NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            stored_name VARCHAR(255) NOT NULL,
            file_path VARCHAR(1024) NOT NULL,
            mime_type VARCHAR(255) NULL,
            file_size BIGINT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
            FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_documents_org (organization_id),
            INDEX idx_documents_project (project_id),
            INDEX idx_documents_user (uploaded_by),
            INDEX idx_documents_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Uploaded documents for projects and organization'
        """)
    
    def insert_sample_data(self, cursor):
        """Insert sample data if tables are empty"""
        import config
        
        # Only create demo data if explicitly enabled
        if not getattr(config, 'CREATE_DEMO_DATA', False):
            return
            
        import bcrypt
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM organizations")
        if cursor.fetchone()[0] > 0:
            return
        
        # Sample organizations - only insert columns that exist in the schema
        cursor.execute("""
        INSERT INTO organizations (name, description) VALUES 
        ('Demo Organization', 'Demo organization for Simple Project Manager')
        """)
        
        # Sample users - using bcrypt hashes for secure passwords
        # Passwords: admin, manager, member
        admin_hash = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        manager_hash = bcrypt.hashpw('manager'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        member_hash = bcrypt.hashpw('member'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
        INSERT INTO users (organization_id, full_name, email, password, role) VALUES
        (%s, 'Admin User', 'admin@demo.com', %s, 'admin'),
        (%s, 'Manager User', 'manager@demo.com', %s, 'manager'),
        (%s, 'Member User', 'member@demo.com', %s, 'member')
        """, (1, admin_hash, 1, manager_hash, 1, member_hash))
        
        # Sample projects
        cursor.execute("""
        INSERT INTO projects (organization_id, name, description, status, start_date, end_date, created_by) VALUES
        (1, 'E-Commerce Platform', 'Build a comprehensive e-commerce platform', 'active', '2025-01-01', '2025-06-30', 1),
        (1, 'Mobile App Development', 'Create mobile applications for iOS and Android', 'planning', '2025-02-01', '2025-08-31', 2)
        """)
        
        project_id = 1
        
        # Sample milestone
        cursor.execute("""
        INSERT INTO milestones (project_id, name, description, due_date, status, created_by) 
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (project_id, 'Design Phase', 'Complete UI/UX design', '2025-03-01', 'in_progress', 1))
        
        milestone_id = cursor.lastrowid
        
        # Sample tasks
        tasks_data = [
            (project_id, milestone_id, 'Create wireframes', 'Design initial wireframes for all pages', 'in_progress', 'high', 2, '2025-02-15', 1),
            (project_id, milestone_id, 'Design homepage', 'Create homepage design mockup', 'pending', 'medium', 3, '2025-02-20', 1),
            (project_id, None, 'Setup development environment', 'Configure development tools and environment', 'completed', 'low', 2, '2025-01-15', 1)
        ]
        
        for task_data in tasks_data:
            cursor.execute("""
            INSERT INTO tasks (project_id, milestone_id, title, description, status, priority, assigned_to, due_date, created_by) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, task_data)
        
        # Sample project members
        cursor.execute("""
        INSERT INTO project_members (project_id, user_id, role) 
        VALUES (%s, %s, %s), (%s, %s, %s)
        """, (project_id, 2, 'manager', project_id, 3, 'member'))
        
        # Sample message
        cursor.execute("""
        INSERT INTO messages (sender_id, recipient_id, project_id, subject, content) 
        VALUES (%s, %s, %s, %s, %s)
        """, (1, 2, project_id, 'Project Update', 'Please update the project status when you complete the wireframes.'))
    
    # User methods
    def authenticate_user(self, email, password_hash):
        """Authenticate user login"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT u.*, o.name as organization_name 
                FROM users u 
                JOIN organizations o ON u.organization_id = o.id 
                WHERE u.email = %s AND u.password = %s AND u.is_active = TRUE
            """, (email, password_hash))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT u.*, o.name as organization_name 
                FROM users u 
                JOIN organizations o ON u.organization_id = o.id 
                WHERE u.id = %s
            """, (user_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def get_user_by_email(self, email):
        """Get user by email"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT u.*, o.name as organization_name 
                FROM users u 
                JOIN organizations o ON u.organization_id = o.id 
                WHERE u.email = %s AND u.is_active = TRUE
            """, (email,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def create_user_with_organization(self, data):
        """Create new user with organization"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Check if email exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
            if cursor.fetchone():
                return None
            
            # Create organization
            cursor.execute("""
                INSERT INTO organizations (name, description) 
                VALUES (%s, %s)
            """, (data['organization_name'], f"Organization for {data['full_name']}"))
            
            org_id = cursor.lastrowid
            
            # Create user
            cursor.execute("""
                INSERT INTO users (organization_id, full_name, email, password, phone, role) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (org_id, data['full_name'], data['email'], data['password'], data['phone'], data['role']))
            
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating user: {e}")
            return None
        finally:
            conn.close()
    
    def get_organization_users(self, org_id):
        """Get all users in organization"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT id, full_name, email, phone, role, is_active, created_at 
                FROM users 
                WHERE organization_id = %s 
                ORDER BY full_name
            """, (org_id,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def create_user(self, data):
        """Create new user in existing organization"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Check if email exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
            if cursor.fetchone():
                return None
            
            # Create user
            cursor.execute("""
                INSERT INTO users (organization_id, full_name, email, password, phone, role) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (data['organization_id'], data['full_name'], data['email'], 
                  data['password'], data['phone'], data['role']))
            
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating user: {e}")
            return None
        finally:
            conn.close()
    
    def update_user(self, user_id, data):
        """Update user information"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Build update query based on provided data
            update_fields = []
            values = []
            
            if 'full_name' in data:
                update_fields.append("full_name = %s")
                values.append(data['full_name'])
            
            if 'email' in data:
                update_fields.append("email = %s")
                values.append(data['email'])
            
            if 'password' in data:
                update_fields.append("password = %s")
                values.append(data['password'])
            
            if 'phone' in data:
                update_fields.append("phone = %s")
                values.append(data['phone'])
            
            if 'role' in data:
                update_fields.append("role = %s")
                values.append(data['role'])
            
            if 'is_active' in data:
                update_fields.append("is_active = %s")
                values.append(data['is_active'])
            
            if not update_fields:
                return True  # No fields to update
            
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating user: {e}")
            return False
        finally:
            conn.close()
    
    def update_user_status(self, user_id, is_active):
        """Update user active status"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_active = %s WHERE id = %s", (is_active, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating user status: {e}")
            return False
        finally:
            conn.close()
    
    # Dashboard methods
    def get_dashboard_stats(self, org_id):
        """Get dashboard statistics"""
        conn = self.get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Projects count
            cursor.execute("SELECT COUNT(*) as total FROM projects WHERE organization_id = %s", (org_id,))
            projects_total = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as active FROM projects WHERE organization_id = %s AND status = 'active'", (org_id,))
            projects_active = cursor.fetchone()['active']
            
            # Tasks count
            cursor.execute("""
                SELECT COUNT(*) as total FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                WHERE p.organization_id = %s
            """, (org_id,))
            tasks_total = cursor.fetchone()['total']
            
            cursor.execute("""
                SELECT COUNT(*) as completed FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                WHERE p.organization_id = %s AND t.status = 'completed'
            """, (org_id,))
            tasks_completed = cursor.fetchone()['completed']
            
            # Users count
            cursor.execute("SELECT COUNT(*) as total FROM users WHERE organization_id = %s", (org_id,))
            users_total = cursor.fetchone()['total']
            
            # Overdue tasks
            cursor.execute("""
                SELECT COUNT(*) as overdue FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                WHERE p.organization_id = %s AND t.due_date < CURDATE() AND t.status != 'completed'
            """, (org_id,))
            overdue_tasks = cursor.fetchone()['overdue']
            
            return {
                'projects_total': projects_total,
                'projects_active': projects_active,
                'tasks_total': tasks_total,
                'tasks_completed': tasks_completed,
                'users_total': users_total,
                'overdue_tasks': overdue_tasks
            }
        finally:
            conn.close()
    
    def get_recent_projects(self, org_id, limit=5):
        """Get recent projects with task counts"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT p.*, u.full_name as created_by_name,
                COUNT(DISTINCT t.id) as task_count,
                COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks
                FROM projects p 
                JOIN users u ON p.created_by = u.id 
                LEFT JOIN tasks t ON p.id = t.project_id 
                WHERE p.organization_id = %s 
                GROUP BY p.id 
                ORDER BY p.created_at DESC 
                LIMIT %s
            """, (org_id, limit))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_user_recent_tasks(self, user_id, limit=10):
        """Get user's recent tasks"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT t.*, p.name as project_name 
                FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                WHERE t.assigned_to = %s 
                ORDER BY t.updated_at DESC 
                LIMIT %s
            """, (user_id, limit))
            tasks = cursor.fetchall()
            
            # Ensure date fields are properly handled
            for task in tasks:
                # Handle due_date
                if task.get('due_date'):
                    if isinstance(task['due_date'], str):
                        try:
                            task['due_date'] = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                task['due_date'] = datetime.strptime(task['due_date'], '%Y-%m-%d %H:%M:%S').date()
                            except ValueError:
                                pass  # Keep original value if conversion fails
                    elif isinstance(task['due_date'], datetime):
                        task['due_date'] = task['due_date'].date()
                        
                # Handle completion_date
                if task.get('completion_date'):
                    if isinstance(task['completion_date'], str):
                        try:
                            task['completion_date'] = datetime.strptime(task['completion_date'], '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                task['completion_date'] = datetime.strptime(task['completion_date'], '%Y-%m-%d %H:%M:%S').date()
                            except ValueError:
                                pass  # Keep original value if conversion fails
                    elif isinstance(task['completion_date'], datetime):
                        task['completion_date'] = task['completion_date'].date()
            
            return tasks
        finally:
            conn.close()
    
    def get_overdue_tasks(self, org_id, user_id=None):
        """Get overdue tasks for organization, optionally filtered by user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Base query with user filter option
            query = """
                SELECT t.*, p.name as project_name, u.full_name as assigned_to_name,
                       DATEDIFF(CURDATE(), t.due_date) as days_overdue,
                       u.role as assignee_role
                FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                LEFT JOIN users u ON t.assigned_to = u.id 
                WHERE p.organization_id = %s 
                AND t.due_date < CURDATE() 
                AND t.status != 'completed' 
            """
            
            params = [org_id]
            
            # Add user filter if specified
            if user_id:
                query += " AND t.assigned_to = %s "
                params.append(user_id)
            
            query += " ORDER BY t.due_date ASC, t.priority DESC"
            
            cursor.execute(query, params)
            tasks = cursor.fetchall()
            
            # Ensure date fields are properly handled
            for task in tasks:
                if task.get('due_date') and isinstance(task['due_date'], str):
                    try:
                        task['due_date'] = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass  # Keep original value if conversion fails
                        
                if task.get('completion_date') and isinstance(task['completion_date'], str):
                    try:
                        task['completion_date'] = datetime.strptime(task['completion_date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass  # Keep original value if conversion fails
            
            return tasks
        finally:
            conn.close()
    
    def get_overdue_tasks_by_user(self, org_id):
        """Get overdue tasks grouped by user for managers"""
        conn = self.get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT t.*, p.name as project_name, u.full_name as assigned_to_name,
                       DATEDIFF(CURDATE(), t.due_date) as days_overdue,
                       u.role as assignee_role, u.id as user_id
                FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                LEFT JOIN users u ON t.assigned_to = u.id 
                WHERE p.organization_id = %s 
                AND t.due_date < CURDATE() 
                AND t.status != 'completed' 
                AND t.assigned_to IS NOT NULL
                ORDER BY u.full_name ASC, t.due_date ASC, t.priority DESC
            """, (org_id,))
            tasks = cursor.fetchall()
            
            # Ensure date fields are properly handled
            for task in tasks:
                if task.get('due_date') and isinstance(task['due_date'], str):
                    try:
                        task['due_date'] = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass  # Keep original value if conversion fails
            
            # Group tasks by user
            tasks_by_user = {}
            for task in tasks:
                user_name = task.get('assigned_to_name', 'Unassigned')
                user_id = task.get('user_id')
                
                if user_name not in tasks_by_user:
                    tasks_by_user[user_name] = {
                        'user_id': user_id,
                        'user_name': user_name,
                        'user_role': task.get('assignee_role', 'member'),
                        'tasks': [],
                        'total_overdue': 0
                    }
                
                tasks_by_user[user_name]['tasks'].append(task)
                tasks_by_user[user_name]['total_overdue'] += 1
            
            return tasks_by_user
        finally:
            conn.close()
    
    def get_tasks_due_soon(self, org_id, days=7):
        """Get tasks that are due within specified days (default 7 days)"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT t.*, p.name as project_name, u.full_name as assigned_to_name,
                       DATEDIFF(t.due_date, CURDATE()) as days_until_due
                FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                LEFT JOIN users u ON t.assigned_to = u.id 
                WHERE p.organization_id = %s 
                AND t.due_date IS NOT NULL
                AND t.due_date >= CURDATE() 
                AND t.due_date <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
                AND t.status != 'completed' 
                ORDER BY t.due_date ASC
            """, (org_id, days))
            tasks = cursor.fetchall()
            
            # Ensure date fields are properly handled
            for task in tasks:
                if task.get('due_date') and isinstance(task['due_date'], str):
                    try:
                        task['due_date'] = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass  # Keep original value if conversion fails
                        
                if task.get('completion_date') and isinstance(task['completion_date'], str):
                    try:
                        task['completion_date'] = datetime.strptime(task['completion_date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass  # Keep original value if conversion fails
            
            return tasks
        finally:
            conn.close()
    
    # Project methods
    def get_organization_projects(self, org_id):
        """Get all projects for organization"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT p.*, u.full_name as created_by_name,
                COUNT(DISTINCT t.id) as task_count,
                COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks
                FROM projects p 
                JOIN users u ON p.created_by = u.id 
                LEFT JOIN tasks t ON p.id = t.project_id 
                WHERE p.organization_id = %s 
                GROUP BY p.id 
                ORDER BY p.created_at DESC
            """, (org_id,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_project_by_id(self, project_id):
        """Get project by ID"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT p.*, u.full_name as created_by_name 
                FROM projects p 
                JOIN users u ON p.created_by = u.id 
                WHERE p.id = %s
            """, (project_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def create_project(self, data):
        """Create new project"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (organization_id, name, description, start_date, end_date, created_by, assigned_manager_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (data['organization_id'], data['name'], data['description'], 
                  data['start_date'] or None, data['end_date'] or None, data['created_by'], 
                  data.get('assigned_manager_id') or None))
            
            project_id = cursor.lastrowid
            conn.commit()
            return project_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating project: {e}")
            return None
        finally:
            conn.close()
    
    def update_project(self, project_id, data):
        """Update project and handle auto-unassignment on completion"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Get current project status
            cursor.execute("SELECT status FROM projects WHERE id = %s", (project_id,))
            current_project = cursor.fetchone()
            current_status = current_project[0] if current_project else None
            
            # Update the project
            cursor.execute("""
                UPDATE projects 
                SET name = %s, description = %s, start_date = %s, end_date = %s, status = %s, assigned_manager_id = %s 
                WHERE id = %s
            """, (data['name'], data['description'], data['start_date'] or None, 
                  data['end_date'] or None, data['status'], data.get('assigned_manager_id') or None, project_id))
            
            # If project status changed to 'completed', auto-unassign team members
            if current_status != 'completed' and data['status'] == 'completed':
                self._auto_unassign_completed_project_members(cursor, project_id)
                logger.info(f"Auto-unassigned team members from completed project {project_id}")
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating project: {e}")
            return False
        finally:
            conn.close()
    
    def delete_project(self, project_id):
        """Delete project and all related data (cascading delete)"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Get project name for logging
            cursor.execute("SELECT name FROM projects WHERE id = %s", (project_id,))
            project = cursor.fetchone()
            project_name = project[0] if project else f"ID {project_id}"
            
            # Delete the project (CASCADE will handle related data)
            cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Project '{project_name}' (ID: {project_id}) deleted successfully")
                return True
            else:
                logger.warning(f"Project with ID {project_id} not found for deletion")
                return False
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting project: {e}")
            return False
        finally:
            conn.close()
    
    def get_project_tasks(self, project_id):
        """Get all tasks for project"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT t.*, 
                u1.full_name as assigned_to_name, 
                u2.full_name as created_by_name,
                m.name as milestone_name
                FROM tasks t 
                LEFT JOIN users u1 ON t.assigned_to = u1.id 
                JOIN users u2 ON t.created_by = u2.id 
                LEFT JOIN milestones m ON t.milestone_id = m.id 
                WHERE t.project_id = %s 
                ORDER BY t.created_at DESC
            """, (project_id,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_project_milestones(self, project_id):
        """Get all milestones for project"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT m.*, u.full_name as created_by_name,
                COUNT(t.id) as task_count,
                COUNT(CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks
                FROM milestones m 
                JOIN users u ON m.created_by = u.id 
                LEFT JOIN tasks t ON m.id = t.milestone_id 
                WHERE m.project_id = %s 
                GROUP BY m.id 
                ORDER BY m.due_date ASC
            """, (project_id,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_project_team_members(self, project_id):
        """Get project team members including project creator, assigned manager, and team members"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            # Get all team members including project creator, assigned manager, and users assigned to tasks
            cursor.execute("""
                SELECT DISTINCT u.id, u.full_name, u.email, u.role, 
                       CASE 
                           WHEN u.id = p.assigned_manager_id THEN 'Assigned Manager'
                           WHEN u.id = p.created_by THEN 'Project Creator'
                           WHEN pm.role IS NOT NULL THEN CONCAT(UPPER(SUBSTRING(pm.role, 1, 1)), LOWER(SUBSTRING(pm.role, 2)))
                           WHEN t.assigned_to IS NOT NULL THEN 'Team Member'
                           ELSE 'Team Member'
                       END as project_role,
                       COALESCE(pm.joined_at, p.created_at) as joined_at,
                       p.created_by as project_creator_id,
                       p.assigned_manager_id
                FROM projects p
                LEFT JOIN users u ON (u.id = p.created_by 
                                     OR u.id = p.assigned_manager_id
                                     OR u.id IN (SELECT pm2.user_id FROM project_members pm2 WHERE pm2.project_id = p.id)
                                     OR u.id IN (SELECT DISTINCT t2.assigned_to FROM tasks t2 WHERE t2.project_id = p.id AND t2.assigned_to IS NOT NULL))
                LEFT JOIN project_members pm ON pm.project_id = p.id AND pm.user_id = u.id
                LEFT JOIN tasks t ON t.project_id = p.id AND t.assigned_to = u.id
                WHERE p.id = %s AND u.id IS NOT NULL
                ORDER BY 
                    CASE 
                        WHEN u.id = p.assigned_manager_id THEN 1 
                        WHEN u.id = p.created_by THEN 2 
                        ELSE 3 
                    END,
                    u.full_name
            """, (project_id,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def add_user_to_project_team(self, cursor, project_id, user_id):
        """Add user to project team if not already added (using existing cursor)"""
        try:
            # Check if user is already in the project team
            cursor.execute("""
                SELECT id FROM project_members 
                WHERE project_id = %s AND user_id = %s
            """, (project_id, user_id))
            
            if not cursor.fetchone():
                # Add user to project team as member
                cursor.execute("""
                    INSERT INTO project_members (project_id, user_id, role) 
                    VALUES (%s, %s, 'member')
                """, (project_id, user_id))
                logger.info(f"Added user {user_id} to project {project_id} team")
        except Exception as e:
            logger.error(f"Error adding user to project team: {e}")
            # Don't raise the exception as this is a secondary operation
    
    # Task methods
    def get_user_tasks(self, user_id):
        """Get tasks assigned to user with role-based access control"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Get user role and organization
            cursor.execute("SELECT role, organization_id FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return []
            
            user_role = user['role']
            org_id = user['organization_id']
            
            if user_role == 'admin':
                # Admins can see all tasks assigned to them
                cursor.execute("""
                    SELECT t.*, p.name as project_name, m.name as milestone_name,
                           u_assigned.full_name as assigned_to_name, u_assigned.role as assigned_to_role,
                           u_assigned.email as assigned_to_email,
                           u_creator.full_name as created_by_name, u_creator.role as created_by_role
                    FROM tasks t 
                    JOIN projects p ON t.project_id = p.id 
                    LEFT JOIN milestones m ON t.milestone_id = m.id 
                    LEFT JOIN users u_assigned ON t.assigned_to = u_assigned.id
                    JOIN users u_creator ON t.created_by = u_creator.id
                    WHERE t.assigned_to = %s 
                    ORDER BY t.due_date ASC, t.priority DESC
                """, (user_id,))
            elif user_role == 'manager':
                # Managers can only see tasks from projects assigned to them
                cursor.execute("""
                    SELECT t.*, p.name as project_name, m.name as milestone_name,
                           u_assigned.full_name as assigned_to_name, u_assigned.role as assigned_to_role,
                           u_assigned.email as assigned_to_email,
                           u_creator.full_name as created_by_name, u_creator.role as created_by_role
                    FROM tasks t 
                    JOIN projects p ON t.project_id = p.id 
                    LEFT JOIN milestones m ON t.milestone_id = m.id 
                    LEFT JOIN users u_assigned ON t.assigned_to = u_assigned.id
                    JOIN users u_creator ON t.created_by = u_creator.id
                    WHERE t.assigned_to = %s 
                    AND p.assigned_manager_id = %s
                    ORDER BY t.due_date ASC, t.priority DESC
                """, (user_id, user_id))
            else:  # member
                # Members can only see tasks from projects they have access to
                cursor.execute("""
                    SELECT t.*, p.name as project_name, m.name as milestone_name,
                           u_assigned.full_name as assigned_to_name, u_assigned.role as assigned_to_role,
                           u_assigned.email as assigned_to_email,
                           u_creator.full_name as created_by_name, u_creator.role as created_by_role
                    FROM tasks t 
                    JOIN projects p ON t.project_id = p.id 
                    LEFT JOIN milestones m ON t.milestone_id = m.id 
                    LEFT JOIN users u_assigned ON t.assigned_to = u_assigned.id
                    JOIN users u_creator ON t.created_by = u_creator.id
                    LEFT JOIN project_visibility pv ON p.id = pv.project_id
                    WHERE t.assigned_to = %s 
                    AND p.organization_id = %s
                    AND (p.visibility = 'all' OR (p.visibility = 'specific' AND pv.user_id = %s))
                    ORDER BY t.due_date ASC, t.priority DESC
                """, (user_id, org_id, user_id))
            
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_tasks_by_creator_role(self, org_id, creator_role=None, user_id=None, user_role=None):
        """Get tasks in organization with role-based access control, optionally filtered by creator role"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            base_query = """
                SELECT t.*, p.name as project_name, m.name as milestone_name,
                       u_assigned.full_name as assigned_to_name, u_assigned.role as assigned_to_role,
                       u_assigned.email as assigned_to_email,
                       u_creator.full_name as created_by_name, u_creator.role as created_by_role
                FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                LEFT JOIN milestones m ON t.milestone_id = m.id 
                LEFT JOIN users u_assigned ON t.assigned_to = u_assigned.id
                JOIN users u_creator ON t.created_by = u_creator.id
            """
            
            # Build WHERE clause based on user role and access control
            where_conditions = ["p.organization_id = %s"]
            params = [org_id]
            
            # Add creator role filter if specified
            if creator_role:
                where_conditions.append("u_creator.role = %s")
                params.append(creator_role)
            
            # Apply role-based access control
            if user_role == 'admin':
                # Admins can see all tasks - no additional restrictions
                pass
            elif user_role == 'manager' and user_id:
                # Managers can only see tasks from projects assigned to them
                where_conditions.append("p.assigned_manager_id = %s")
                params.append(user_id)
            elif user_role == 'member' and user_id:
                # Members can only see tasks from projects they have access to
                base_query += " LEFT JOIN project_visibility pv ON p.id = pv.project_id"
                where_conditions.append("(p.visibility = 'all' OR (p.visibility = 'specific' AND pv.user_id = %s))")
                params.append(user_id)
            
            # Construct final query
            where_clause = " WHERE " + " AND ".join(where_conditions)
            order_clause = " ORDER BY t.created_at DESC, t.priority DESC"
            
            final_query = base_query + where_clause + order_clause
            
            cursor.execute(final_query, params)
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_task_by_id(self, task_id):
        """Get task by ID"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT t.*, 
                p.name as project_name,
                m.name as milestone_name,
                u1.full_name as assigned_to_name, u1.role as assigned_to_role, u1.email as assigned_to_email,
                u2.full_name as created_by_name, u2.role as created_by_role
                FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                LEFT JOIN milestones m ON t.milestone_id = m.id 
                LEFT JOIN users u1 ON t.assigned_to = u1.id 
                JOIN users u2 ON t.created_by = u2.id 
                WHERE t.id = %s
            """, (task_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def create_task(self, data):
        """Create new task"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Validate due date is within project dates
            is_valid, project_name, project_start, project_end, error_msg = self.validate_date_within_project(cursor, data['project_id'], data['due_date'])
            if not is_valid:
                raise ValueError(f"Due date must be within project '{project_name}' date range ({project_start.strftime('%Y-%m-%d')} to {project_end.strftime('%Y-%m-%d')})")
            
            cursor.execute("""
                INSERT INTO tasks (project_id, milestone_id, title, description, assigned_to, priority, due_date, created_by) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (data['project_id'], data['milestone_id'] or None, data['title'], 
                  data['description'], data['assigned_to'] or None, data['priority'], 
                  data['due_date'] or None, data['created_by']))
            
            task_id = cursor.lastrowid
            
            # Automatically add assigned user to project team if not already added
            if data['assigned_to']:
                self.add_user_to_project_team(cursor, data['project_id'], data['assigned_to'])
            
            conn.commit()
            return task_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating task: {e}")
            return None
        finally:
            conn.close()
    
    def update_task(self, task_id, data):
        """Update task with partial data"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Build update query based on provided data
            update_fields = []
            values = []
            
            if 'title' in data:
                update_fields.append("title = %s")
                values.append(data['title'])
            
            if 'description' in data:
                update_fields.append("description = %s")
                values.append(data['description'])
            
            if 'assigned_to' in data:
                update_fields.append("assigned_to = %s")
                values.append(data['assigned_to'] or None)
            
            if 'priority' in data:
                update_fields.append("priority = %s")
                values.append(data['priority'])
            
            if 'status' in data:
                update_fields.append("status = %s")
                values.append(data['status'])
                
                # Set completion date when task is marked as completed
                if data['status'] == 'completed':
                    update_fields.append("completion_date = CURDATE()")
                elif data['status'] in ['pending', 'in_progress']:
                    # Clear completion date if status is changed back from completed
                    update_fields.append("completion_date = NULL")
            
            if 'due_date' in data:
                update_fields.append("due_date = %s")
                values.append(data['due_date'] or None)
            
            if 'milestone_id' in data:
                update_fields.append("milestone_id = %s")
                values.append(data['milestone_id'] or None)
            
            if not update_fields:
                return True  # No fields to update
            
            # Add updated_at timestamp
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            values.append(task_id)
            query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = %s"
            
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating task: {e}")
            return False
        finally:
            conn.close()
    
    def get_task_comments(self, task_id):
        """Get task comments"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT tc.*, u.full_name as user_name 
                FROM task_comments tc 
                JOIN users u ON tc.user_id = u.id 
                WHERE tc.task_id = %s 
                ORDER BY tc.created_at ASC
            """, (task_id,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def create_task_comment(self, data):
        """Create new task comment"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_comments (task_id, user_id, content) 
                VALUES (%s, %s, %s)
            """, (data['task_id'], data['user_id'], data['content']))
            
            comment_id = cursor.lastrowid
            conn.commit()
            return comment_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating task comment: {e}")
            return None
        finally:
            conn.close()
    
    # Message methods
    def get_user_messages(self, user_id):
        """Get user messages"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT m.*, 
                u1.full_name as sender_name,
                u2.full_name as recipient_name,
                p.name as project_name
                FROM messages m 
                JOIN users u1 ON m.sender_id = u1.id 
                JOIN users u2 ON m.recipient_id = u2.id 
                LEFT JOIN projects p ON m.project_id = p.id 
                WHERE m.sender_id = %s OR m.recipient_id = %s 
                ORDER BY m.created_at DESC
            """, (user_id, user_id))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_message_by_id(self, message_id):
        """Get message by ID"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT m.*, 
                u1.full_name as sender_name,
                u2.full_name as recipient_name,
                p.name as project_name
                FROM messages m 
                JOIN users u1 ON m.sender_id = u1.id 
                JOIN users u2 ON m.recipient_id = u2.id 
                LEFT JOIN projects p ON m.project_id = p.id 
                WHERE m.id = %s
            """, (message_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def create_message(self, data):
        """Create new message"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (sender_id, recipient_id, project_id, subject, content) 
                VALUES (%s, %s, %s, %s, %s)
            """, (data['sender_id'], data['recipient_id'], data['project_id'] or None, 
                  data['subject'], data['content']))
            
            message_id = cursor.lastrowid
            conn.commit()
            return message_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating message: {e}")
            return None
        finally:
            conn.close()
    
    def mark_message_as_read(self, message_id):
        """Mark message as read"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE messages SET read_at = NOW() WHERE id = %s", (message_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error marking message as read: {e}")
            return False
        finally:
            conn.close()
    
    def get_unread_message_count(self, user_id):
        """Get count of unread messages for a user"""
        conn = self.get_connection()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM messages 
                WHERE recipient_id = %s AND read_at IS NULL
            """, (user_id,))
            
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            conn.close()
    
    # Milestone management methods
    def create_milestone(self, data):
        """Create new milestone"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Validate due date is within project dates
            is_valid, project_name, project_start, project_end, error_msg = self.validate_date_within_project(cursor, data['project_id'], data['due_date'])
            if not is_valid:
                raise ValueError(f"Due date must be within project '{project_name}' date range ({project_start.strftime('%Y-%m-%d')} to {project_end.strftime('%Y-%m-%d')})")
            
            cursor.execute("""
                INSERT INTO milestones (project_id, name, description, due_date, created_by) 
                VALUES (%s, %s, %s, %s, %s)
            """, (data['project_id'], data['name'], data['description'], 
                  data['due_date'] or None, data['created_by']))
            
            milestone_id = cursor.lastrowid
            conn.commit()
            return milestone_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating milestone: {e}")
            return None
        finally:
            conn.close()
    
    def update_milestone(self, milestone_id, data):
        """Update milestone"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE milestones 
                SET name = %s, description = %s, due_date = %s, status = %s 
                WHERE id = %s
            """, (data['name'], data['description'], data['due_date'] or None, 
                  data['status'], milestone_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating milestone: {e}")
            return False
        finally:
            conn.close()
    
    def assign_milestone_to_user(self, milestone_id, user_id, assigned_by):
        """Assign milestone to user by admin/manager"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            # Get milestone info
            cursor.execute("SELECT project_id FROM milestones WHERE id = %s", (milestone_id,))
            milestone = cursor.fetchone()
            if not milestone:
                return False
            
            # Assign all tasks in this milestone to the user
            cursor.execute("""
                UPDATE tasks 
                SET assigned_to = %s 
                WHERE milestone_id = %s AND assigned_to IS NULL
            """, (user_id, milestone_id))
            
            # Log milestone assignment in messages
            cursor.execute("""
                INSERT INTO messages (sender_id, recipient_id, project_id, subject, content) 
                VALUES (%s, %s, %s, %s, %s)
            """, (assigned_by, user_id, milestone[0], 'Milestone Assigned', 
                  f'You have been assigned to work on milestone tasks.'))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error assigning milestone: {e}")
            return False
        finally:
            conn.close()
    
    def get_milestone_by_id(self, milestone_id):
        """Get milestone by ID"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT m.*, p.name as project_name, u.full_name as created_by_name,
                COUNT(t.id) as task_count,
                COUNT(CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks
                FROM milestones m 
                JOIN projects p ON m.project_id = p.id
                JOIN users u ON m.created_by = u.id 
                LEFT JOIN tasks t ON m.id = t.milestone_id 
                WHERE m.id = %s 
                GROUP BY m.id
            """, (milestone_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    # Project visibility methods
    def update_project_visibility(self, project_id, data):
        """Update project visibility and specific members"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Update project visibility
            cursor.execute("""
                UPDATE projects 
                SET visibility = %s 
                WHERE id = %s
            """, (data['visibility'], project_id))
            
            # Clear existing visibility settings
            cursor.execute("DELETE FROM project_visibility WHERE project_id = %s", (project_id,))
            
            # If specific visibility, add selected members
            if data['visibility'] == 'specific' and 'member_ids' in data:
                for member_id in data['member_ids']:
                    cursor.execute("""
                        INSERT INTO project_visibility (project_id, user_id) 
                        VALUES (%s, %s)
                    """, (project_id, member_id))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating project visibility: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_visible_projects(self, user_id, org_id):
        """Get projects visible to user based on role and assignment"""
        conn = self.get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return []

            # Admin and managers can see all projects
            if user['role'] in ['admin', 'manager']:
                return self.get_organization_projects(org_id)

            # Members see only projects they are assigned to
            cursor.execute("""
                SELECT DISTINCT p.*, u.full_name as created_by_name,
                COUNT(DISTINCT t.id) as task_count,
                COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks
                FROM projects p
                JOIN users u ON p.created_by = u.id
                LEFT JOIN tasks t ON p.id = t.project_id
                JOIN project_members pm ON pm.project_id = p.id AND pm.user_id = %s
                WHERE p.organization_id = %s
                GROUP BY p.id
                ORDER BY p.created_at DESC
            """, (user_id, org_id))
            return cursor.fetchall()
        finally:
            conn.close()
    
    # Notification management methods
    def create_due_date_notifications(self, org_id, days_ahead=7):
        """Create notifications for tasks that are due soon"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Get tasks due in 1-7 days for users in the organization
            cursor.execute("""
                SELECT t.id, t.title, t.due_date, t.assigned_to, p.name as project_name, p.id as project_id,
                       DATEDIFF(t.due_date, CURDATE()) as days_until_due
                FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                WHERE p.organization_id = %s 
                AND t.assigned_to IS NOT NULL
                AND t.due_date IS NOT NULL
                AND t.due_date >= CURDATE() 
                AND t.due_date <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
                AND t.status != 'completed'
            """, (org_id, days_ahead))
            
            upcoming_tasks = cursor.fetchall()
            
            notifications_created = 0
            for task in upcoming_tasks:
                task_id, title, due_date, assigned_to, project_name, project_id, days_until_due = task
                
                # Check if notification already exists for this task and user for today
                cursor.execute("""
                    SELECT id FROM notifications 
                    WHERE user_id = %s AND task_id = %s AND type = 'task_due_soon'
                    AND DATE(created_at) = CURDATE()
                """, (assigned_to, task_id))
                
                if cursor.fetchone():
                    continue  # Notification already exists for today
                
                # Create notification message based on days until due
                if days_until_due == 0:
                    notification_title = f"Task Due Today: {title}"
                    notification_message = f"Your task '{title}' in project '{project_name}' is due today!"
                elif days_until_due == 1:
                    notification_title = f"Task Due Tomorrow: {title}"
                    notification_message = f"Your task '{title}' in project '{project_name}' is due tomorrow."
                else:
                    notification_title = f"Task Due in {days_until_due} Days: {title}"
                    notification_message = f"Your task '{title}' in project '{project_name}' is due in {days_until_due} days."
                
                # Insert notification
                cursor.execute("""
                    INSERT INTO notifications (user_id, task_id, project_id, type, title, message, days_until_due) 
                    VALUES (%s, %s, %s, 'task_due_soon', %s, %s, %s)
                """, (assigned_to, task_id, project_id, notification_title, notification_message, days_until_due))
                
                notifications_created += 1
            
            conn.commit()
            logger.info(f"Created {notifications_created} due date notifications for organization {org_id}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating due date notifications: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_notifications(self, user_id, limit=10, unread_only=False):
        """Get notifications for a user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            where_clause = "WHERE n.user_id = %s"
            params = [user_id]
            
            if unread_only:
                where_clause += " AND n.is_read = FALSE"
            
            cursor.execute(f"""
                SELECT n.*, t.title as task_title, p.name as project_name
                FROM notifications n
                LEFT JOIN tasks t ON n.task_id = t.id
                LEFT JOIN projects p ON n.project_id = p.id
                {where_clause}
                ORDER BY n.created_at DESC
                LIMIT %s
            """, params + [limit])
            
            return cursor.fetchall()
        finally:
            conn.close()
    
    def mark_notification_as_read(self, notification_id, user_id):
        """Mark a notification as read"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE notifications 
                SET is_read = TRUE 
                WHERE id = %s AND user_id = %s
            """, (notification_id, user_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error marking notification as read: {e}")
            return False
        finally:
            conn.close()
    
    def mark_all_notifications_as_read(self, user_id):
        """Mark all notifications as read for a user"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE notifications 
                SET is_read = TRUE 
                WHERE user_id = %s AND is_read = FALSE
            """, (user_id,))
            
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            logger.error(f"Error marking all notifications as read: {e}")
            return False
        finally:
            conn.close()
    
    def get_unread_notification_count(self, user_id):
        """Get count of unread notifications for a user"""
        conn = self.get_connection()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM notifications 
                WHERE user_id = %s AND is_read = FALSE
            """, (user_id,))
            
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            conn.close()
    
    def cleanup_old_notifications(self, days_old=30):
        """Remove old notifications to keep the table clean"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM notifications 
                WHERE created_at < DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """, (days_old,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Cleaned up {deleted_count} old notifications (older than {days_old} days)")
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error cleaning up old notifications: {e}")
            return False
        finally:
            conn.close()
    
    # Report generation methods
    def generate_project_report(self, project_id, start_date=None, end_date=None):
        """Generate comprehensive project report"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Project basic info
            cursor.execute("""
                SELECT p.*, u.full_name as created_by_name 
                FROM projects p 
                JOIN users u ON p.created_by = u.id 
                WHERE p.id = %s
            """, (project_id,))
            project = cursor.fetchone()
            
            if not project:
                return None
            
            # Tasks summary
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_tasks,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks,
                    COUNT(CASE WHEN due_date < CURDATE() AND status != 'completed' THEN 1 END) as overdue_tasks
                FROM tasks 
                WHERE project_id = %s
            """, (project_id,))
            task_stats = cursor.fetchone()
            
            # Team members performance
            cursor.execute("""
                SELECT u.full_name, u.email,
                    COUNT(t.id) as assigned_tasks,
                    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
                    COUNT(CASE WHEN t.due_date < CURDATE() AND t.status != 'completed' THEN 1 END) as overdue_tasks
                FROM users u
                LEFT JOIN tasks t ON u.id = t.assigned_to AND t.project_id = %s
                JOIN project_members pm ON u.id = pm.user_id AND pm.project_id = %s
                GROUP BY u.id, u.full_name, u.email
                ORDER BY assigned_tasks DESC
            """, (project_id, project_id))
            team_performance = cursor.fetchall()
            
            # Milestones progress
            cursor.execute("""
                SELECT m.name, m.due_date, m.status,
                    COUNT(t.id) as milestone_tasks,
                    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks
                FROM milestones m
                LEFT JOIN tasks t ON m.id = t.milestone_id
                WHERE m.project_id = %s
                GROUP BY m.id, m.name, m.due_date, m.status
                ORDER BY m.due_date
            """, (project_id,))
            milestones_progress = cursor.fetchall()
            
            # Time-based task completion (if date range provided)
            date_filter = ""
            date_params = [project_id]
            if start_date and end_date:
                date_filter = "AND t.completion_date BETWEEN %s AND %s"
                date_params.extend([start_date, end_date])
            
            cursor.execute(f"""
                SELECT DATE(t.completion_date) as completion_date, COUNT(*) as tasks_completed
                FROM tasks t
                WHERE t.project_id = %s AND t.status = 'completed' AND t.completion_date IS NOT NULL {date_filter}
                GROUP BY DATE(t.completion_date)
                ORDER BY completion_date
            """, date_params)
            daily_completions = cursor.fetchall()
            
            return {
                'project': project,
                'task_stats': task_stats,
                'team_performance': team_performance,
                'milestones_progress': milestones_progress,
                'daily_completions': daily_completions,
                'generated_at': datetime.now()
            }
            
        finally:
            conn.close()
    
    def generate_user_report(self, user_id, start_date=None, end_date=None):
        """Generate user performance report"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # User info
            cursor.execute("""
                SELECT u.*, o.name as organization_name 
                FROM users u 
                JOIN organizations o ON u.organization_id = o.id 
                WHERE u.id = %s
            """, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return None
            
            # Task statistics
            date_filter = ""
            date_params = [user_id]
            if start_date and end_date:
                date_filter = "AND t.created_at BETWEEN %s AND %s"
                date_params.extend([start_date, end_date])
            
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_assigned,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_tasks,
                    COUNT(CASE WHEN due_date < CURDATE() AND status != 'completed' THEN 1 END) as overdue_tasks,
                    AVG(CASE WHEN status = 'completed' AND completion_date IS NOT NULL AND due_date IS NOT NULL 
                            THEN DATEDIFF(completion_date, due_date) END) as avg_delay_days
                FROM tasks t
                WHERE t.assigned_to = %s {date_filter}
            """, date_params)
            task_stats = cursor.fetchone()
            
            # Project involvement
            cursor.execute(f"""
                SELECT p.name, p.status,
                    COUNT(t.id) as assigned_tasks,
                    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks
                FROM projects p
                JOIN tasks t ON p.id = t.project_id
                WHERE t.assigned_to = %s {date_filter}
                GROUP BY p.id, p.name, p.status
                ORDER BY assigned_tasks DESC
            """, date_params)
            project_involvement = cursor.fetchall()
            
            return {
                'user': user,
                'task_stats': task_stats,
                'project_involvement': project_involvement,
                'generated_at': datetime.now()
            }
            
        finally:
            conn.close()
    
    def get_available_team_members(self, org_id, project_id=None):
        """Get available team members (users with role 'member') for assignment with current project assignments"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            if project_id:
                # Get members not already assigned to this project, with their current project assignments
                cursor.execute("""
                    SELECT u.id, u.full_name, u.email, u.role,
                           GROUP_CONCAT(DISTINCT CONCAT(p.name, ' (', p.status, ')') SEPARATOR ', ') as current_projects
                    FROM users u
                    LEFT JOIN project_members pm_current ON u.id = pm_current.user_id
                    LEFT JOIN projects p ON pm_current.project_id = p.id AND p.status IN ('active', 'planning')
                    WHERE u.organization_id = %s 
                    AND u.is_active = TRUE
                    AND u.role = 'member'
                    AND u.id NOT IN (
                        SELECT pm.user_id FROM project_members pm WHERE pm.project_id = %s
                    )
                    GROUP BY u.id, u.full_name, u.email, u.role
                    ORDER BY u.full_name
                """, (org_id, project_id))
            else:
                # Get all active members in organization with their current project assignments
                cursor.execute("""
                    SELECT u.id, u.full_name, u.email, u.role,
                           GROUP_CONCAT(DISTINCT CONCAT(p.name, ' (', p.status, ')') SEPARATOR ', ') as current_projects
                    FROM users u
                    LEFT JOIN project_members pm ON u.id = pm.user_id
                    LEFT JOIN projects p ON pm.project_id = p.id AND p.status IN ('active', 'planning')
                    WHERE u.organization_id = %s 
                    AND u.is_active = TRUE
                    AND u.role = 'member'
                    GROUP BY u.id, u.full_name, u.email, u.role
                    ORDER BY u.full_name
                """, (org_id,))
            
            return cursor.fetchall()
        finally:
            conn.close()
    
    def assign_team_members_to_project(self, project_id, member_ids, assigned_by):
        """Assign multiple team members to a project"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # First, remove existing team members (except manager and creator)
            cursor.execute("""
                DELETE FROM project_members 
                WHERE project_id = %s AND role = 'member'
            """, (project_id,))
            
            # Add new team members
            success_count = 0
            for member_id in member_ids:
                try:
                    cursor.execute("""
                        INSERT INTO project_members (project_id, user_id, role) 
                        VALUES (%s, %s, 'member')
                        ON DUPLICATE KEY UPDATE role = 'member'
                    """, (project_id, member_id))
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error assigning member {member_id} to project {project_id}: {e}")
                    continue
            
            conn.commit()
            logger.info(f"Successfully assigned {success_count} team members to project {project_id}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error assigning team members to project: {e}")
            return False
        finally:
            conn.close()
    
    def remove_team_member_from_project(self, project_id, member_id):
        """Remove a team member from a project"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Remove the team member
            cursor.execute("""
                DELETE FROM project_members 
                WHERE project_id = %s AND user_id = %s AND role = 'member'
            """, (project_id, member_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            
            if success:
                logger.info(f"Successfully removed team member {member_id} from project {project_id}")
            
            return success
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error removing team member from project: {e}")
            return False
        finally:
            conn.close()
    
    def _auto_unassign_completed_project_members(self, cursor, project_id):
        """Auto-unassign team members from completed project (using existing cursor)"""
        try:
            # Get project info for logging
            cursor.execute("SELECT name FROM projects WHERE id = %s", (project_id,))
            project = cursor.fetchone()
            project_name = project[0] if project else f"ID {project_id}"
            
            # Get list of members to be unassigned for logging
            cursor.execute("""
                SELECT u.full_name FROM project_members pm
                JOIN users u ON pm.user_id = u.id
                WHERE pm.project_id = %s AND pm.role = 'member'
            """, (project_id,))
            members_to_unassign = cursor.fetchall()
            
            # Remove team members (but keep manager assignment)
            cursor.execute("""
                DELETE FROM project_members 
                WHERE project_id = %s AND role = 'member'
            """, (project_id,))
            
            unassigned_count = cursor.rowcount
            
            if unassigned_count > 0:
                member_names = [member[0] for member in members_to_unassign]
                logger.info(f"Auto-unassigned {unassigned_count} team members from completed project '{project_name}': {', '.join(member_names)}")
            
        except Exception as e:
            logger.error(f"Error in auto-unassigning team members: {e}")
            # Don't raise the exception as this is a secondary operation
    
    def get_user_project_assignments(self, user_id):
        """Get all active project assignments for a user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT p.id, p.name, p.status, p.start_date, p.end_date,
                       pm.role as project_role, pm.joined_at,
                       u_creator.full_name as created_by_name
                FROM project_members pm
                JOIN projects p ON pm.project_id = p.id
                JOIN users u_creator ON p.created_by = u_creator.id
                WHERE pm.user_id = %s
                ORDER BY 
                    CASE WHEN p.status = 'active' THEN 1 
                         WHEN p.status = 'planning' THEN 2
                         WHEN p.status = 'on_hold' THEN 3
                         ELSE 4 END,
                    p.name
            """, (user_id,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_project_assigned_members(self, project_id):
        """Get only the assigned team members for a project (not including manager/creator)"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT u.id, u.full_name, u.email, u.role, pm.joined_at
                FROM project_members pm
                JOIN users u ON pm.user_id = u.id
                WHERE pm.project_id = %s AND pm.role = 'member'
                ORDER BY u.full_name
            """, (project_id,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_project_assignable_members(self, project_id, current_user_role):
        """Get all users who can be assigned tasks in a project (team members + manager + admins if allowed)"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Base query (admins only included if allowed)
            query = """
                SELECT u.id, u.full_name, u.email, u.role,
                       CASE 
                           WHEN u.id = p.assigned_manager_id THEN 'Project Manager'
                           WHEN pm.user_id IS NOT NULL THEN 'Team Member'
                           WHEN u.role = 'admin' THEN 'Administrator'
                           ELSE 'Other'
                       END as project_role,
                       p.assigned_manager_id
                FROM projects p
                LEFT JOIN users u ON (u.id = p.assigned_manager_id 
                                     OR u.id IN (SELECT pm2.user_id FROM project_members pm2 WHERE pm2.project_id = p.id)
                                     {admin_condition})
                LEFT JOIN project_members pm ON pm.project_id = p.id AND pm.user_id = u.id
                WHERE p.id = %s 
                AND u.id IS NOT NULL 
                AND u.is_active = TRUE
                AND p.organization_id = u.organization_id
                GROUP BY u.id, u.full_name, u.email, u.role, p.assigned_manager_id
                ORDER BY 
                    CASE 
                        WHEN u.role = 'admin' THEN 1
                        WHEN u.id = p.assigned_manager_id THEN 2 
                        ELSE 3 
                    END,
                    u.full_name
            """

            # Manager should NOT see admins
            if current_user_role == "manager":
                admin_condition = ""
            else:
                admin_condition = "OR u.role = 'admin'"

            final_query = query.format(admin_condition=admin_condition)
            cursor.execute(final_query, (project_id,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_organization_report(self, org_id, start_date=None, end_date=None):
        """Generate organization-wide report"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Organization info
            cursor.execute("SELECT * FROM organizations WHERE id = %s", (org_id,))
            organization = cursor.fetchone()
            
            # Overall statistics
            date_filter = ""
            date_params = [org_id]
            if start_date and end_date:
                date_filter = "AND t.created_at BETWEEN %s AND %s"
                date_params.extend([start_date, end_date])
            
            cursor.execute(f"""
                SELECT 
                    COUNT(DISTINCT p.id) as total_projects,
                    COUNT(DISTINCT CASE WHEN p.status = 'active' THEN p.id END) as active_projects,
                    COUNT(DISTINCT CASE WHEN p.status = 'completed' THEN p.id END) as completed_projects,
                    COUNT(t.id) as total_tasks,
                    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
                    COUNT(DISTINCT u.id) as total_users
                FROM projects p
                LEFT JOIN tasks t ON p.id = t.project_id {date_filter.replace('t.created_at', 't.created_at')}
                LEFT JOIN users u ON p.organization_id = u.organization_id
                WHERE p.organization_id = %s
            """, date_params)
            overall_stats = cursor.fetchone()
            
            # Top performing users
            cursor.execute(f"""
                SELECT u.full_name, u.role,
                    COUNT(t.id) as assigned_tasks,
                    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
                    COUNT(CASE WHEN t.due_date < CURDATE() AND t.status != 'completed' THEN 1 END) as overdue_tasks
                FROM users u
                LEFT JOIN tasks t ON u.id = t.assigned_to
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE u.organization_id = %s {date_filter.replace('t.created_at', 't.created_at')}
                GROUP BY u.id, u.full_name, u.role
                HAVING COUNT(t.id) > 0
                ORDER BY completed_tasks DESC, overdue_tasks ASC
                LIMIT 10
            """, date_params)
            top_performers = cursor.fetchall()
            
            return {
                'organization': organization,
                'overall_stats': overall_stats,
                'top_performers': top_performers,
                'generated_at': datetime.now()
            }
            
        finally:
            conn.close()

    # Documents methods
    # Updated Documents methods to match your database table schema

    def create_document_record(self, organization_id, project_id, uploaded_by, original_name, stored_name, file_path, mime_type, file_size):
        """Create a document record with enhanced fields to match database schema"""
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            
            # Get file extension from original name
            file_extension = os.path.splitext(original_name)[1].lower() if original_name else ''
            
            cursor.execute(
                """
                INSERT INTO documents (
                    organization_id, project_id, title, description, filename, 
                    file_path, file_size, file_type, file_extension, uploaded_by,
                    is_active, version, download_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    organization_id, 
                    project_id or None, 
                    original_name,  # Use original name as title
                    None,  # description - can be added later
                    stored_name,  # filename field stores the actual stored filename
                    file_path, 
                    file_size, 
                    mime_type,  # file_type field
                    file_extension, 
                    uploaded_by,
                    1,  # is_active = true
                    1,  # version = 1 (initial version)
                    0   # download_count = 0
                ),
            )
            doc_id = cursor.lastrowid
            conn.commit()
            return doc_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating document record: {e}")
            return None
        finally:
            conn.close()

    def create_document_record_enhanced(self, data):
        """Create document record with all optional fields"""
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO documents (
                    organization_id, project_id, title, description, filename,
                    file_path, file_size, file_type, file_extension, uploaded_by,
                    tags, version, is_active, download_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data['organization_id'], data.get('project_id'), data['title'],
                    data.get('description'), data['filename'], data['file_path'],
                    data['file_size'], data['file_type'], data['file_extension'],
                    data['uploaded_by'], data.get('tags'), data.get('version', 1),
                    data.get('is_active', True), data.get('download_count', 0)
                )
            )
            doc_id = cursor.lastrowid
            conn.commit()
            return doc_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating enhanced document record: {e}")
            return None
        finally:
            conn.close()

    def get_documents_for_user(self, user_id, org_id, role):
        """List documents based on role with enhanced access control"""
        conn = self.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            if role == 'admin':
                # Admin sees all active organization documents
                cursor.execute(
                    """
                    SELECT d.*, u.full_name AS uploaded_by_name, p.name AS project_name
                    FROM documents d
                    JOIN users u ON d.uploaded_by = u.id
                    LEFT JOIN projects p ON d.project_id = p.id
                    WHERE d.organization_id = %s AND d.is_active = 1
                    ORDER BY d.created_at DESC
                    """,
                    (org_id,),
                )
            elif role == 'manager':
                # Manager sees documents from their assigned projects + their own uploads
                cursor.execute(
                    """
                    SELECT DISTINCT d.*, u.full_name AS uploaded_by_name, p.name AS project_name
                    FROM documents d
                    JOIN users u ON d.uploaded_by = u.id
                    LEFT JOIN projects p ON d.project_id = p.id
                    WHERE d.organization_id = %s AND d.is_active = 1
                    AND (p.assigned_manager_id = %s OR d.uploaded_by = %s OR d.project_id IS NULL)
                    ORDER BY d.created_at DESC
                    """,
                    (org_id, user_id, user_id),
                )
            else:
                # Members see their own uploads + documents from projects they're assigned to
                cursor.execute(
                    """
                    SELECT DISTINCT d.*, u.full_name AS uploaded_by_name, p.name AS project_name
                    FROM documents d
                    JOIN users u ON d.uploaded_by = u.id
                    LEFT JOIN projects p ON d.project_id = p.id
                    LEFT JOIN project_members pa ON p.id = pa.project_id
                    WHERE d.organization_id = %s AND d.is_active = 1
                    AND (d.uploaded_by = %s OR pa.user_id = %s OR d.project_id IS NULL)
                    ORDER BY d.created_at DESC
                    """,
                    (org_id, user_id, user_id),
                )
            
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting documents for user: {e}")
            return []
        finally:
            conn.close()

    def get_document_by_id(self, doc_id):
        """Get document details by id"""
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(
                """
                SELECT d.*, u.full_name AS uploaded_by_name, p.name AS project_name
                FROM documents d
                JOIN users u ON d.uploaded_by = u.id
                LEFT JOIN projects p ON d.project_id = p.id
                WHERE d.id = %s AND d.is_active = 1
                """,
                (doc_id,),
            )
            return cursor.fetchone()
        finally:
            conn.close()

    def can_user_view_document(self, user_id, org_id, role, document):
        """Enhanced RBAC for document viewing"""
        if not document or document.get('organization_id') != org_id or not document.get('is_active', True):
            return False
        
        if role == 'admin':
            return True
        
        # Users can always view their own uploads
        if document.get('uploaded_by') == user_id:
            return True
        
        # For project-associated documents
        if document.get('project_id'):
            if role == 'manager':
                # Manager can view documents from their assigned projects
                project = self.get_project_by_id(document['project_id'])
                if project and project.get('assigned_manager_id') == user_id:
                    return True
            elif role == 'member':
                # Member can view documents from projects they're assigned to
                return self.is_user_assigned_to_project(user_id, document['project_id'])
        
        # Documents not associated with projects are visible to all org members
        if not document.get('project_id'):
            return True
        
        return False

    def can_user_manage_document(self, user_id, org_id, role, document):
        """Enhanced RBAC for document management (delete, edit)"""
        if not document or document.get('organization_id') != org_id or not document.get('is_active', True):
            return False
        
        # Admin can manage all documents
        if role == 'admin':
            return True
        
        # Users can always manage their own uploads
        if document.get('uploaded_by') == user_id:
            return True
        
        # For project-associated documents
        if document.get('project_id'):
            if role == 'manager':
                # Manager can manage documents from their assigned projects
                project = self.get_project_by_id(document['project_id'])
                if project and project.get('assigned_manager_id') == user_id:
                    return True
        
        # Members cannot manage documents (only view)
        return False

    def delete_document(self, doc_id):
        """Soft delete document (set is_active to 0) instead of hard delete"""
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE documents SET is_active = 0 WHERE id = %s", (doc_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting document record: {e}")
            return False
        finally:
            conn.close()

    def increment_download_count(self, doc_id):
        """Increment download count and update last downloaded timestamp"""
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE documents 
                SET download_count = download_count + 1, 
                    last_downloaded_at = CURRENT_TIMESTAMP
                WHERE id = %s AND is_active = 1
                """,
                (doc_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating download count: {e}")
            return False
        finally:
            conn.close()

    def is_user_assigned_to_project(self, user_id, project_id):
        """Check if user is assigned to a project"""
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 1 FROM project_assignments 
                WHERE user_id = %s AND project_id = %s
                """,
                (user_id, project_id)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking project assignment: {e}")
            return False
        finally:
            conn.close()
    
    # Manager-specific Dashboard Methods
    def get_manager_dashboard_stats(self, manager_id, org_id):
        """Get dashboard statistics for manager (only their assigned projects)"""
        conn = self.get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Projects count - only manager's assigned projects
            cursor.execute("SELECT COUNT(*) as total FROM projects WHERE organization_id = %s AND assigned_manager_id = %s", (org_id, manager_id))
            projects_total = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as active FROM projects WHERE organization_id = %s AND assigned_manager_id = %s AND status = 'active'", (org_id, manager_id))
            projects_active = cursor.fetchone()['active']
            
            cursor.execute("SELECT COUNT(*) as completed FROM projects WHERE organization_id = %s AND assigned_manager_id = %s AND status = 'completed'", (org_id, manager_id))
            projects_completed = cursor.fetchone()['completed']
            
            # Tasks count - only from manager's projects
            cursor.execute("""
                SELECT COUNT(*) as total FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                WHERE p.organization_id = %s AND p.assigned_manager_id = %s
            """, (org_id, manager_id))
            tasks_total = cursor.fetchone()['total']
            
            cursor.execute("""
                SELECT COUNT(*) as completed FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                WHERE p.organization_id = %s AND p.assigned_manager_id = %s AND t.status = 'completed'
            """, (org_id, manager_id))
            tasks_completed = cursor.fetchone()['completed']
            
            # Users count - team members working on manager's projects
            cursor.execute("""
                SELECT COUNT(DISTINCT t.assigned_to) as total FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                WHERE p.organization_id = %s AND p.assigned_manager_id = %s AND t.assigned_to IS NOT NULL
            """, (org_id, manager_id))
            users_total = cursor.fetchone()['total']
            
            # Overdue tasks - only from manager's projects
            cursor.execute("""
                SELECT COUNT(*) as overdue FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                WHERE p.organization_id = %s AND p.assigned_manager_id = %s AND t.due_date < CURDATE() AND t.status != 'completed'
            """, (org_id, manager_id))
            overdue_tasks = cursor.fetchone()['overdue']
            
            return {
                'projects_total': projects_total,
                'projects_active': projects_active,
                'projects_completed': projects_completed,
                'tasks_total': tasks_total,
                'tasks_completed': tasks_completed,
                'users_total': users_total,
                'overdue_tasks': overdue_tasks
            }
        finally:
            conn.close()
    
    def get_manager_overdue_tasks(self, manager_id, org_id):
        """Get overdue tasks from manager's assigned projects"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT t.*, p.name as project_name, u.full_name as assigned_to_name,
                       DATEDIFF(CURDATE(), t.due_date) as days_overdue,
                       u.role as assignee_role
                FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                LEFT JOIN users u ON t.assigned_to = u.id 
                WHERE p.organization_id = %s 
                AND p.assigned_manager_id = %s
                AND t.due_date < CURDATE() 
                AND t.status != 'completed' 
                ORDER BY t.due_date ASC, t.priority DESC
            """, (org_id, manager_id))
            tasks = cursor.fetchall()
            
            # Ensure date fields are properly handled
            for task in tasks:
                if task.get('due_date') and isinstance(task['due_date'], str):
                    try:
                        task['due_date'] = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass  # Keep original value if conversion fails
                        
                if task.get('completion_date') and isinstance(task['completion_date'], str):
                    try:
                        task['completion_date'] = datetime.strptime(task['completion_date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass  # Keep original value if conversion fails
            
            return tasks
        finally:
            conn.close()
    
    def get_manager_overdue_tasks_by_user(self, manager_id, org_id):
        """Get overdue tasks grouped by user for manager's assigned projects"""
        conn = self.get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT t.*, p.name as project_name, u.full_name as assigned_to_name,
                       DATEDIFF(CURDATE(), t.due_date) as days_overdue,
                       u.role as assignee_role, u.id as user_id
                FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                LEFT JOIN users u ON t.assigned_to = u.id 
                WHERE p.organization_id = %s 
                AND p.assigned_manager_id = %s
                AND t.due_date < CURDATE() 
                AND t.status != 'completed' 
                AND t.assigned_to IS NOT NULL
                ORDER BY u.full_name ASC, t.due_date ASC, t.priority DESC
            """, (org_id, manager_id))
            tasks = cursor.fetchall()
            
            # Ensure date fields are properly handled
            for task in tasks:
                if task.get('due_date') and isinstance(task['due_date'], str):
                    try:
                        task['due_date'] = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass  # Keep original value if conversion fails
            
            # Group tasks by user
            tasks_by_user = {}
            for task in tasks:
                user_name = task.get('assigned_to_name', 'Unassigned')
                user_id = task.get('user_id')
                
                if user_name not in tasks_by_user:
                    tasks_by_user[user_name] = {
                        'user_id': user_id,
                        'user_name': user_name,
                        'user_role': task.get('assignee_role', 'member'),
                        'tasks': [],
                        'total_overdue': 0
                    }
                
                tasks_by_user[user_name]['tasks'].append(task)
                tasks_by_user[user_name]['total_overdue'] += 1
            
            return tasks_by_user
        finally:
            conn.close()
    
    def get_manager_tasks_due_soon(self, manager_id, org_id, days=7):
        """Get tasks due soon from manager's assigned projects"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT t.*, p.name as project_name, u.full_name as assigned_to_name,
                       DATEDIFF(t.due_date, CURDATE()) as days_until_due
                FROM tasks t 
                JOIN projects p ON t.project_id = p.id 
                LEFT JOIN users u ON t.assigned_to = u.id 
                WHERE p.organization_id = %s 
                AND p.assigned_manager_id = %s
                AND t.due_date IS NOT NULL
                AND t.due_date >= CURDATE() 
                AND t.due_date <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
                AND t.status != 'completed' 
                ORDER BY t.due_date ASC
            """, (org_id, manager_id, days))
            tasks = cursor.fetchall()
            
            # Ensure date fields are properly handled
            for task in tasks:
                if task.get('due_date') and isinstance(task['due_date'], str):
                    try:
                        task['due_date'] = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass  # Keep original value if conversion fails
                        
                if task.get('completion_date') and isinstance(task['completion_date'], str):
                    try:
                        task['completion_date'] = datetime.strptime(task['completion_date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass  # Keep original value if conversion fails
            
            return tasks
        finally:
            conn.close()
    
    # Project Manager Assignment Methods
    def get_manager_assigned_projects(self, manager_id, org_id):
        """Get projects assigned to a specific manager"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT p.*, u_creator.full_name as created_by_name, u_manager.full_name as assigned_manager_name,
                COUNT(DISTINCT t.id) as task_count,
                COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks
                FROM projects p 
                JOIN users u_creator ON p.created_by = u_creator.id 
                LEFT JOIN users u_manager ON p.assigned_manager_id = u_manager.id
                LEFT JOIN tasks t ON p.id = t.project_id 
                WHERE p.organization_id = %s AND p.assigned_manager_id = %s
                GROUP BY p.id 
                ORDER BY p.created_at DESC
            """, (org_id, manager_id))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def assign_project_to_manager(self, project_id, manager_id):
        """Assign a project to a manager"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE projects 
                SET assigned_manager_id = %s 
                WHERE id = %s
            """, (manager_id, project_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error assigning project to manager: {e}")
            return False
        finally:
            conn.close()
    
    def get_available_managers(self, org_id):
        """Get all managers in organization for assignment"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT id, full_name, email 
                FROM users 
                WHERE organization_id = %s AND role = 'manager' AND is_active = TRUE
                ORDER BY full_name
            """, (org_id,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_projects_with_manager_info(self, org_id):
        """Get all organization projects with manager assignment info"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT p.*, u_creator.full_name as created_by_name, 
                       u_manager.full_name as assigned_manager_name, u_manager.id as assigned_manager_id,
                COUNT(DISTINCT t.id) as task_count,
                COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks
                FROM projects p 
                JOIN users u_creator ON p.created_by = u_creator.id 
                LEFT JOIN users u_manager ON p.assigned_manager_id = u_manager.id
                LEFT JOIN tasks t ON p.id = t.project_id 
                WHERE p.organization_id = %s 
                GROUP BY p.id 
                ORDER BY p.created_at DESC
            """, (org_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    # Daily Report Methods
    def create_daily_report(self, data):
        """Create new daily report"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_reports (user_id, organization_id, project_id, report_date, work_title, 
                                         work_description, status, discussion, visible_to_manager, visible_to_admin) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (data['user_id'], data['organization_id'], data.get('project_id'), data['report_date'], data['work_title'],
                  data['work_description'], data['status'], data['discussion'], 
                  data['visible_to_manager'], data['visible_to_admin']))
            
            report_id = cursor.lastrowid
            conn.commit()
            return report_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating daily report: {e}")
            return None
        finally:
            conn.close()
    
    def get_daily_reports_for_user(self, user_id, org_id):
        """Get daily reports submitted by a specific user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT dr.*, u.full_name as user_name, p.name as project_name
                FROM daily_reports dr
                JOIN users u ON dr.user_id = u.id
                LEFT JOIN projects p ON dr.project_id = p.id
                WHERE dr.user_id = %s AND dr.organization_id = %s
                ORDER BY dr.report_date DESC, dr.created_at DESC
            """, (user_id, org_id))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_daily_reports_for_managers(self, org_id):
        """Get daily reports visible to managers and project team members"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT dr.*, u.full_name as user_name, p.name as project_name
                FROM daily_reports dr
                JOIN users u ON dr.user_id = u.id
                LEFT JOIN projects p ON dr.project_id = p.id
                WHERE dr.organization_id = %s AND dr.visible_to_manager = TRUE
                ORDER BY dr.report_date DESC, dr.created_at DESC
            """, (org_id,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_daily_reports_for_admins(self, org_id):
        """Get daily reports visible to admins"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT dr.*, u.full_name as user_name, p.name as project_name
                FROM daily_reports dr
                JOIN users u ON dr.user_id = u.id
                LEFT JOIN projects p ON dr.project_id = p.id
                WHERE dr.organization_id = %s AND dr.visible_to_admin = TRUE
                ORDER BY dr.report_date DESC, dr.created_at DESC
            """, (org_id,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_daily_reports_by_date_range(self, org_id, start_date, end_date, user_role):
        """Get daily reports within a date range based on user role"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            if user_role == 'admin':
                # Admins can see all reports visible to them
                cursor.execute("""
                    SELECT dr.*, u.full_name as user_name, p.name as project_name
                    FROM daily_reports dr
                    JOIN users u ON dr.user_id = u.id
                    LEFT JOIN projects p ON dr.project_id = p.id
                    WHERE dr.organization_id = %s AND dr.visible_to_admin = TRUE 
                          AND dr.report_date BETWEEN %s AND %s
                    ORDER BY dr.report_date DESC, dr.created_at DESC
                """, (org_id, start_date, end_date))
            elif user_role == 'manager':
                # Managers can see reports visible to them
                cursor.execute("""
                    SELECT dr.*, u.full_name as user_name, p.name as project_name
                    FROM daily_reports dr
                    JOIN users u ON dr.user_id = u.id
                    LEFT JOIN projects p ON dr.project_id = p.id
                    WHERE dr.organization_id = %s AND dr.visible_to_manager = TRUE 
                          AND dr.report_date BETWEEN %s AND %s
                    ORDER BY dr.report_date DESC, dr.created_at DESC
                """, (org_id, start_date, end_date))
            else:
                # Regular members can only see their own reports
                return []
            
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_user_projects(self, user_id, org_id):
        """Get projects that a user is assigned to or can access"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT DISTINCT p.id, p.name, p.description, p.status
                FROM projects p
                LEFT JOIN project_members pm ON p.id = pm.project_id
                WHERE p.organization_id = %s 
                  AND (pm.user_id = %s OR p.created_by = %s OR p.assigned_manager_id = %s)
                ORDER BY p.name
            """, (org_id, user_id, user_id, user_id))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_daily_report_by_id(self, report_id, user_id, org_id, user_role):
        """Get a specific daily report by ID with access control including project-based access"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Base query
            query = """
                SELECT dr.*, u.full_name as user_name, p.name as project_name
                FROM daily_reports dr
                JOIN users u ON dr.user_id = u.id
                LEFT JOIN projects p ON dr.project_id = p.id
                LEFT JOIN project_members pm ON dr.project_id = pm.project_id
                WHERE dr.id = %s AND dr.organization_id = %s
            """
            params = [report_id, org_id]
            
            # Access control conditions
            access_conditions = [
                "dr.user_id = %s"  # Submitter always has access
            ]
            params.append(user_id)
            
            if user_role == 'admin':
                access_conditions.append("dr.visible_to_admin = TRUE")
            elif user_role == 'manager':
                # Manager access: only from projects they manage or are team members of
                access_conditions.append("""
                    dr.project_id IS NULL 
                    OR p.assigned_manager_id = %s 
                    OR pm.user_id = %s
                """)
                params.extend([user_id, user_id])
            elif user_role == 'member':
                # Member access: visible to manager AND team member
                access_conditions.append("""
                    dr.visible_to_manager = TRUE AND (
                        dr.project_id IS NULL 
                        OR pm.user_id = %s
                    )
                """)
                params.append(user_id)
            
            query += " AND (" + " OR ".join(access_conditions) + ")"
            
            cursor.execute(query, tuple(params))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def get_daily_reports_for_user_role(self, user_id, org_id, user_role):
        """Get daily reports based on user role and project access"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            if user_role == 'admin':
                # Admins can see all reports visible to them
                cursor.execute("""
                    SELECT dr.*, u.full_name as user_name, p.name as project_name
                    FROM daily_reports dr
                    JOIN users u ON dr.user_id = u.id
                    LEFT JOIN projects p ON dr.project_id = p.id
                    WHERE dr.organization_id = %s AND dr.visible_to_admin = TRUE
                    ORDER BY dr.report_date DESC, dr.created_at DESC
                """, (org_id,))
            elif user_role == 'manager':
                # Managers can only see reports from projects they manage or are team members of
                cursor.execute("""
                    SELECT DISTINCT dr.*, u.full_name as user_name, p.name as project_name
                    FROM daily_reports dr
                    JOIN users u ON dr.user_id = u.id
                    LEFT JOIN projects p ON dr.project_id = p.id
                    LEFT JOIN project_members pm ON dr.project_id = pm.project_id AND pm.user_id = %s
                    WHERE dr.organization_id = %s 
                      AND (dr.project_id IS NULL 
                           OR p.assigned_manager_id = %s 
                           OR pm.user_id IS NOT NULL)
                    ORDER BY dr.report_date DESC, dr.created_at DESC
                """, (user_id, org_id, user_id))
            else:
                # Regular members can see their own reports, plus reports from projects they're assigned to
                cursor.execute("""
                    SELECT DISTINCT dr.*, u.full_name as user_name, p.name as project_name
                    FROM daily_reports dr
                    JOIN users u ON dr.user_id = u.id
                    LEFT JOIN projects p ON dr.project_id = p.id
                    LEFT JOIN project_members pm ON dr.project_id = pm.project_id
                    WHERE dr.organization_id = %s 
                      AND (dr.user_id = %s 
                           OR (dr.visible_to_manager = TRUE AND dr.project_id IS NOT NULL AND pm.user_id = %s))
                    ORDER BY dr.report_date DESC, dr.created_at DESC
                """, (org_id, user_id, user_id))
            
            return cursor.fetchall()
        finally:
            conn.close()

    def update_user_profile(self, user_id, first_name, last_name, email, phone):
        """Update user profile information"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Update user profile
            cursor.execute("""
                UPDATE users 
                SET full_name = %s, email = %s, phone = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (f"{first_name} {last_name}", email, phone, user_id))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_user_password(self, user_id, password_hash):
        """Update user password"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Update user password
            cursor.execute("""
                UPDATE users 
                SET password = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (password_hash, user_id))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user password: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_user_avatar(self, user_id, avatar_url):
        """Update user's avatar URL"""
        conn = self.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            # Add column if missing (safe-guard)
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(512) NULL")
            except Exception:
                pass
            cursor.execute("""
                UPDATE users
                SET avatar_url = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (avatar_url, user_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user avatar: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_daily_report_with_modules(self, report_id, user_id, org_id, user_role):
        """Get a specific daily report with its modules and tasks"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Get the main report
            cursor.execute("""
                SELECT dr.*, u.full_name as user_name, p.name as project_name
                FROM daily_reports dr
                JOIN users u ON dr.user_id = u.id
                LEFT JOIN projects p ON dr.project_id = p.id
                WHERE dr.id = %s AND dr.organization_id = %s
            """, (report_id, org_id))
            
            report = cursor.fetchone()
            if not report:
                return None
            
            # Check access permissions based on user role
            if user_role == 'member' and report['user_id'] != user_id:
                return None
            elif user_role == 'manager' and not report['visible_to_manager'] and report['user_id'] != user_id:
                return None
            elif user_role == 'admin' and not report['visible_to_admin'] and not report['visible_to_manager'] and report['user_id'] != user_id:
                return None
            
            # Get modules for this report
            cursor.execute("""
                SELECT * FROM daily_report_modules 
                WHERE report_id = %s 
                ORDER BY id
            """, (report_id,))
            
            modules = cursor.fetchall()
            
            # Get tasks for each module
            for module in modules:
                cursor.execute("""
                    SELECT * FROM daily_report_tasks 
                    WHERE module_id = %s 
                    ORDER BY id
                """, (module['id'],))
                
                module['tasks'] = cursor.fetchall()
            
            report['modules'] = modules
            return report
            
        finally:
            conn.close()

    def get_daily_reports_with_module_counts(self, user_id, org_id, user_role):
        """Get daily reports with module counts for list view"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            if user_role == 'admin':
                # Admins can see all reports visible to them
                cursor.execute("""
                    SELECT dr.*, u.full_name as user_name, p.name as project_name,
                           (SELECT COUNT(*) FROM daily_report_modules WHERE report_id = dr.id) as module_count
                    FROM daily_reports dr
                    JOIN users u ON dr.user_id = u.id
                    LEFT JOIN projects p ON dr.project_id = p.id
                    WHERE dr.organization_id = %s AND dr.visible_to_admin = TRUE
                    ORDER BY dr.report_date DESC, dr.created_at DESC
                """, (org_id,))
            elif user_role == 'manager':
                # Managers can see reports from their projects or visible to managers
                cursor.execute("""
                    SELECT dr.*, u.full_name as user_name, p.name as project_name,
                           (SELECT COUNT(*) FROM daily_report_modules WHERE report_id = dr.id) as module_count
                    FROM daily_reports dr
                    JOIN users u ON dr.user_id = u.id
                    LEFT JOIN projects p ON dr.project_id = p.id
                    WHERE dr.organization_id = %s AND (
                        dr.visible_to_manager = TRUE OR
                        dr.user_id = %s OR
                        p.id IN (SELECT pm.project_id FROM project_members pm WHERE pm.user_id = %s)
                    )
                    ORDER BY dr.report_date DESC, dr.created_at DESC
                """, (org_id, user_id, user_id))
            else:
                # Members can only see their own reports
                cursor.execute("""
                    SELECT dr.*, u.full_name as user_name, p.name as project_name,
                           (SELECT COUNT(*) FROM daily_report_modules WHERE report_id = dr.id) as module_count
                    FROM daily_reports dr
                    JOIN users u ON dr.user_id = u.id
                    LEFT JOIN projects p ON dr.project_id = p.id
                    WHERE dr.user_id = %s AND dr.organization_id = %s
                    ORDER BY dr.report_date DESC, dr.created_at DESC
                """, (user_id, org_id))
            
            return cursor.fetchall()
        finally:
            conn.close()