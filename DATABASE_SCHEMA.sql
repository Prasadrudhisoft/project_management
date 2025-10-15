-- =====================================================
-- Project Manager - Complete Database Schema
-- =====================================================
-- Version: 3.1 (with Advanced Team Management Features)
-- Compatible with: MySQL 8.0+ / MariaDB 10.3+
-- Character Set: utf8mb4 (full Unicode support)
-- Created: 2025-08-12
-- Last Updated: 2025-08-14
--
-- NEW FEATURES IN v3.1:
-- - Team assignments overview functionality
-- - Auto-unassignment on project completion
-- - Enhanced team member management
-- - Improved project workflow management
-- =====================================================

-- Set database defaults
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS `project_management_app` 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `project_management_app`;

-- =====================================================
-- 1. ORGANIZATIONS TABLE
-- =====================================================
DROP TABLE IF EXISTS `organizations`;
CREATE TABLE `organizations` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL COMMENT 'Organization name',
    `description` TEXT COMMENT 'Organization description',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX `idx_organizations_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Organizations table';

-- =====================================================
-- 2. USERS TABLE
-- =====================================================
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `organization_id` INT NOT NULL COMMENT 'Reference to organization',
    `full_name` VARCHAR(255) NOT NULL COMMENT 'User full name',
    `email` VARCHAR(255) NOT NULL COMMENT 'User email (unique)',
    `password` VARCHAR(255) NOT NULL COMMENT 'Password hash (bcrypt/SHA256)',
    `phone` VARCHAR(20) COMMENT 'User phone number',
    `role` ENUM('admin', 'manager', 'member') DEFAULT 'member' COMMENT 'User role',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT 'User account status',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `avatar_url` VARCHAR(512) NULL COMMENT 'Profile picture URL',
    
    -- Foreign key constraints
    CONSTRAINT `fk_users_organization` FOREIGN KEY (`organization_id`) 
        REFERENCES `organizations`(`id`) ON DELETE CASCADE,
    
    -- Unique constraints
    UNIQUE KEY `uk_users_email` (`email`),
    
    -- Indexes
    INDEX `idx_users_organization` (`organization_id`),
    INDEX `idx_users_role` (`role`),
    INDEX `idx_users_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Users table with role-based access';

-- =====================================================
-- 3. PROJECTS TABLE
-- =====================================================
DROP TABLE IF EXISTS `projects`;
CREATE TABLE projects (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    organization_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status ENUM('planning', 'active', 'completed', 'on_hold') DEFAULT 'planning',
    start_date DATE,
    end_date DATE,
    created_by INT NOT NULL,
    assigned_manager_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    visibility ENUM('all', 'specific') DEFAULT 'all',
    INDEX (organization_id),
    INDEX (status),
    INDEX (created_by),
    INDEX (assigned_manager_id),
    INDEX (visibility),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_manager_id) REFERENCES users(id) ON DELETE SET NULL
);

-- =====================================================
-- 4. PROJECT VISIBILITY TABLE
-- =====================================================
DROP TABLE IF EXISTS `project_visibility`;
CREATE TABLE `project_visibility` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `project_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    
    CONSTRAINT `fk_project_visibility_project` FOREIGN KEY (`project_id`) 
        REFERENCES `projects`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_project_visibility_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users`(`id`) ON DELETE CASCADE,
        
    UNIQUE KEY `uk_project_visibility` (`project_id`, `user_id`),
    INDEX `idx_project_visibility_project` (`project_id`),
    INDEX `idx_project_visibility_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Project visibility permissions';

-- =====================================================
-- 5. PROJECT MEMBERS TABLE
-- =====================================================
DROP TABLE IF EXISTS `project_members`;
CREATE TABLE `project_members` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `project_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `role` ENUM('manager', 'member') DEFAULT 'member' COMMENT 'Project role',
    `joined_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT `fk_project_members_project` FOREIGN KEY (`project_id`) 
        REFERENCES `projects`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_project_members_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users`(`id`) ON DELETE CASCADE,
        
    -- Unique constraint
    UNIQUE KEY `uk_project_members` (`project_id`, `user_id`),
    
    -- Indexes
    INDEX `idx_project_members_project` (`project_id`),
    INDEX `idx_project_members_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Project team members';

-- =====================================================
-- 6. MILESTONES TABLE
-- =====================================================
DROP TABLE IF EXISTS `milestones`;
CREATE TABLE `milestones` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `project_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL COMMENT 'Milestone name',
    `description` TEXT COMMENT 'Milestone description',
    `status` ENUM('pending', 'in_progress', 'completed', 'overdue') DEFAULT 'pending' COMMENT 'Milestone status',
    `due_date` DATE COMMENT 'Milestone due date',
    `completion_date` DATE COMMENT 'Actual completion date',
    `created_by` INT NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT `fk_milestones_project` FOREIGN KEY (`project_id`) 
        REFERENCES `projects`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_milestones_creator` FOREIGN KEY (`created_by`) 
        REFERENCES `users`(`id`) ON DELETE RESTRICT,
        
    -- Indexes
    INDEX `idx_milestones_project` (`project_id`),
    INDEX `idx_milestones_status` (`status`),
    INDEX `idx_milestones_due_date` (`due_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Project milestones';

