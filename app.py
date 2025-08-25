from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
import pymysql
import bcrypt
import os
import re
from datetime import datetime, timedelta, date
import secrets
from functools import wraps
from utils.db_helper import DatabaseHelper
import config
import branding_config
import logging

# Set up logging
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads', 'avatars')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

# Security Configuration
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Allow HTTP in development
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),  # Auto-logout after 2 hours
    WTF_CSRF_ENABLED=True,
    WTF_CSRF_TIME_LIMIT=None,
)

# Initialize database helper
db = DatabaseHelper(config.DB_CONFIG)

# Add today function to template context
@app.template_global()
def today():
    return date.today()

# Add branding configuration to template context
@app.context_processor
def inject_branding_config():
    return {
        'app_config': {
            'APP_NAME': branding_config.APP_NAME,
            'COMPANY_NAME': branding_config.COMPANY_NAME,
            'TAGLINE': branding_config.TAGLINE,
            'SUPPORT_EMAIL': branding_config.SUPPORT_EMAIL,
            'SALES_EMAIL': branding_config.SALES_EMAIL,
            'PHONE_NUMBER': branding_config.PHONE_NUMBER,
            'LOGO_ICON': branding_config.LOGO_ICON,
            'LOGO_TEXT': branding_config.LOGO_TEXT,
            'HERO_TITLE': branding_config.HERO_TITLE,
            'HERO_SUBTITLE': branding_config.HERO_SUBTITLE,
            'HERO_STATS': branding_config.HERO_STATS,
            'FEATURES_TITLE': branding_config.FEATURES_TITLE,
            'FEATURES_SUBTITLE': branding_config.FEATURES_SUBTITLE,
            'FEATURES_LIST': branding_config.FEATURES_LIST,
            'CTA_TITLE': branding_config.CTA_TITLE,
            'CTA_SUBTITLE': branding_config.CTA_SUBTITLE,
            'FOOTER_DESCRIPTION': branding_config.FOOTER_DESCRIPTION,
            'NAV_ITEMS': branding_config.NAV_ITEMS,
            'FOOTER_LINKS': branding_config.FOOTER_LINKS,
            'BUTTON_TEXT': branding_config.BUTTON_TEXT,
            'BRAND_COLORS': branding_config.BRAND_COLORS,
            'SHOW_SECTIONS': branding_config.SHOW_SECTIONS
        }
    }

# Add filter to safely convert date strings to date objects
@app.template_filter('to_date')
def to_date_filter(date_value):
    """Convert date string/datetime to date object for safe comparisons"""
    if not date_value:
        return None
    if isinstance(date_value, datetime):
        return date_value.date()  # Convert datetime to date
    if isinstance(date_value, date):
        return date_value  # Already a date object
    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S').date()
            except ValueError:
                try:
                    return datetime.strptime(date_value, '%m/%d/%Y').date()
                except ValueError:
                    return None
    return None

