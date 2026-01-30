# Patch Log

Generated: 2026-01-30 10:32:22

## Changes

- **app/blueprints/auth.py** — Import ProfileForm, PasswordChangeForm to prevent /auth/account NameError
- **app/blueprints/public.py** — Remove duplicate /admin/applications route from public blueprint to avoid route collision
- **app/blueprints/admin.py** — Add @login_required to /admin/page-builder so logged-out users are redirected to login instead of 403
- **app/templates/admin/stories.html** — Add CSRF token hidden inputs to admin story moderation POST forms
- **app/__init__.py** — Gate db.create_all() behind BOOTSTRAP_DB=1 to avoid unintended prod DB mutations
- **app/utils.py** — Remove duplicate module that conflicts with app/utils/ package imports
- **.gitignore** — Add standard ignores for caches, env files, IDE metadata
- **__pycache__** — Remove cached bytecode directories from the packaged project

## Notes
- If you are deploying to production, do **not** set `BOOTSTRAP_DB=1`. Use migrations (`flask db upgrade`) and only run `flask bootstrap-db` once if you need the default layouts seeded.
