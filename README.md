# Overcomers | SLE (Flask)

Production-ready Flask web app for Overcomers | SLE:
- Public marketing pages
- Apply + Contact forms (stored in PostgreSQL)
- Optional email notifications via SMTP
- Auth (login/signup) + simple admin page for applications

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
flask --app wsgi:app run --debug
```

## Render setup

1) Create a **PostgreSQL** database in Render.
2) In the **Web Service** env vars, set:
   - `DATABASE_URL` = the Render Postgres **External Database URL** (or Internal if you only access from Render)
   - `SECRET_KEY` = long random string

3) (Optional) Email notifications: set the SMTP env vars from `.env.example`.

Start command:
`gunicorn --bind 0.0.0.0:$PORT wsgi:app`
