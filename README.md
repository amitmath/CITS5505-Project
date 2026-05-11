## Agile Project Management Web Application

### Team Members

| UWA ID    | Name              | Github Name                      |
|-----------|-------------------|----------------------------------|
| 24910402  | Dulya Murage      | https://github.com/DulyaMur      |
| 24762506  | Amit Mathew       | https://github.com/amitmath      |
| 24173567  | MeiHui Chen       | https://github.com/CheMiui       |
| 24858187  | Naveen Kumar Babu | https://github.com/naveenswa     |

### Overview

This application is a Flask-based Agile project management system designed to help teams manage projects, sprints, tasks, and team collaboration efficiently.

The system allows users to:

- Create and manage projects
- Assign users to projects
- Manage Sprints
- Track tasks and their status (todo, in progress, done)
- View project progress calculated dynamically based on tasks
- Manage user profiles
- Navigate through project backlog and detailed views

### Design Approach

The application follows:

- MVC architecture (Flask + Jinja templates)
- Relational database design (SQLite + SQLAlchemy)
- RESTful routing for project and task operations
- Modern UI/UX principles with modals, hover interactions, and responsive layouts

**User Authentication Process:**
- Session-based authentication using Flask sessions
- Passwords hashed using Werkzeug's `generate_password_hash()` for security
- User login/registration on `/auth` endpoint
- User state managed via `session["user_id"]` across requests
- Protected routes redirect unauthenticated users to login page
- Automatic session validation on each request via `load_logged_in_user()` before_request hook
- Session cleared on logout

### Technologies Used

**Backend:** 
- Flask (web framework)
- SQLAlchemy (ORM)
- Flask-Migrate & Alembic (database migrations)
- Python

**Frontend:**
- HTML5
- CSS3
- Bootstrap 5.3.3 (UI framework)
- Jinja2 (template engine)
- JavaScript
- Chart.js 3.9.1 (data visualization and charts)
- Font Awesome 6.5.0 (icons)

**Database:** SQLite

**Version Control:** Git & GitHub

### Prerequisites

Before running the application, make sure the following have been installed:

- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
- **pip** - Python package manager (comes with Python)
- **Git** - For cloning the repository
- A modern web browser (Chrome, Firefox, Safari, or Edge)

### Project Structure

```
CITS5505-Project/
├── app/                          # Main application package
│   ├── __init__.py              # Application factory
│   ├── models.py                # Database models (User, Project, Sprint, Task)
│   ├── routes.py                # API endpoints
│   ├── static/                  # Static files
│   │   ├── css/                 # Stylesheets
│   │   ├── images/              # Image assets
│   │   ├── js/                  # JavaScript files
│   │   └── uploads/             # User uploads (avatars)
│   └── templates/               # HTML templates
│       ├── base.html            # Base template layout
│       ├── auth.html            # Login/Register page
│       ├── dashboard.html       # Dashboard page
│       ├── project.html         # Projects list page
│       ├── project_detail.html  # Individual project view
│       ├── sprints.html         # Sprints management page
│       ├── analytics.html       # Analytics dashboard page
│       ├── profile.html         # User profile page
│       ├── backlog.html         # Project backlog page
│       └── components/          # Reusable template components
├── migrations/                  # Database migration files (Alembic)
├── config.py                    # Application configuration
├── run.py                       # Entry point to run the application
├── seed_db.py                   # Script to populate sample data
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

### How to Run the Application

1. Clone the repository

```bash
git clone https://github.com/amitmath/CITS5505-Project.git
cd CITS5505-Project
```

2. Set up environment variables

```bash
cp .env.example .env
```

Then open `.env` and set a secret key (generate one with):
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

3. Install Dependencies

```bash
pip install -r requirements.txt
```

4. Set up the database

```bash
flask --app run.py db upgrade
```

5. Seed sample data (optional)

```bash
python seed_db.py
```

6. Run the Application

```bash
python run.py
```

7. Then open your browser and navigate to:

```
http://127.0.0.1:5000
```

### App Navigation Guide

**Home Page (`/`)**
- Landing page for new visitors
- Links to login/register

**Authentication (`/auth`)**
- User login page
- User registration page
- Navigate from: Home page or when accessing protected pages

**Dashboard (`/dashboard`)**
- Main hub after login
- Shows active projects, assigned tasks, and active sprint summary
- Navigate from: Sidebar menu or after login

**Projects (`/project`)**
- View all active projects
- Create new projects
- Manage project team members
- Navigate to: Project detail by clicking on a project card

**Project Detail (`/projects/<id>`)**
- View individual project information
- See project tasks and team members
- Edit project details
- Assign/remove users from project
- Navigate from: Projects list
- Navigate to: Project Backlog by clicking "View Backlog" button

**Project Backlog (`/projects/<id>/backlog`)**
- View all tasks in the project backlog
- Add, Edit or View Tasks
- Manage tasks (todo, in progress, done status)
- Navigate from: Project detail page or from sidebar Menu

**Sprints (`/sprints`)**
- View all sprints (active, planned, completed)
- Create new sprints
- Activate/complete sprints
- View sprint health and velocity
- Navigate from: Sidebar menu Sprints

**Analytics (`/analytics`)**
- Comprehensive dashboard with real-time performance metrics
- **Key Metrics:** Total tasks, Completed tasks, Active sprints, Team members
- **Sprint Velocity Chart:** Visualize completed vs planned story points across sprints
- **Task Distribution Chart:** Breakdown of tasks by status (Done, In Progress, To Do, Backlog)
- **Team Workload Chart:** Task and story point distribution across team members
- **Priority Distribution Chart:** Visual breakdown of task priorities (Low, Medium, High)
- **Project Progress Chart:** Completion percentage for each active project
- **Active Sprints Summary:** Real-time metrics for current sprint performance
- All data is generated from the database with no placeholder data
- Charts update dynamically based on project activities
- Responsive design optimized for all screen sizes
- Navigate from: Sidebar menu Analytics

**Profile (`/profile`)**
- View and edit user profile information
- Update personal details (title, bio, location, timezone, avatar)
- Navigate from: Sidebar menu

**Logout**
- Click logout option in the top navigation
- Clears session and returns to login page

### License

This project is part of the CITS5505 Agile Development course at the University of Western Australia (UWA).
