# Overcomers | SLE

A premium, structured sober-living / supportive-housing website built with Flask.

## Features

- Public pages: Home, What We Do, Resources, Impact, Shop, Contact, Apply
- Accounts: signup/login, account settings, logout
- Admin area (admins only):
  - Applications
  - Contact messages
  - Stories (approve / reject / delete)
  - Users
  - Page Builder (homepage blocks)
  - **Openings** (create & publish “Upcoming Openings” listings)

## Local setup (easy)

1) Create a virtualenv and install deps:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
```

2) Set environment variables (example):

```bash
# Windows PowerShell
$env:FLASK_APP="manage.py"
$env:FLASK_ENV="development"
$env:SECRET_KEY="change-me"
$env:DATABASE_URL="sqlite:///app.db"
$env:BOOTSTRAP_DB="1"
```

3) Run the app:

```bash
flask run
```

On first boot (with `BOOTSTRAP_DB=1`) it will create tables + seed starter content.

## Making yourself admin

1) Create an account on the site (Signup)
2) In a terminal, run:

```bash
flask make-admin your@email.com
```

Now you’ll see the **Admin** link in the navbar when you’re logged in.

## Openings (Upcoming Openings)

- Admin → Openings → “New opening”
- Set **Status = Published** to show it on `/openings`
- Recommended: leave **Hide pricing publicly** checked (pricing is shared after application)

## Deploying (Render)

- Set `DATABASE_URL` to your Render Postgres URL
- Set `SECRET_KEY` to a strong random string
- Set `BOOTSTRAP_DB=1` only once for the first deploy, then remove it
