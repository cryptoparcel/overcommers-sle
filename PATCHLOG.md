# Patch Log

Generated: 2026-02-08

## Round 2 — full working cleanup

### Removed dead files
- `app/utils.py` — conflicted with `app/utils/` package (Python can't resolve both)
- `app/emailer.py` — duplicate of `app/utils/mailer.py`
- `app/login.py` — duplicate user_loader already in `app/__init__.py`
- 10 orphan templates not routed to: `admin_dashboard.html`, `admin_applications.html`, `admin_settings.html`, `login.html`, `register.html`, `privacy.html`, `terms.html`, `what_we_do.html`, `_page.html`, `auth/signup.html`
- Root-level static HTML files (`index.html`, `what-we-do.html`, `resources.html`, `impact.html`, `shop.html`, `contact.html`, `careers.html`) and `assets/`, `privacy/`, `terms/` directories — Flask serves everything now

### Fixed bugs
- **XSS in story_detail.html** — replaced `story.body | replace('\n', '<br>') | safe` with `story.body | nl2br` (escapes HTML before converting newlines)
- **nl2br filter** — now uses `markupsafe.escape()` before replacing newlines, returns `Markup` object
- **Page Builder JSON double-encoding** — template used `raw_json|tojson` on a JSON string, causing `JSON.parse()` to return a string instead of an object. Now passes parsed dict as `layout_data` and uses `layout_data|tojson`
- **Empty favicon.ico** — `app/static/assets/favicon.ico` was 0 bytes; copied valid 16K favicon from `app/static/favicon.ico`
- **index.html missing container** — "Programs, classes & support" section lacked `<div class="container">` wrapper, causing full-width bleed on that section

### Cleaned up config
- Removed dead `AUTO_CREATE_DB` config option (was never referenced in code)
- Rewrote README with correct setup flow: `flask db upgrade` → `flask bootstrap-db` → `flask make-admin`
- Removed incorrect `BOOTSTRAP_DB` environment variable references from README

## Round 1 (original patches)

- **app/blueprints/auth.py** — Import ProfileForm, PasswordChangeForm to prevent /auth/account NameError
- **app/blueprints/public.py** — Remove duplicate /admin/applications route from public blueprint
- **app/blueprints/admin.py** — Add @login_required to /admin/page-builder
- **app/templates/admin/stories.html** — Add CSRF token hidden inputs to admin story moderation POST forms
- **app/__init__.py** — Gate db.create_all() behind BOOTSTRAP_DB=1
- **.gitignore** — Add standard ignores for caches, env files, IDE metadata
