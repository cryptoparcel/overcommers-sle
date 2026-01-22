# OVERCOMERS | SLE — UI + Flask Backend

This repo includes:
- Frontend UI (templates + static assets)
- Backend: auth (login/register), Apply form (stored in DB), Admin dashboard
- Admin-managed homepage settings (including YouTube “video of the day”)

## Local run
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# mac/linux: source .venv/bin/activate
pip install -r requirements.txt

export SECRET_KEY="dev"
export DATABASE_URL="sqlite:///local.db"
python app.py
```

Open http://localhost:5000

## Create the first admin (recommended)
Set these env vars once, then start the app:
- `BOOTSTRAP_ADMIN_EMAIL`
- `BOOTSTRAP_ADMIN_PASSWORD`

```bash
export BOOTSTRAP_ADMIN_EMAIL="admin@overcomerssle.com"
export BOOTSTRAP_ADMIN_PASSWORD="ChangeThisPassword123!"
python app.py
```

Then:
- `/login` to log in
- `/admin` to manage applications + homepage settings

## Render deployment
1) Create a Render **Web Service** from this repo
2) Add a **Postgres** database
3) Set env vars:
- `SECRET_KEY`
- `DATABASE_URL` (from Render Postgres)
- optional bootstrap vars above

This repo also includes `render.yaml`.

## Optional spam protection (Cloudflare Turnstile)
Set:
- TURNSTILE_SITE_KEY
- TURNSTILE_SECRET_KEY

## Optional email notifications (SMTP)
Set:
- SMTP_HOST
- SMTP_PORT
- SMTP_USER
- SMTP_PASSWORD
- SMTP_FROM
- ADMIN_NOTIFY_EMAIL