-- =====================================================
-- 7. TASKS TABLE
-- =====================================================
DROP TABLE IF EXISTS `tasks`;
CREATE TABLE `tasks` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `project_id` INT NOT NULL,
    `milestone_id` INT COMMENT 'Associated milestone',
    `title` VARCHAR(255) NOT NULL COMMENT 'Task title',
    `description` TEXT COMMENT 'Task description',
    `status` ENUM('pending', 'in_progress', 'completed') DEFAULT 'pending' COMMENT 'Task status',
    `priority` ENUM('low', 'medium', 'high') DEFAULT 'medium' COMMENT 'Task priority',
    `assigned_to` INT COMMENT 'Assigned user',
    `due_date` DATE COMMENT 'Task due date',
    `completion_date` DATE COMMENT 'Actual completion date',
    `created_by` INT NOT NULL COMMENT 'Task creator',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT `fk_tasks_project` FOREIGN KEY (`project_id`) 
        REFERENCES `projects`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_tasks_milestone` FOREIGN KEY (`milestone_id`) 
        REFERENCES `milestones`(`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_tasks_assignee` FOREIGN KEY (`assigned_to`) 
        REFERENCES `users`(`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_tasks_creator` FOREIGN KEY (`created_by`) 
        REFERENCES `users`(`id`) ON DELETE RESTRICT,
        
    -- Indexes
    INDEX `idx_tasks_project` (`project_id`),
    INDEX `idx_tasks_milestone` (`milestone_id`),
    INDEX `idx_tasks_assignee` (`assigned_to`),
    INDEX `idx_tasks_status` (`status`),
    INDEX `idx_tasks_priority` (`priority`),
    INDEX `idx_tasks_due_date` (`due_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Project tasks';

