## Development

1. Install Required Packages
pip install flask flask_sqlalchemy flask_migrate

2. Run the Application
python run.py

This will:

Start the Flask development server
Automatically create the SQLite database (agilepm.db)
Create all tables (via db.create_all())

3. Seed the Database (Insert Sample Data)
python seed_db.py

This will:

Populate the database with initial/sample data
Skip insertion if data already exists (if implemented in seed script)
