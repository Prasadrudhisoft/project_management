# Branding Configuration
# Easily customize your application's branding by modifying these settings

# Company Information
COMPANY_NAME = "Rudhisoft"  # Change this to your company name
APP_NAME = "RudhiManage"  # Full application name
TAGLINE = "made by razi and om "

# Contact Information
SUPPORT_EMAIL = "rudhisoft@gmail.com"  # Change to your support email
SALES_EMAIL = "sales@projectpro.com"      # Change to your sales email
PHONE_NUMBER = "+1 (555) 123-4567"        # Change to your phone number

# Website URLs (if you have existing website/social media)
WEBSITE_URL = "https://www.projectpro.com"
BLOG_URL = "https://blog.projectpro.com"
LINKEDIN_URL = "https://linkedin.com/company/projectpro"
TWITTER_URL = "https://twitter.com/projectpro"

# Branding Colors (CSS Custom Properties)
BRAND_COLORS = {
    'primary': '#2563eb',       # Main brand color (blue)
    'primary_dark': '#1d4ed8',  # Darker shade of primary
    'primary_light': '#dbeafe', # Lighter shade of primary
    'secondary': '#64748b',     # Secondary color (gray)
    'accent': "#10b951",        # Accent color (green)
    'warning': '#f59e0b',       # Warning color (orange)
    'danger': '#ef4444',        # Danger color (red)
}

# Logo Configuration
LOGO_ICON = "fas fa-project-diagram"  # FontAwesome icon class
LOGO_TEXT = COMPANY_NAME              # Text next to logo

# Hero Section Content
HERO_TITLE = "Transform Your Project Management Experience"
HERO_SUBTITLE = "Streamline workflows, boost team productivity, and deliver projects on time with our comprehensive project management platform designed for modern teams."

# Statistics (displayed in hero section)
HERO_STATS = {
    'users': {'number': '10K+', 'label': 'Active Users'},
    'projects': {'number': '50K+', 'label': 'Projects Completed'},
    'uptime': {'number': '99.9%', 'label': 'Uptime'},
    'rating': {'number': '4.9★', 'label': 'User Rating'}
}

# Features Section
FEATURES_TITLE = "Powerful Features for Modern Teams"
FEATURES_SUBTITLE = "Everything you need to manage projects efficiently, collaborate seamlessly, and deliver exceptional results."

FEATURES_LIST = [
    {
        'icon': 'fas fa-tasks',
        'color': 'blue',
        'title': 'Task Management',
        'description': 'Create, assign, and track tasks with ease. Set priorities, deadlines, and dependencies to keep your projects moving forward.'
    },
    {
        'icon': 'fas fa-users',
        'color': 'green',
        'title': 'Team Collaboration',
        'description': 'Foster seamless collaboration with real-time messaging, file sharing, and team workspaces that keep everyone connected.'
    },
    {
        'icon': 'fas fa-chart-line',
        'color': 'purple',
        'title': 'Progress Tracking',
        'description': 'Monitor project progress with visual dashboards, milestone tracking, and comprehensive reporting tools.'
    },
    {
        'icon': 'fas fa-calendar-alt',
        'color': 'orange',
        'title': 'Smart Scheduling',
        'description': 'Intelligent scheduling with automated reminders, deadline tracking, and resource allocation optimization.'
    },
    {
        'icon': 'fas fa-shield-alt',
        'color': 'red',
        'title': 'Enterprise Security',
        'description': 'Bank-grade security with role-based access control, data encryption, and compliance with industry standards.'
    },
    {
        'icon': 'fas fa-mobile-alt',
        'color': 'indigo',
        'title': 'Mobile Ready',
        'description': 'Access your projects anywhere with our responsive design and mobile-optimized interface for on-the-go productivity.'
    }
]

# Call-to-Action Section
CTA_TITLE = "Ready to Transform Your Workflow?"
CTA_SUBTITLE = f"Join thousands of teams who trust {COMPANY_NAME} to deliver their most important projects."

# Footer Information
FOOTER_DESCRIPTION = "Empowering teams to achieve more through intelligent project management solutions."

# Navigation Menu Items
NAV_ITEMS = [
    {'name': 'Features', 'url': '#features'},
    {'name': 'Pricing', 'url': '#pricing'},
    {'name': 'About', 'url': '#about'},
    {'name': 'Contact', 'url': '#contact'}
]

# Footer Links
FOOTER_LINKS = {
    'Product': [
        {'name': 'Features', 'url': '#features'},
        {'name': 'Pricing', 'url': '#pricing'},
        {'name': 'Security', 'url': '#security'},
        {'name': 'Integrations', 'url': '#integrations'}
    ],
    'Company': [
        {'name': 'About Us', 'url': '#about'},
        {'name': 'Careers', 'url': '#careers'},
        {'name': 'Blog', 'url': BLOG_URL if 'blog.' in BLOG_URL else '#blog'},
        {'name': 'Press', 'url': '#press'}
    ],
    'Support': [
        {'name': 'Help Center', 'url': '#help'},
        {'name': 'Documentation', 'url': '#docs'},
        {'name': 'Community', 'url': '#community'},
        {'name': 'Contact Us', 'url': '#contact'}
    ]
}

# SEO Meta Information
META_DESCRIPTION = f"Professional project management solution by {COMPANY_NAME}. Streamline your projects, boost team productivity, and achieve your goals with our comprehensive platform."
META_KEYWORDS = "project management, task management, team collaboration, productivity, workflow, project tracking"

# Button Text Customization
BUTTON_TEXT = {
    'get_started': 'Get Started',
    'start_trial': 'Start Free Trial',
    'watch_demo': 'Watch Demo',
    'contact_sales': 'Contact Sales',
    'login': 'Login',
    'register': 'Sign Up'
}

# Additional Customization Options
CUSTOM_CSS_OVERRIDES = """
/* Add any custom CSS overrides here */
/* Example: Change primary color gradient */
/*
:root {
    --primary-color: #your-color;
    --primary-dark: #your-darker-color;
}
*/
"""

# Enable/Disable Sections
SHOW_SECTIONS = {
    'hero_stats': True,
    'features': True,
    'cta': True,
    'footer': True,
    'animated_counters': True,
    'smooth_scroll': True
}
