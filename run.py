"""Local development entrypoint.

Why this file exists:
- On deployments (e.g. Render/Gunicorn), we import the Flask app from wsgi.py.
- A top-level file named `app.py` would shadow the `app/` package and break imports.

Run locally:
  python run.py
or
  flask --app wsgi run --debug
"""

from app import create_app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