########################## Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user = db.get_user_by_id(session['user_id'])
        if not user or user['role'] not in ['admin', 'manager']:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def admin_only_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user = db.get_user_by_id(session['user_id'])
        if not user or user['role'] != 'admin':
            flash('Access denied. Only administrators can perform this action.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to hash passwords
def hash_password(password):
    """Hash password using bcrypt with salt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against bcrypt or SHA-256 hash (backwards compatibility)"""
    if hashed.startswith('$2b$'):
        # bcrypt hash (new format)
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    else:
        # SHA-256 hash (legacy format) - for backwards compatibility
        import hashlib
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        return sha256_hash == hashed

# Helper function to validate email
def is_valid_email(email):
    """Validate email address using regex"""
    if not email or len(email.strip()) == 0:
        return False
    
    email = email.strip()
    # RFC 5322 compliant email regex pattern
    pattern = r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    return re.match(pattern, email) is not None

############################################ Routes
@app.route('/')
def index():
    """Always show landing page first, regardless of login status"""
    return render_template('landing.html')

@app.route('/landing')
def landing():
    """Professional landing page for marketing and lead generation"""
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = db.get_user_by_email(email)
        if user and verify_password(password, user['password']):
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_role'] = user['role']
            session['organization_id'] = user['organization_id']
            session['organization_name'] = user.get('organization_name')
            # Populate commonly used session fields for dashboards
            session['user_email'] = user.get('email', '')
            session['avatar_url'] = user.get('avatar_url')
            # Handle created_at safely - it might be None or a string
            created_at = user.get('created_at')
            if created_at:
                if hasattr(created_at, 'strftime'):
                    # It's a datetime object
                    session['user_created_at'] = created_at.strftime('%Y-%m-%d')
                else:
                    # It's already a string or other format
                    session['user_created_at'] = str(created_at)
            else:
                session['user_created_at'] = 'Unknown'
            
            # Debug: print session data
            print(f"DEBUG: Session data set - Email: {session['user_email']}, Created: {session['user_created_at']}")
            
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Validate required fields
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        organization_name = request.form.get('organization_name', '').strip()
        
        # Server-side validation
        if not full_name or not email or not password or not organization_name:
            flash('Please fill in all required fields.', 'error')
            return render_template('auth/register.html')
        
        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('auth/register.html')
        
        data = {
            'full_name': full_name,
            'email': email.lower(),  # Store email in lowercase
            'password': hash_password(password),
            'organization_name': organization_name,
            'phone': request.form.get('phone', '').strip(),
            'role': 'admin'  # First user becomes admin
        }
        
        try:
            user_id = db.create_user_with_organization(data)
            if user_id:
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Email already exists. Please use a different email address.', 'error')
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')
    
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get data based on user role with role-specific methods
    if session['user_role'] == 'admin':
        # Admins see all organization data
        stats = db.get_dashboard_stats(session['organization_id'])
        recent_projects = db.get_recent_projects(session['organization_id'], limit=5)
        overdue_tasks = db.get_overdue_tasks(session['organization_id'])
        overdue_tasks_by_user = db.get_overdue_tasks_by_user(session['organization_id'])
        tasks_due_soon = db.get_tasks_due_soon(session['organization_id'], days=7)
    elif session['user_role'] == 'manager':
        # Managers see only their assigned projects and related data
        stats = db.get_manager_dashboard_stats(session['user_id'], session['organization_id'])
        recent_projects = db.get_manager_assigned_projects(session['user_id'], session['organization_id'])[:5]
        overdue_tasks = db.get_manager_overdue_tasks(session['user_id'], session['organization_id'])
        overdue_tasks_by_user = db.get_manager_overdue_tasks_by_user(session['user_id'], session['organization_id'])
        tasks_due_soon = db.get_manager_tasks_due_soon(session['user_id'], session['organization_id'], days=7)
    else:
        # Members see projects based on visibility rules
        stats = db.get_dashboard_stats(session['organization_id'])
        recent_projects = db.get_user_visible_projects(session['user_id'], session['organization_id'])[:5]
        overdue_tasks = db.get_overdue_tasks(session['organization_id'], user_id=session['user_id'])
        overdue_tasks_by_user = {}
        tasks_due_soon = db.get_tasks_due_soon(session['organization_id'], days=7)
    
    recent_tasks = db.get_user_recent_tasks(session['user_id'], limit=10)
    
    # Route to specific dashboard based on user role
    if session['user_role'] == 'manager':
        return render_template('manager_dashboard.html', 
                             stats=stats, 
                             recent_projects=recent_projects,
                             recent_tasks=recent_tasks,
                             overdue_tasks=overdue_tasks,
                             overdue_tasks_by_user=overdue_tasks_by_user,
                             tasks_due_soon=tasks_due_soon)
    elif session['user_role'] == 'member':
        return render_template('member_dashboard.html', 
                             stats=stats, 
                             recent_projects=recent_projects,
                             recent_tasks=recent_tasks,
                             overdue_tasks=overdue_tasks,
                             tasks_due_soon=tasks_due_soon)
    else:
        # Default dashboard for admin
        return render_template('dashboard.html', 
                             stats=stats, 
                             recent_projects=recent_projects,
                             recent_tasks=recent_tasks,
                             overdue_tasks=overdue_tasks,
                             overdue_tasks_by_user=overdue_tasks_by_user,
                             tasks_due_soon=tasks_due_soon)

############################ Projects Routes (visibility-aware)
@app.route('/projects')
@login_required
def projects():
    if session['user_role'] == 'admin':
        # Admins see all projects with manager assignment info
        projects = db.get_projects_with_manager_info(session['organization_id'])
    elif session['user_role'] == 'manager':
        # Managers see only projects assigned to them
        projects = db.get_manager_assigned_projects(session['user_id'], session['organization_id'])
    else:
        # Members see projects based on visibility rules
        projects = db.get_user_visible_projects(session['user_id'], session['organization_id'])
    
    return render_template('projects/list.html', projects=projects)

@app.route('/projects/new', methods=['GET', 'POST'])
@admin_required
def new_project():
    if request.method == 'POST':
        data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'start_date': request.form.get('start_date'),
            'end_date': request.form.get('end_date'),
            'organization_id': session['organization_id'],
            'created_by': session['user_id'],
            'assigned_manager_id': request.form.get('assigned_manager_id') or None
        }
        
        project_id = db.create_project(data)
        if project_id:
            flash('Project created successfully!', 'success')
            return redirect(url_for('view_project', id=project_id))
        else:
            flash('Failed to create project.', 'error')
    
    # Get available managers for the dropdown
    managers = db.get_available_managers(session['organization_id'])
    return render_template('projects/new.html', managers=managers)

@app.route('/projects/<int:id>')
@login_required
def view_project(id):
    project = db.get_project_by_id(id)
    if not project or project['organization_id'] != session['organization_id']:
        flash('Project not found.', 'error')
        return redirect(url_for('projects'))
    
    tasks = db.get_project_tasks(id)
    milestones = db.get_project_milestones(id)
    team_members = db.get_project_team_members(id)
    
    return render_template('projects/view.html', 
                         project=project, 
                         tasks=tasks, 
                         milestones=milestones,
                         team_members=team_members)

@app.route('/projects/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_project(id):
    project = db.get_project_by_id(id)
    if not project or project['organization_id'] != session['organization_id']:
        flash('Project not found.', 'error')
        return redirect(url_for('projects'))
    
    if request.method == 'POST':
        data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'start_date': request.form.get('start_date'),
            'end_date': request.form.get('end_date'),
            'status': request.form['status'],
            'assigned_manager_id': request.form.get('assigned_manager_id') or None
        }
        
        if db.update_project(id, data):
            flash('Project updated successfully!', 'success')
            return redirect(url_for('view_project', id=id))
        else:
            flash('Failed to update project.', 'error')
    
    # Get available managers for the dropdown
    managers = db.get_available_managers(session['organization_id'])
    return render_template('projects/edit.html', project=project, managers=managers)

@app.route('/projects/<int:id>/delete', methods=['POST'])
@admin_only_required
def delete_project(id):
    project = db.get_project_by_id(id)
    if not project or project['organization_id'] != session['organization_id']:
        flash('Project not found.', 'error')
        return redirect(url_for('projects'))
    
    if db.delete_project(id):
        flash(f'Project "{project["name"]}" has been deleted successfully!', 'success')
    else:
        flash('Failed to delete project.', 'error')
    
    return redirect(url_for('projects'))

# Tasks Routes
@app.route('/tasks')
@login_required
def tasks():
    user_tasks = db.get_user_tasks(session['user_id'])
    return render_template('tasks/list.html', tasks=user_tasks)

@app.route('/tasks/all')
@login_required
def all_tasks():
    if session.get('user_role') == 'member':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    # Get filter parameter
    creator_role = request.args.get('creator_role')
    
    # Get tasks based on filter with role-based access control
    tasks = db.get_tasks_by_creator_role(
        session['organization_id'], 
        creator_role, 
        session['user_id'], 
        session['user_role']
    )
    
    # Get unique creator roles for filter dropdown (also with access control)
    all_tasks_for_roles = db.get_tasks_by_creator_role(
        session['organization_id'], 
        None, 
        session['user_id'], 
        session['user_role']
    )
    creator_roles = []
    seen_roles = set()
    for task in all_tasks_for_roles:
        if task['created_by_role'] not in seen_roles:
            creator_roles.append({
                'role': task['created_by_role'],
                'display': task['created_by_role'].title()
            })
            seen_roles.add(task['created_by_role'])
    
    # Sort roles for consistent display
    creator_roles.sort(key=lambda x: x['role'])
    
    return render_template('tasks/all_tasks.html', 
                         tasks=tasks, 
                         creator_roles=creator_roles,
                         selected_role=creator_role)

