import os
# load_dotenv reads the .env file and injects its values into os.environ
from dotenv import load_dotenv

# absolute path to the project root directory
basedir = os.path.abspath(os.path.dirname(__file__))

# load environment variables from .env before Config reads them
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    """
    Base configuration for the Flask application.
    Stores app settings such as the secret key and database connection.
    """

    # Secret key used by Flask for session management and security features
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")

    # Database URI:
    # use DATABASE_URL from environment if available
    # otherwise, fall back to a local SQLite database file
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        "sqlite:///" + os.path.join(basedir, "agilepm.db")

    # disable SQLAlchemy's event system for object modifications
    SQLALCHEMY_TRACK_MODIFICATIONS = False