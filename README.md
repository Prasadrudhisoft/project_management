# Project Manager - Complete Solution

A comprehensive project management web application built with Flask and MySQL, featuring modern UI design, multi-role support, and advanced team management capabilities.

## 🚀 Features

### Core Functionality
- **Multi-tenant Organization Support** - Separate organizations with isolated data
- **Role-Based Access Control** - Admin, Manager, and Member roles with different permissions
- **Project Management** - Create, edit, and track projects with visibility controls
- **Task Management** - Assign tasks, set priorities, due dates, and track completion
- **Milestone Tracking** - Organize tasks into project milestones
- **Internal Messaging** - Communication system between team members
- **Notifications** - Real-time alerts for task assignments and updates
- **Comments System** - Task-level discussions and updates

### Advanced Team Management (NEW)
- **Team Assignments Overview** - Admin dashboard showing all team member project assignments
- **Smart Member Assignment** - Visual display of current project assignments when managing teams
- **Auto-Unassignment** - Automatic removal of team members when projects are completed
- **Assignment Visibility** - Clear indication of team member workload and availability
- **Project Completion Workflow** - Streamlined process for project closure

### Technical Features
- **Responsive Design** - Works on desktop, tablet, and mobile devices
- **Modern UI** - Bootstrap 5 with custom styling and animations
- **Secure Authentication** - Support for both bcrypt and SHA-256 password hashing
- **Database Optimization** - Proper indexing and foreign key relationships
- **Clean Architecture** - Modular code structure with separation of concerns
- **Enhanced Navigation** - Dropdown menus for better organization of features

## 📋 Requirements

- Python 3.8+
- MySQL 8.0+ or MariaDB 10.3+
- Web browser with JavaScript enabled

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone [repository-url]
cd simple-project-manager
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup

#### Create Database
```sql
-- Connect to MySQL as root user
mysql -u root -p

-- Run the database schema file
source DATABASE_SCHEMA.sql;
```

The schema file will create:
- Database: `project_management_app`
- All necessary tables with proper relationships
- Sample data for testing

### 5. Environment Configuration

Create a `.env` file in the project root:
```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=project_management_app

# Application Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Application Settings
APP_NAME=Project Manager
APP_VERSION=3.0
```

### 6. Run the Application

#### Development Mode
```bash
python app.py
```

#### Production Mode
```bash
python start_production.py
```

#### Using WSGI (Recommended for Production)
```bash
gunicorn --bind 0.0.0.0:8000 wsgi:app
```

The application will be available at `http://localhost:5000` (development) or `http://localhost:8000` (production).

## 👥 Default Login Accounts

After running the database schema, you can login with these accounts:

| Role | Email | Password | Description |
|------|-------|----------|--------------|
| Admin | admin@demo.com | password123 | Full system access |
| Manager | manager@demo.com | password123 | Project management access |
| Member | member@demo.com | password123 | Basic user access |

## 📁 Project Structure

```
simple-project-manager/
├── app.py                    # Main application file
├── wsgi.py                   # WSGI entry point
├── config.py                 # Configuration settings
├── branding_config.py        # UI branding configuration
├── start.py                  # Development server
├── start_production.py       # Production server
├── DATABASE_SCHEMA.sql       # Complete database schema
├── requirements.txt          # Python dependencies
├── requirements-production.txt # Production dependencies
├── Dockerfile               # Docker container setup
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore file
├── README.md                # This file
├── utils/
│   ├── __init__.py
│   └── db_helper.py         # Database utility functions
├── templates/               # HTML templates
│   ├── base.html           # Base template with enhanced navigation
│   ├── dashboard.html      # Main dashboard
│   ├── manager_dashboard.html
│   ├── member_dashboard.html
│   ├── landing.html        # Landing page
│   ├── team_assignments_overview.html  # Team assignments dashboard
│   ├── auth/               # Authentication templates
│   ├── projects/           # Project management templates
│   │   └── team_members.html  # Enhanced team member management
│   ├── tasks/              # Task management templates
│   ├── milestones/         # Milestone templates
│   ├── messages/           # Messaging templates
│   ├── notifications/      # Notification templates
│   ├── users/              # User management templates
│   ├── reports/            # Reports templates
│   └── errors/             # Error page templates
└── static/                 # Static files (CSS, JS, images)
```

## 🎯 Usage Guide

### For Administrators
- **User Management**: Create and manage user accounts
- **System Overview**: View organization-wide statistics
- **Project Oversight**: Access to all projects and tasks
- **Role Assignment**: Assign roles to users
- **Team Assignments Overview**: View comprehensive dashboard of all team member project assignments
- **Assignment Analytics**: Monitor workload distribution across team members

### For Managers
- **Project Creation**: Create and configure new projects
- **Smart Team Management**: Add/remove members with visibility into their current assignments
- **Task Assignment**: Create and assign tasks to team members
- **Progress Tracking**: Monitor project and task progress
- **Milestone Management**: Create and track project milestones
- **Project Completion**: Close projects with automatic team member unassignment

### For Members
- **Task Management**: View and update assigned tasks
- **Project Participation**: Collaborate on assigned projects
- **Communication**: Send messages and add comments
- **Status Updates**: Update task progress and completion
- **Assignment Visibility**: See your project assignments clearly displayed

## 🔧 Configuration Options

### Database Configuration
Modify the database connection in `config.py` or use environment variables.

### Branding Customization
Update `branding_config.py` to customize:
- Application name and logo
- Color schemes
- Footer information
- Custom CSS styles

### Feature Toggles
Enable/disable features by modifying the configuration files.

## 🐳 Docker Deployment

```bash
# Build the image
docker build -t project-manager .

# Run the container
docker run -p 8000:8000 --env-file .env project-manager
```

## 🔒 Security Features

- **Password Security**: Support for bcrypt and SHA-256 hashing
- **Session Management**: Secure session handling
- **Role-Based Access**: Different permission levels
- **SQL Injection Protection**: Parameterized queries
- **XSS Protection**: Template auto-escaping
- **CSRF Protection**: Built-in Flask-WTF protection

## 🚀 Production Deployment

1. **Server Setup**: Use a production WSGI server like Gunicorn or uWSGI
2. **Database**: Use a dedicated MySQL/MariaDB server
3. **Reverse Proxy**: Configure Nginx or Apache as reverse proxy
4. **SSL Certificate**: Enable HTTPS with SSL certificates
5. **Environment Variables**: Use production-specific configurations
6. **Monitoring**: Set up application and server monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the documentation in the code comments
- Review the database schema comments
- Examine the example configurations
- Create an issue in the repository

## 🔄 Version History

- **v3.1** - Advanced Team Management Features (Latest)
  - Team Assignments Overview dashboard for admins
  - Smart team member assignment with current project visibility
  - Auto-unassignment of team members from completed projects
  - Enhanced navigation with dropdown menus
  - Improved user experience for team management workflows

- **v3.0** - Complete cleanup and consolidation
  - Codebase refactoring and optimization
  - Database schema improvements
  - Enhanced security features

- **v2.1** - Bug fixes and UI improvements
- **v2.0** - Enhanced features and responsive design
- **v1.0** - Initial release

---

**Built with ❤️ using Flask, MySQL, and Bootstrap**
