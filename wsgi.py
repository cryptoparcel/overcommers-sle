# Entry point for Gunicorn / production
from app import create_app
app = create_app()
