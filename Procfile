web: bash -lc "flask db upgrade && gunicorn --workers 2 --threads 2 --timeout 120 wsgi:app"