@app.route('/tasks/new', methods=['GET', 'POST'])
@login_required
def new_task():
    if request.method == 'POST':
        # Handle empty values properly
        assigned_to = request.form.get('assigned_to')
        if assigned_to == '':
            assigned_to = None
        
        milestone_id = request.form.get('milestone_id')
        if milestone_id == '':
            milestone_id = None
            
        due_date = request.form.get('due_date')
        if due_date == '':
            due_date = None
        
        data = {
            'title': request.form['title'],
            'description': request.form['description'],
            'project_id': request.form['project_id'],
            'assigned_to': assigned_to,
            'priority': request.form['priority'],
            'due_date': due_date,
            'milestone_id': milestone_id,
            'created_by': session['user_id']
        }
        
        try:
            task_id = db.create_task(data)
            if task_id:
                flash('Task created successfully!', 'success')
                return redirect(url_for('view_task', id=task_id))
            else:
                flash('Failed to create task.', 'error')
        except ValueError as e:
            flash(str(e), 'error')
    
    # Get projects based on user role
    user_role = session.get('user_role')
    org_id = session.get('organization_id')
    
    if user_role == 'admin':
        projects = db.get_organization_projects(org_id)
    elif user_role == 'manager':
        projects = db.get_manager_assigned_projects(session['user_id'], org_id)
    else:
        projects = db.get_user_visible_projects(session['user_id'], org_id)
    
    milestones = []
    users = []  # Will be loaded via AJAX based on project selection
    
    selected_project = None
    if request.args.get('project_id'):
        project_id = request.args.get('project_id')
        milestones = db.get_project_milestones(project_id)
        users = db.get_project_assignable_members(project_id,user_role)
        selected_project = db.get_project_by_id(project_id)
    
    return render_template('tasks/new.html', 
                         projects=projects, 
                         users=users, 
                         milestones=milestones,
                         selected_project=selected_project)

@app.route('/tasks/<int:id>')
@login_required
def view_task(id):
    task = db.get_task_by_id(id)
    if not task:
        flash('Task not found.', 'error')
        return redirect(url_for('tasks'))
    
    # Check if user has access to this task
    project = db.get_project_by_id(task['project_id'])
    if project['organization_id'] != session['organization_id']:
        flash('Access denied.', 'error')
        return redirect(url_for('tasks'))

    # Extra check: if member, ensure task is assigned to them
    if session['user_role'] == 'member' and task['assigned_to'] != session['user_id']:
        flash('You are not allowed to view this task.', 'error')
        return redirect(url_for('tasks'))
    
    comments = db.get_task_comments(id)
    return render_template('tasks/view.html', task=task, comments=comments)

