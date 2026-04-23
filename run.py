"""
Entry point for running the Flask application.
Initializes the app using the factory pattern and starts the development server.
"""
from app import create_app

# Create the Flask app instance using the application factory
app = create_app()

# Run the application only when this file is executed directly
if __name__ == "__main__":
    # Start the Flask development server
    # debug=True enables auto-reload and provides detailed error messages
    app.run(debug=True)