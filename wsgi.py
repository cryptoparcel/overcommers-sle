
# Entry point for Gunicorn / production
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app
app = create_app()