@app.route('/tasks/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    task = db.get_task_by_id(id)
    if not task:
        flash('Task not found.', 'error')
        return redirect(url_for('tasks'))
    
    # Check permissions
    project = db.get_project_by_id(task['project_id'])
    if project['organization_id'] != session['organization_id']:
        flash('Access denied.', 'error')
        return redirect(url_for('tasks'))
    
    # Check if user is a member - members can only edit tasks assigned to them
    if session['user_role'] == 'member':
        if task['assigned_to'] != session['user_id']:
            flash('You can only edit tasks assigned to you.', 'error')
            return redirect(url_for('tasks'))
    
    if request.method == 'POST':
        # Members can only update status
        if session['user_role'] == 'member':
            data = {
                'status': request.form['status']
            }
        else:
            # Admins and managers can update all fields
            data = {
                'title': request.form['title'],
                'description': request.form['description'],
                'assigned_to': request.form.get('assigned_to'),
                'priority': request.form['priority'],
                'status': request.form['status'],
                'due_date': request.form.get('due_date'),
                'milestone_id': request.form.get('milestone_id')
            }
        
        if db.update_task(id, data):
            if session['user_role'] == 'member':
                flash('Task status updated successfully!', 'success')
            else:
                flash('Task updated successfully!', 'success')
            return redirect(url_for('view_task', id=id))
        else:
            flash('Failed to update task.', 'error')
    
    projects = db.get_organization_projects(session['organization_id'])
    # ✅ pass role too
    users = db.get_project_assignable_members(task['project_id'], session['user_role'])
    milestones = db.get_project_milestones(task['project_id'])
    
    return render_template(
        'tasks/edit.html', 
        task=task, 
        projects=projects, 
        users=users, 
        milestones=milestones,
        user_role=session['user_role']
    )


###################### Messages Routes
@app.route('/messages')
@login_required
def messages():
    user_messages = db.get_user_messages(session['user_id'])
    return render_template('messages/list.html', messages=user_messages)

@app.route('/messages/new', methods=['GET', 'POST'])
@login_required
def new_message():
    if request.method == 'POST':
        data = {
            'subject': request.form['subject'],
            'content': request.form['content'],
            'sender_id': session['user_id'],
            'recipient_id': request.form['recipient_id'],
            'project_id': request.form.get('project_id')
        }
        
        message_id = db.create_message(data)
        if message_id:
            flash('Message sent successfully!', 'success')
            return redirect(url_for('messages'))
        else:
            flash('Failed to send message.', 'error')
    
    users = db.get_organization_users(session['organization_id'])
    projects = db.get_organization_projects(session['organization_id'])
    
    return render_template('messages/new.html', users=users, projects=projects)

@app.route('/messages/<int:id>')
@login_required
def view_message(id):
    message = db.get_message_by_id(id)
    if not message or (message['sender_id'] != session['user_id'] and message['recipient_id'] != session['user_id']):
        flash('Message not found.', 'error')
        return redirect(url_for('messages'))
    
    # Mark as read if recipient is viewing
    if message['recipient_id'] == session['user_id'] and not message['read_at']:
        db.mark_message_as_read(id)
    
    return render_template('messages/view.html', message=message)

############################ User Management Routes
@app.route('/users')
@admin_required
def users():
    users = db.get_organization_users(session['organization_id'])
    return render_template('users/list.html', users=users)

@app.route('/users/new', methods=['GET', 'POST'])
@admin_required
def new_user():
    if request.method == 'POST':
        data = {
            'organization_id': session['organization_id'],
            'full_name': request.form['full_name'],
            'email': request.form['email'],
            'password': hash_password(request.form['password']),
            'phone': request.form.get('phone', ''),
            'role': request.form['role']
        }
        
        try:
            user_id = db.create_user(data)
            if user_id:
                flash(f'User {data["full_name"]} created successfully!', 'success')
                return redirect(url_for('users'))
            else:
                flash('Email already exists.', 'error')
        except Exception as e:
            flash(f'Failed to create user: {str(e)}', 'error')
    
    return render_template('users/new.html')

@app.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    user = db.get_user_by_id(id)
    if not user or user['organization_id'] != session['organization_id']:
        flash('User not found.', 'error')
        return redirect(url_for('users'))
    
    # Get current user info for role checking
    current_user = db.get_user_by_id(session['user_id'])
    
    # Prevent editing own admin role
    if user['id'] == session['user_id'] and user['role'] == 'admin':
        flash('You cannot edit your own admin role.', 'warning')
        return redirect(url_for('users'))
    
    # Prevent managers from editing admin users
    if current_user['role'] == 'manager' and user['role'] == 'admin':
        flash('Access denied. Managers cannot edit admin users.', 'error')
        return redirect(url_for('users'))
    
    # Prevent managers from editing other managers
    if current_user['role'] == 'manager' and user['role'] == 'manager' and user['id'] != session['user_id']:
        flash('Access denied. Managers cannot edit other managers.', 'error')
        return redirect(url_for('users'))
    
    if request.method == 'POST':
        # Get the requested role
        requested_role = request.form['role']
        
        # Role change validation for managers
        if current_user['role'] == 'manager':
            # Prevent managers from setting admin role
            if requested_role == 'admin':
                flash('Access denied. Managers cannot assign admin role.', 'error')
                return render_template('users/edit.html', user=user, current_user_role=current_user['role'])
            # Prevent managers from changing other managers' roles
            if user['role'] == 'manager' and user['id'] != session['user_id']:
                flash('Access denied. Managers cannot change the role of other managers.', 'error')
                return render_template('users/edit.html', user=user, current_user_role=current_user['role'])
            # Prevent managers from promoting users to managers
            if requested_role == 'manager' and user['role'] != 'manager':
                flash('Access denied. Managers cannot promote users to manager role.', 'error')
                return render_template('users/edit.html', user=user, current_user_role=current_user['role'])
        
        data = {
            'full_name': request.form['full_name'],
            'email': request.form['email'],
            'phone': request.form.get('phone', ''),
            'role': requested_role,
            'is_active': 'is_active' in request.form
        }
        
        # Update password only if provided
        if request.form.get('password'):
            data['password'] = hash_password(request.form['password'])
        
        try:
            if db.update_user(id, data):
                flash(f'User {data["full_name"]} updated successfully!', 'success')
                return redirect(url_for('users'))
            else:
                flash('Failed to update user.', 'error')
        except Exception as e:
            flash(f'Failed to update user: {str(e)}', 'error')
    
    return render_template('users/edit.html', user=user, current_user_role=current_user['role'])

@app.route('/users/<int:id>/toggle-status', methods=['POST'])
@admin_only_required
def toggle_user_status(id):
    user = db.get_user_by_id(id)
    if not user or user['organization_id'] != session['organization_id']:
        flash('User not found.', 'error')
        return redirect(url_for('users'))
    
    # Prevent deactivating own account
    if user['id'] == session['user_id']:
        flash('You cannot deactivate your own account.', 'warning')
        return redirect(url_for('users'))
    
    new_status = not user['is_active']
    if db.update_user_status(id, new_status):
        status_text = 'activated' if new_status else 'deactivated'
        flash(f'User {user["full_name"]} has been {status_text}.', 'success')
    else:
        flash('Failed to update user status.', 'error')
    
    return redirect(url_for('users'))

# ############################Task Comments Route
@app.route('/tasks/<int:task_id>/comments', methods=['POST'])
@login_required
def add_task_comment(task_id):
    task = db.get_task_by_id(task_id)
    if not task:
        flash('Task not found.', 'error')
        return redirect(url_for('tasks'))
    
    # Check if user has access to this task
    project = db.get_project_by_id(task['project_id'])
    if project['organization_id'] != session['organization_id']:
        flash('Access denied.', 'error')
        return redirect(url_for('tasks'))
    
    comment_text = request.form.get('comment', '').strip()
    if comment_text:
        data = {
            'task_id': task_id,
            'user_id': session['user_id'],
            'content': comment_text
        }
        
        if db.create_task_comment(data):
            flash('Comment added successfully!', 'success')
        else:
            flash('Failed to add comment.', 'error')
    else:
        flash('Comment cannot be empty.', 'error')
    
    return redirect(url_for('view_task', id=task_id))

########################## API Routes for AJAX
@app.route('/api/project/<int:project_id>')
@login_required
def api_project_details(project_id):
    """Get project details for AJAX requests"""
    project = db.get_project_by_id(project_id)
    if not project or project['organization_id'] != session['organization_id']:
        return jsonify({'error': 'Project not found'}), 404
    
    return jsonify({
        'id': project['id'],
        'name': project['name'],
        'description': project['description'],
        'status': project['status'],
        'start_date': project['start_date'].strftime('%Y-%m-%d') if project['start_date'] else None,
        'end_date': project['end_date'].strftime('%Y-%m-%d') if project['end_date'] else None,
        'created_by': project['created_by'],
        'created_at': project['created_at'].strftime('%Y-%m-%d') if project['created_at'] else None
    })

@app.route('/api/project/<int:project_id>/milestones')
@login_required
def api_project_milestones(project_id):
    milestones = db.get_project_milestones(project_id)
    return jsonify([{
        'id': m['id'], 
        'name': m['name'],
        'due_date': m['due_date'].strftime('%Y-%m-%d') if m['due_date'] else None
    } for m in milestones])

@app.route('/api/project/<int:project_id>/assignable-members')
@login_required
def api_project_assignable_members(project_id):
    user_role = session.get('user_role')
    members = db.get_project_assignable_members(project_id, user_role)
    return jsonify(members)

@app.route('/api/manager/projects')
@login_required
def api_manager_projects():
    """API endpoint for managers to get their assigned projects"""
    if session['user_role'] != 'manager':
        return jsonify({'error': 'Access denied'}), 403
    
    projects = db.get_manager_assigned_projects(session['user_id'], session['organization_id'])
    return jsonify({
        'projects': [
            {
                'id': p['id'],
                'name': p['name'],
                'description': p['description'],
                'status': p['status'],
                'task_count': p['task_count'],
                'completed_tasks': p['completed_tasks']
            } for p in projects
        ]
    })

@app.route('/manager/projects')
@login_required
def manager_project_selector():
    """Manager project selector page where managers can view and select from their assigned projects"""
    if session['user_role'] != 'manager':
        flash('Access denied. This page is only available to managers.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get manager's assigned projects
    projects = db.get_manager_assigned_projects(session['user_id'], session['organization_id'])
    return render_template('projects/manager_project_selector.html', projects=projects)

######################### Dashboard Routes by Role
@app.route('/manager-dashboard')
@login_required
def manager_dashboard():
    if session['user_role'] not in ['admin', 'manager']:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    # Use manager-specific methods for role-based data
    if session['user_role'] == 'manager':
        stats = db.get_manager_dashboard_stats(session['user_id'], session['organization_id'])
        recent_projects = db.get_manager_assigned_projects(session['user_id'], session['organization_id'])[:5]
        overdue_tasks = db.get_manager_overdue_tasks(session['user_id'], session['organization_id'])
        overdue_tasks_by_user = db.get_manager_overdue_tasks_by_user(session['user_id'], session['organization_id'])
        tasks_due_soon = db.get_manager_tasks_due_soon(session['user_id'], session['organization_id'], days=7)
    else:
        # Admin sees all organization data
        stats = db.get_dashboard_stats(session['organization_id'])
        recent_projects = db.get_recent_projects(session['organization_id'], limit=5)
        overdue_tasks = db.get_overdue_tasks(session['organization_id'])
        overdue_tasks_by_user = db.get_overdue_tasks_by_user(session['organization_id'])
        tasks_due_soon = db.get_tasks_due_soon(session['organization_id'], days=7)
    
    recent_tasks = db.get_user_recent_tasks(session['user_id'], limit=10)
    
    return render_template('manager_dashboard.html', 
                         stats=stats, 
                         recent_projects=recent_projects,
                         recent_tasks=recent_tasks,
                         overdue_tasks=overdue_tasks,
                         overdue_tasks_by_user=overdue_tasks_by_user,
                         tasks_due_soon=tasks_due_soon)

@app.route('/member-dashboard')
@login_required
def member_dashboard():
    stats = db.get_dashboard_stats(session['organization_id'])
    recent_projects = db.get_recent_projects(session['organization_id'], limit=5)
    recent_tasks = db.get_user_recent_tasks(session['user_id'], limit=10)
    overdue_tasks = db.get_overdue_tasks(session['organization_id'])
    
    return render_template('member_dashboard.html', 
                         stats=stats, 
                         recent_projects=recent_projects,
                         recent_tasks=recent_tasks,
                         overdue_tasks=overdue_tasks)

############################## Milestone Management Routes
@app.route('/projects/<int:project_id>/milestones/new', methods=['GET', 'POST'])
@admin_required
def new_milestone(project_id):
    project = db.get_project_by_id(project_id)
    if not project or project['organization_id'] != session['organization_id']:
        flash('Project not found.', 'error')
        return redirect(url_for('projects'))
        
    # Format dates for display
    if project['start_date'] and project['end_date']:
        project['formatted_start_date'] = project['start_date'].strftime('%Y-%m-%d')
        project['formatted_end_date'] = project['end_date'].strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        data = {
            'project_id': project_id,
            'name': request.form['name'],
            'description': request.form['description'],
            'due_date': request.form.get('due_date'),
            'created_by': session['user_id']
        }
        
        try:
            milestone_id = db.create_milestone(data)
            if milestone_id:
                flash('Milestone created successfully!', 'success')
                return redirect(url_for('view_project', id=project_id))
            else:
                flash('Failed to create milestone.', 'error')
        except ValueError as e:
            flash(str(e), 'error')
    
    return render_template('milestones/new.html', project=project)

@app.route('/milestones/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_milestone(id):
    milestone = db.get_milestone_by_id(id)
    if not milestone:
        flash('Milestone not found.', 'error')
        return redirect(url_for('projects'))
    
    # Check organization access
    project = db.get_project_by_id(milestone['project_id'])
    if project['organization_id'] != session['organization_id']:
        flash('Access denied.', 'error')
        return redirect(url_for('projects'))
    
    if request.method == 'POST':
        data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'due_date': request.form.get('due_date'),
            'status': request.form['status']
        }
        
        if db.update_milestone(id, data):
            flash('Milestone updated successfully!', 'success')
            return redirect(url_for('view_project', id=milestone['project_id']))
        else:
            flash('Failed to update milestone.', 'error')
    
    return render_template('milestones/edit.html', milestone=milestone, project=project)

@app.route('/milestones/<int:milestone_id>/assign/<int:user_id>', methods=['POST'])
@admin_required
def assign_milestone(milestone_id, user_id):
    milestone = db.get_milestone_by_id(milestone_id)
    if not milestone:
        flash('Milestone not found.', 'error')
        return redirect(url_for('projects'))
    
    # Check organization access
    project = db.get_project_by_id(milestone['project_id'])
    if project['organization_id'] != session['organization_id']:
        flash('Access denied.', 'error')
        return redirect(url_for('projects'))
    
    # Check if user exists and is in same organization
    user = db.get_user_by_id(user_id)
    if not user or user['organization_id'] != session['organization_id']:
        flash('User not found.', 'error')
        return redirect(url_for('view_project', id=milestone['project_id']))
    
    if db.assign_milestone_to_user(milestone_id, user_id, session['user_id']):
        flash(f'Milestone assigned to {user["full_name"]} successfully!', 'success')
    else:
        flash('Failed to assign milestone.', 'error')
    
    return redirect(url_for('view_project', id=milestone['project_id']))

####################### Project Visibility Routes
@app.route('/projects/<int:id>/visibility', methods=['GET', 'POST'])
@admin_required
def project_visibility(id):
    project = db.get_project_by_id(id)
    if not project or project['organization_id'] != session['organization_id']:
        flash('Project not found.', 'error')
        return redirect(url_for('projects'))
    
    if request.method == 'POST':
        visibility = request.form['visibility']
        member_ids = request.form.getlist('member_ids')
        
        data = {
            'visibility': visibility,
            'member_ids': member_ids if visibility == 'specific' else []
        }
        
        if db.update_project_visibility(id, data):
            flash('Project visibility updated successfully!', 'success')
            return redirect(url_for('view_project', id=id))
        else:
            flash('Failed to update project visibility.', 'error')
    
    # Get all members for selection
    all_members = db.get_organization_users(session['organization_id'])
    members_only = [u for u in all_members if u['role'] == 'member']
    
    # Get current visible members
    visible_members = db.get_project_assigned_members(id)
    
    return render_template('projects/visibility.html', 
                         project=project, 
                         members=members_only,
                         visible_members=visible_members)

@app.route('/projects/<int:id>/team-members', methods=['GET', 'POST'])
@admin_only_required
def manage_project_team_members(id):
    """Manage team members for a project - Admin only"""
    project = db.get_project_by_id(id)
    if not project or project['organization_id'] != session['organization_id']:
        flash('Project not found.', 'error')
        return redirect(url_for('projects'))
    
    if request.method == 'POST':
        # Get selected team member IDs
        member_ids = request.form.getlist('member_ids')
        
        # Assign team members to project
        if db.assign_team_members_to_project(id, member_ids, session['user_id']):
            if len(member_ids) > 0:
                flash(f'Successfully assigned {len(member_ids)} team member(s) to the project!', 'success')
            else:
                flash('Team member assignments cleared.', 'info')
            
            # Notify the project manager if one is assigned
            if project.get('assigned_manager_id'):
                try:
                    # Get assigned member names for notification
                    if member_ids:
                        assigned_members = db.get_project_assigned_members(id)
                        member_names = [member['full_name'] for member in assigned_members]
                        member_list = ', '.join(member_names)
                        
                        notification_data = {
                            'sender_id': session['user_id'],
                            'recipient_id': project['assigned_manager_id'],
                            'project_id': id,
                            'subject': f'Team Members Assigned to {project["name"]}',
                            'content': f'The following team members have been assigned to your project "{project["name"]}":\n\n{member_list}\n\nYou can now coordinate tasks and track their progress.'
                        }
                        db.create_message(notification_data)
                    else:
                        notification_data = {
                            'sender_id': session['user_id'],
                            'recipient_id': project['assigned_manager_id'],
                            'project_id': id,
                            'subject': f'Team Member Changes - {project["name"]}',
                            'content': f'Team member assignments for project "{project["name"]}" have been updated by the administrator.'
                        }
                        db.create_message(notification_data)
                except Exception as e:
                    # Don't fail the main operation if notification fails
                    logger.error(f"Failed to send notification to manager: {e}")
            
            return redirect(url_for('view_project', id=id))
        else:
            flash('Failed to assign team members. Please try again.', 'error')
    
    # Get all available team members
    available_members = db.get_available_team_members(session['organization_id'])
    
    # Get currently assigned team members
    assigned_members = db.get_project_assigned_members(id)
    assigned_member_ids = [member['id'] for member in assigned_members]
    
    return render_template('projects/team_members.html', 
                         project=project, 
                         available_members=available_members,
                         assigned_members=assigned_members,
                         assigned_member_ids=assigned_member_ids)

@app.route('/projects/<int:project_id>/remove-member/<int:member_id>', methods=['POST'])
@admin_only_required
def remove_project_team_member(project_id, member_id):
    """Remove a team member from a project - Admin only"""
    project = db.get_project_by_id(project_id)
    if not project or project['organization_id'] != session['organization_id']:
        flash('Project not found.', 'error')
        return redirect(url_for('projects'))
    
    # Get member info for notification
    member = db.get_user_by_id(member_id)
    if not member:
        flash('Member not found.', 'error')
        return redirect(url_for('view_project', id=project_id))
    
    if db.remove_team_member_from_project(project_id, member_id):
        flash(f'{member["full_name"]} has been removed from the project team.', 'success')
        
        # Notify the project manager if one is assigned
        if project.get('assigned_manager_id'):
            try:
                notification_data = {
                    'sender_id': session['user_id'],
                    'recipient_id': project['assigned_manager_id'],
                    'project_id': project_id,
                    'subject': f'Team Member Removed - {project["name"]}',
                    'content': f'{member["full_name"]} has been removed from the project "{project["name"]}" team by the administrator.'
                }
                db.create_message(notification_data)
            except Exception as e:
                # Don't fail the main operation if notification fails
                logger.error(f"Failed to send notification to manager: {e}")
    else:
        flash('Failed to remove team member. Please try again.', 'error')
    
    return redirect(url_for('view_project', id=project_id))

@app.route('/team-assignments')
@admin_only_required
def team_assignments_overview():
    """Overview of team member assignments across all projects - Admin only"""
    # Get all team members with their project assignments
    team_members = db.get_organization_users(session['organization_id'])
    
    # Filter to only members and get their project assignments
    member_assignments = []
    for member in team_members:
        if member['role'] == 'member':
            assignments = db.get_user_project_assignments(member['id'])
            member_assignments.append({
                'member': member,
                'assignments': assignments,
                'active_count': len([a for a in assignments if a['status'] == 'active']),
                'total_count': len(assignments)
            })
    
    # Sort by active project count (descending) then by name
    member_assignments.sort(key=lambda x: (-x['active_count'], x['member']['full_name']))
    
    return render_template('team_assignments_overview.html', 
                         member_assignments=member_assignments)

# ##################Report Generation Routes
@app.route('/reports')
@login_required
def reports_dashboard():
    if session['user_role'] not in ['admin', 'manager']:
        flash('Access denied. Reports are only available to admins and managers.', 'error')
        return redirect(url_for('dashboard'))
    
    projects = db.get_organization_projects(session['organization_id'])
    users = db.get_organization_users(session['organization_id'])
    
    return render_template('reports/dashboard.html', projects=projects, users=users)

@app.route('/reports/project/<int:project_id>')
@login_required
def project_report(project_id):
    if session['user_role'] not in ['admin', 'manager']:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    project = db.get_project_by_id(project_id)
    if not project or project['organization_id'] != session['organization_id']:
        flash('Project not found.', 'error')
        return redirect(url_for('reports_dashboard'))
    
    # Get date range from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    report_data = db.generate_project_report(project_id, start_date, end_date)
    if not report_data:
        flash('Failed to generate report.', 'error')
        return redirect(url_for('reports_dashboard'))
    
    return render_template('reports/project.html', report=report_data)

@app.route('/reports/user/<int:user_id>')
@login_required
def user_report(user_id):
    if session['user_role'] not in ['admin', 'manager']:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    user = db.get_user_by_id(user_id)
    if not user or user['organization_id'] != session['organization_id']:
        flash('User not found.', 'error')
        return redirect(url_for('reports_dashboard'))
    
    # Get date range from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    report_data = db.generate_user_report(user_id, start_date, end_date)
    if not report_data:
        flash('Failed to generate report.', 'error')
        return redirect(url_for('reports_dashboard'))
    
    return render_template('reports/user.html', report=report_data)

@app.route('/reports/organization')
@login_required
def organization_report():
    if session['user_role'] != 'admin':
        flash('Access denied. Organization reports are only available to admins.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get date range from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    report_data = db.get_organization_report(session['organization_id'], start_date, end_date)
    if not report_data:
        flash('Failed to generate report.', 'error')
        return redirect(url_for('reports_dashboard'))
    
    return render_template('reports/organization.html', report=report_data)

# Notification Routes
@app.route('/api/notifications')
@login_required
def api_notifications():
    """API endpoint to get user notifications"""
    limit = request.args.get('limit', 10, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    notifications = db.get_user_notifications(session['user_id'], limit=limit, unread_only=unread_only)
    
    return jsonify({
        'notifications': [
            {
                'id': n['id'],
                'title': n['title'],
                'message': n['message'],
                'type': n['type'],
                'days_until_due': n['days_until_due'],
                'is_read': bool(n['is_read']),
                'created_at': n['created_at'].isoformat() if n['created_at'] else None,
                'task_title': n['task_title'],
                'project_name': n['project_name']
            } for n in notifications
        ]
    })

@app.route('/api/notifications/<int:notification_id>/mark-read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a specific notification as read"""
    success = db.mark_notification_as_read(notification_id, session['user_id'])
    return jsonify({'success': success})

@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read for current user"""
    count = db.mark_all_notifications_as_read(session['user_id'])
    return jsonify({'success': True, 'marked_count': count})

@app.route('/api/notifications/count')
@login_required
def get_notification_count():
    """Get unread notification count"""
    count = db.get_unread_notification_count(session['user_id'])
    return jsonify({'unread_count': count})

@app.route('/api/messages/count')
@login_required
def get_message_count():
    """Get unread message count"""
    count = db.get_unread_message_count(session['user_id'])
    return jsonify({'unread_count': count})

@app.route('/notifications')
@login_required
def notifications():
    """Show notifications page"""
    notifications = db.get_user_notifications(session['user_id'], limit=50)
    unread_count = db.get_unread_notification_count(session['user_id'])
    
    return render_template('notifications/list.html', 
                         notifications=notifications,
                         unread_count=unread_count)

@app.route('/admin/generate-notifications', methods=['POST'])
@admin_required
def generate_notifications():
    """Manually trigger notification generation (admin only)"""
    success = db.create_due_date_notifications(session['organization_id'])
    
    if success:
        flash('Due date notifications generated successfully!', 'success')
    else:
        flash('Failed to generate notifications.', 'error')
    
    return redirect(request.referrer or url_for('dashboard'))

############################## Daily Report Routes
@app.route('/daily-reports')
@login_required
def daily_reports():
    """Show daily reports page based on user role and project access"""
    user_role = session['user_role']
    org_id = session['organization_id']
    user_id = session['user_id']
    
    # Use the enhanced method that considers project access
    reports = db.get_daily_reports_for_user_role(user_id, org_id, user_role)
    
    return render_template('daily_reports/list.html', reports=reports, user_role=user_role)

@app.route('/daily-reports/new', methods=['GET', 'POST'])
@login_required
def new_daily_report():
    """Create new daily report"""
    if request.method == 'POST':
        data = {
            'user_id': session['user_id'],
            'organization_id': session['organization_id'],
            'project_id': request.form.get('project_id') or None,
            'report_date': request.form['report_date'],
            'work_title': request.form['work_title'],
            'work_description': request.form['work_description'],
            'status': request.form['status'],
            'discussion': request.form['discussion'],
            'visible_to_manager': 'visible_to_manager' in request.form,
            'visible_to_admin': 'visible_to_admin' in request.form
        }
        
        try:
            report_id = db.create_daily_report(data)
            if report_id:
                flash('Daily report submitted successfully!', 'success')
                return redirect(url_for('daily_reports'))
            else:
                flash('Failed to submit daily report.', 'error')
        except Exception as e:
            flash(f'Error submitting report: {str(e)}', 'error')
    
    # Get current user info and available projects for the form
    user = db.get_user_by_id(session['user_id'])
    projects = db.get_user_projects(session['user_id'], session['organization_id'])
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('daily_reports/new.html', user=user, projects=projects, today=today)

@app.route('/daily-reports/<int:report_id>')
@login_required
def view_daily_report(report_id):
    """View a specific daily report"""
    user_id = session['user_id']
    org_id = session['organization_id']
    user_role = session['user_role']  # Get user role from session
    
    report = db.get_daily_report_by_id(report_id, user_id, org_id, user_role)
    
    if not report:
        flash('Daily report not found or access denied.', 'error')
        return redirect(url_for('daily_reports'))
    
    return render_template('daily_reports/view.html', report=report)

@app.route('/daily-reports/filter', methods=['POST'])
@login_required
def filter_daily_reports():
    """Filter daily reports by date range"""
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    user_role = session['user_role']
    org_id = session['organization_id']
    user_id = session['user_id']
    
    if not start_date or not end_date:
        flash('Please select both start and end dates.', 'error')
        return redirect(url_for('daily_reports'))
    
    # Get all reports for the user role first, then filter by date
    all_reports = db.get_daily_reports_for_user_role(user_id, org_id, user_role)
    
    # Filter by date range
    filtered_reports = []
    for report in all_reports:
        if report['report_date']:
            report_date = report['report_date']
            if isinstance(report_date, str):
                report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
            elif hasattr(report_date, 'date'):
                report_date = report_date.date()
            
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            if start_date_obj <= report_date <= end_date_obj:
                filtered_reports.append(report)
    
    return render_template('daily_reports/list.html', 
                         reports=filtered_reports, 
                         user_role=user_role,
                         start_date=start_date,
                         end_date=end_date)

# Profile Management Routes
@app.route('/profile')
@login_required
def view_profile():
    """View user profile"""
    user_id = session['user_id']
    user = db.get_user_by_id(user_id)
    
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('profile/view.html', user=user)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    user_id = session['user_id']
    user = db.get_user_by_id(user_id)
    
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        avatar_file = request.files.get('avatar')
        
        # Basic validation
        if not first_name or not last_name or not email:
            flash('First name, last name, and email are required.', 'error')
            return render_template('profile/edit.html', user=user)
        
        # Check if email is already taken by another user
        existing_user = db.get_user_by_email(email)
        if existing_user and existing_user['id'] != user_id:
            flash('Email is already taken by another user.', 'error')
            return render_template('profile/edit.html', user=user)
        
        try:
            # Update user profile
            success = db.update_user_profile(user_id, first_name, last_name, email, phone)
            avatar_url = None
            if avatar_file and avatar_file.filename:
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filename = secure_filename(f"user_{user_id}_" + avatar_file.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                avatar_file.save(save_path)
                # Store relative URL to serve via static endpoint
                avatar_url = url_for('serve_avatar', filename=filename)
                db.update_user_avatar(user_id, avatar_url)
            
            if success:
                flash('Profile updated successfully!', 'success')
                # Update session data
                session['user_name'] = f"{first_name} {last_name}"
                session['user_email'] = email
                if avatar_url:
                    session['avatar_url'] = avatar_url
                return redirect(url_for('view_profile'))
            else:
                flash('Failed to update profile. Please try again.', 'error')
        except Exception as e:
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('profile/edit.html', user=user)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    user_id = session['user_id']
    user = db.get_user_by_id(user_id)
    
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if not current_password or not new_password or not confirm_password:
            flash('All password fields are required.', 'error')
            return render_template('profile/change_password.html', user=user)
        
        if new_password != confirm_password:
            flash('New password and confirm password do not match.', 'error')
            return render_template('profile/change_password.html', user=user)
        
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long.', 'error')
            return render_template('profile/change_password.html', user=user)
        
        try:
            # Verify current password
            if not bcrypt.checkpw(current_password.encode('utf-8'), user['password'].encode('utf-8')):
                flash('Current password is incorrect.', 'error')
                return render_template('profile/change_password.html', user=user)
            
            # Hash new password
            new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            # Update password in database
            success = db.update_user_password(user_id, new_password_hash.decode('utf-8'))
            
            if success:
                flash('Password changed successfully!', 'success')
                return redirect(url_for('view_profile'))
            else:
                flash('Failed to change password. Please try again.', 'error')
        except Exception as e:
            flash(f'Error changing password: {str(e)}', 'error')
    
    return render_template('profile/change_password.html', user=user)

@app.route('/debug-session')
def debug_session():
    """Debug route to check session data"""
    return {
        'session_data': dict(session),
        'user_id': session.get('user_id'),
        'user_email': session.get('user_email'),
        'user_created_at': session.get('user_created_at')
    }

# Serve uploaded avatars
@app.route('/uploads/avatars/<path:filename>')
def serve_avatar(filename):
    from flask import send_from_directory
    directory = app.config['UPLOAD_FOLDER']
    return send_from_directory(directory, filename)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    print(f"\n🚀 Starting {config.APP_NAME} v{config.APP_VERSION}")
    print(f"📊 Database: {config.DB_CONFIG['host']}:{config.DB_CONFIG['database']}")
    
    # Initialize database on first run
    try:
        db.init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("\n💡 Please check your database configuration in config.py:")
        print(f"   - Host: {config.DB_CONFIG['host']}")
        print(f"   - User: {config.DB_CONFIG['user']}")
        print(f"   - Password: {'*' * len(config.DB_CONFIG['password']) if config.DB_CONFIG['password'] else '(empty)'}")
        print(f"   - Database: {config.DB_CONFIG['database']}")
        print("\n🔧 Make sure MySQL is running and credentials are correct.")
        exit(1)
    
    print(f"\n🌐 Server starting on http://localhost:5000")
    print("\n📋 Demo credentials:")
    print("   Admin:   admin@demo.com / admin")
    print("   Manager: manager@demo.com / manager")
    print("   Member:  member@demo.com / member")
    print("\n" + "="*50)
    
    app.run(debug=config.DEBUG, host='0.0.0.0', port=5000)