-- =====================================================
-- 8. TASK COMMENTS TABLE
-- =====================================================
DROP TABLE IF EXISTS `task_comments`;
CREATE TABLE task_comments (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (task_id),
    INDEX (user_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- =====================================================
-- 9. DAILY REPORTS TABLE
-- =====================================================
DROP TABLE IF EXISTS `daily_reports`;
CREATE TABLE `daily_reports` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL COMMENT 'User who submitted the report',
    `organization_id` INT NOT NULL COMMENT 'Reference to organization',
    `project_id` INT COMMENT 'Reference to project (optional)',
    `report_date` DATE NOT NULL COMMENT 'Date of the report',
    `work_title` VARCHAR(255) NOT NULL COMMENT 'Title of work done',
    `work_description` TEXT COMMENT 'Detailed description of work',
    `status` ENUM('completed', 'in_progress', 'pending', 'blocked') DEFAULT 'completed' COMMENT 'Work status',
    `discussion` TEXT COMMENT 'Any discussions or notes',
    `visible_to_manager` BOOLEAN DEFAULT FALSE COMMENT 'Visible to managers',
    `visible_to_admin` BOOLEAN DEFAULT FALSE COMMENT 'Visible to admins',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT `fk_daily_reports_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_daily_reports_organization` FOREIGN KEY (`organization_id`) 
        REFERENCES `organizations`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_daily_reports_project` FOREIGN KEY (`project_id`) 
        REFERENCES `projects`(`id`) ON DELETE SET NULL,
        
    -- Indexes
    INDEX `idx_daily_reports_user` (`user_id`),
    INDEX `idx_daily_reports_organization` (`organization_id`),
    INDEX `idx_daily_reports_project` (`project_id`),
    INDEX `idx_daily_reports_date` (`report_date`),
    INDEX `idx_daily_reports_manager` (`visible_to_manager`),
    INDEX `idx_daily_reports_admin` (`visible_to_admin`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Daily work reports submitted by users';

-- =====================================================


-- =====================================================
-- 9. MESSAGES TABLE
-- =====================================================
DROP TABLE IF EXISTS `messages`;
CREATE TABLE `messages` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `sender_id` INT NOT NULL,
    `recipient_id` INT NOT NULL,
    `project_id` INT COMMENT 'Associated project',
    `subject` VARCHAR(255) NOT NULL COMMENT 'Message subject',
    `content` TEXT NOT NULL COMMENT 'Message content',
    `read_at` TIMESTAMP NULL COMMENT 'When message was read',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT `fk_messages_sender` FOREIGN KEY (`sender_id`) 
        REFERENCES `users`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_messages_recipient` FOREIGN KEY (`recipient_id`) 
        REFERENCES `users`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_messages_project` FOREIGN KEY (`project_id`) 
        REFERENCES `projects`(`id`) ON DELETE SET NULL,
    
    -- Indexes
    INDEX `idx_messages_sender` (`sender_id`),
    INDEX `idx_messages_recipient` (`recipient_id`),
    INDEX `idx_messages_project` (`project_id`),
    INDEX `idx_messages_read` (`read_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Internal messaging system';

-- =====================================================
-- 10. NOTIFICATIONS TABLE
-- =====================================================
DROP TABLE IF EXISTS `notifications`;
CREATE TABLE notifications (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    task_id INT,
    project_id INT,
    type ENUM('task_due_soon', 'task_overdue', 'task_assigned', 'project_update', 'milestone_due') DEFAULT 'task_due_soon',
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    days_until_due INT,
    is_read TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (user_id),
    INDEX (task_id),
    INDEX (project_id),
    INDEX (type),
    INDEX (is_read),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);


-- Create structured daily report tables if they don't exist
CREATE TABLE IF NOT EXISTS `daily_report_modules` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `report_id` INT NOT NULL,
    `module_name` VARCHAR(255) NOT NULL,
    `total_hours` DECIMAL(5,2) DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_daily_report_modules_report` FOREIGN KEY (`report_id`)
        REFERENCES `daily_reports`(`id`) ON DELETE CASCADE,
    INDEX `idx_daily_report_modules_report` (`report_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `daily_report_tasks` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `report_id` INT NOT NULL,
    `module_id` INT NULL,
    `task_name` VARCHAR(255) NOT NULL,
    `task_hours` DECIMAL(5,2) DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_daily_report_tasks_report` FOREIGN KEY (`report_id`)
        REFERENCES `daily_reports`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_daily_report_tasks_module` FOREIGN KEY (`module_id`)
        REFERENCES `daily_report_modules`(`id`) ON DELETE SET NULL,
    INDEX `idx_daily_report_tasks_report` (`report_id`),
    INDEX `idx_daily_report_tasks_module` (`module_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



CREATE TABLE document_permissions (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    document_id INT NOT NULL,
    user_id INT,
    role ENUM('admin', 'manager', 'member'),
    permission_type ENUM('view', 'download', 'edit', 'delete') NOT NULL DEFAULT 'view',
    granted_by INT NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (document_id),
    INDEX (user_id),
    INDEX (role),
    INDEX (permission_type),
    INDEX (granted_by),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE CASCADE
);


CREATE TABLE documents (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    organization_id INT NOT NULL,
    project_id INT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    file_extension VARCHAR(10) NOT NULL,
    uploaded_by INT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active TINYINT(1) DEFAULT 1,
    tags TEXT,
    version INT DEFAULT 1,
    parent_document_id INT,
    download_count INT DEFAULT 0,
    last_downloaded_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (organization_id),
    INDEX (project_id),
    INDEX (file_type),
    INDEX (uploaded_by),
    INDEX (upload_date),
    INDEX (is_active),
    INDEX (parent_document_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_document_id) REFERENCES documents(id) ON DELETE SET NULL
);




-- =====================================================
-- SAMPLE DATA
-- =====================================================

-- =====================================================
-- MIGRATION SAFEGUARDS (apply safely on existing databases)
-- =====================================================
-- Add avatar_url to users if missing
ALTER TABLE `users` 
    ADD COLUMN IF NOT EXISTS `avatar_url` VARCHAR(512) NULL COMMENT 'Profile picture URL' AFTER `updated_at`;


-- Reset foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Insert sample organization
INSERT INTO `organizations` (`name`) VALUES
('Demo Company Ltd');

-- Insert sample users with bcrypt passwords (password123 for all)
INSERT INTO `users` (`organization_id`, `full_name`, `email`, `password`, `role`) VALUES
(1, 'Admin User', 'admin@demo.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewWHoddw4Nfj8T/q', 'admin'),
(1, 'John Manager', 'manager@demo.com', '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'manager'),
(1, 'Jane Member', 'member@demo.com', '$2b$12$FGWWaU8Hl5.KZBdZhvY3JO5bXJWXxYvJKA3m8vQ7B5K9rC9Ao1rYK', 'member');

-- Insert sample project
INSERT INTO `projects` (`organization_id`, `name`, `description`, `status`, `start_date`, `end_date`, `created_by`) VALUES
(1, 'Sample Project', 'A sample project for demonstration', 'active', '2025-01-01', '2025-12-31', 1);

-- Insert sample milestone
INSERT INTO `milestones` (`project_id`, `name`, `description`, `due_date`, `created_by`) VALUES
(1, 'Project Kickoff', 'Initial project setup and planning', '2025-02-28', 1);

-- Insert sample tasks
INSERT INTO `tasks` (`project_id`, `milestone_id`, `title`, `description`, `status`, `priority`, `assigned_to`, `due_date`, `created_by`) VALUES
(1, 1, 'Setup Project Structure', 'Create initial project structure and documentation', 'in_progress', 'high', 2, '2025-02-15', 1),
(1, 1, 'Define Requirements', 'Gather and document project requirements', 'pending', 'medium', 3, '2025-02-20', 1),
(1, NULL, 'Code Review', 'Review existing codebase', 'completed', 'medium', 3, '2025-02-10', 1);

-- Insert sample project members
INSERT INTO `project_members` (`project_id`, `user_id`, `role`) VALUES
(1, 2, 'manager'),
(1, 3, 'member');

-- Insert sample task comment
INSERT INTO `task_comments` (`task_id`, `user_id`, `comment`) VALUES
(1, 2, 'Started working on the project structure. Setting up the basic folders and documentation.');

-- Insert sample daily report
INSERT INTO `daily_reports` (`user_id`, `organization_id`, `project_id`, `report_date`, `work_title`, `work_description`, `status`, `visible_to_manager`, `visible_to_admin`) VALUES
(2, 1, 1, '2025-02-28', 'Project Planning', 'Planning and discussing the project structure and requirements.', 'completed', TRUE, FALSE);

-- Insert sample message
INSERT INTO `messages` (`subject`, `content`, `sender_id`, `recipient_id`, `project_id`) VALUES
('Welcome to the Project', 'Welcome to the Sample Project! Please review the initial tasks assigned to you.', 1, 2, 1);

-- Insert sample notification
INSERT INTO `notifications` (`user_id`, `title`, `content`, `type`, `reference_type`, `reference_id`) VALUES
(2, 'New Task Assigned', 'You have been assigned a new task: Setup Project Structure', 'task_assigned', 'task', 1);


--##################document_permissions####################


-- =====================================================
-- USEFUL QUERIES FOR DEBUGGING
-- =====================================================

/*
-- Check database structure:
SHOW TABLES;

-- Check users and their roles:
SELECT u.id, u.full_name, u.email, u.role, o.name as organization
FROM users u 
JOIN organizations o ON u.organization_id = o.id;

-- Check project assignments:
SELECT p.name as project, u.full_name as member, pm.role
FROM projects p
JOIN project_members pm ON p.id = pm.project_id
JOIN users u ON pm.user_id = u.id;

-- Check tasks and assignments:
SELECT t.title, t.status, t.priority, 
       u_assigned.full_name as assigned_to,
       u_creator.full_name as created_by,
       p.name as project
FROM tasks t
LEFT JOIN users u_assigned ON t.assigned_to = u_assigned.id
LEFT JOIN users u_creator ON t.created_by = u_creator.id
LEFT JOIN projects p ON t.project_id = p.id;
*/

COMMIT;

-- =====================================================
-- SCHEMA SUMMARY
-- =====================================================
/*
This schema provides:
✅ Complete project management functionality
✅ Role-based access control
✅ Project visibility management
✅ Task management with milestones
✅ Internal messaging system
✅ Notification system
✅ Comment system for tasks
✅ Proper foreign key relationships
✅ Optimized indexes for performance
✅ Sample data for testing
✅ Support for both bcrypt and SHA256 passwords
✅ Full Unicode support (utf8mb4)

🆕 NEW v3.1 TEAM MANAGEMENT FEATURES:
✅ Advanced team assignments overview
✅ Auto-unassignment on project completion
✅ Enhanced team member visibility
✅ Smart assignment workflow management
✅ Comprehensive member-project relationship tracking

Core entities:
- Organizations (multi-tenant support)
- Users (with roles: admin, manager, member)
- Projects (with visibility controls & auto-completion workflow)
- Project Members (enhanced with auto-unassignment capabilities)
- Milestones (project phases)
- Tasks (with assignments and status)
- Messages (internal communication)
- Notifications (system alerts)
- Comments (task discussions)

Key relationships supporting team management:
- Users → Project Members (many-to-many with auto-cleanup)
- Projects → Status transitions (triggers member management)
- Project completion → Automatic team unassignment
- Admin dashboard → Cross-project assignment visibility
*/
