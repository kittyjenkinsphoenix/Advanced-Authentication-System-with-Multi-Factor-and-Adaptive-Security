Advanced Authentication System With Multi‑Factor And Adaptive Security

## Overview

This project is a production‑ready Flask application that delivers a secure authentication system with adaptive protections and Multi‑Factor Authentication (MFA). It combines strong password handling, progressive lockout and CAPTCHA, TOTP‑based MFA, rate limiting, CSRF protection, secure session cookies, reverse‑proxy awareness, and structured logging.

Key goals:

- Reduce account takeover risk with layered defenses
- Provide clear, auditable security events
- Be deployable behind HTTPS and a reverse proxy

For a visual end‑to‑end flow, see `AUTHENTICATION_FLOW.md`.

## Features

- Password authentication with secure hashing (Werkzeug)
- Progressive protections:
  - CAPTCHA required after 3 failed attempts
  - Account lockout for 5 minutes after 5 failed attempts
- TOTP‑based MFA (Google Authenticator/Authy compatible) with QR setup
- Rate limiting on login (7 requests per minute per IP)
- CSRF protection on all forms (Flask‑WTF)
- Secure sessions (HttpOnly, SameSite=Lax, Secure cookies)
- Reverse proxy support via ProxyFix (honors X‑Forwarded‑For/Proto)
- Structured JSON logging with rotating files and UTC timestamps

## Tech Stack

- Python 3.x, Flask 3.x
- Flask‑Login, Flask‑WTF, Flask‑SQLAlchemy, Flask‑Limiter
- pyotp (TOTP), qrcode/Pillow (QR generation)
- SQLite (default), configurable via `DATABASE_URL`

## Repository Structure

```text
app/
  __init__.py        # App factory, extensions, logging, ProxyFix
  models.py          # SQLAlchemy models (User)
  routes.py          # All routes: login, MFA setup/verify, dashboard, logout
  templates/         # Jinja2 templates (base, login, dashboard, MFA views)
config.py            # Hardened settings; env‑driven secrets/keys
run.py               # Launch app and create initial DB
reset_db.py          # Reset and seed the database
AUTHENTICATION_FLOW.md
NAMING_CONVENTION_UPDATES.md
README.md
```

## Configuration

Configuration is centralized in `config.py` and is environment‑driven for sensitive values.

Environment variables (recommended in production):

- `SECRET_KEY` — Strong secret used for sessions/CSRF
- `RECAPTCHA_PUBLIC_KEY` — Your Google reCAPTCHA site key
- `RECAPTCHA_PRIVATE_KEY` — Your Google reCAPTCHA secret key
- `DATABASE_URL` — Optional; overrides default SQLite (e.g., `postgresql+psycopg://...`)

Security‑oriented defaults (already set):

- `DEBUG = False`, `TESTING = False`
- `SESSION_COOKIE_SECURE = True`, `REMEMBER_COOKIE_SECURE = True`
- `SESSION_COOKIE_HTTPONLY = True`, `REMEMBER_COOKIE_HTTPONLY = True`
- `SESSION_COOKIE_SAMESITE = 'Lax'`, `REMEMBER_COOKIE_SAMESITE = 'Lax'`
- `PREFERRED_URL_SCHEME = 'https'`

Proxy/HTTPS awareness:

- The app enables `ProxyFix` to honor `X‑Forwarded‑For` and `X‑Forwarded‑Proto` from a reverse proxy (e.g., Nginx). Ensure your proxy sets these headers.

## Quick Start (Windows PowerShell)

1) Create and activate a virtual environment (optional but recommended)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

1) Install dependencies

```powershell
pip install -r requirements.txt
```

1) Set required environment variables (use your real keys)

```powershell
# Strong secret key (example generated via Python: secrets.token_hex(32))
$env:SECRET_KEY = "<64-hex-characters>"

# Google reCAPTCHA keys
$env:RECAPTCHA_PUBLIC_KEY  = "<your-site-key>"
$env:RECAPTCHA_PRIVATE_KEY = "<your-secret-key>"

# Optional: database URL (if not using default SQLite)
# $env:DATABASE_URL = "postgresql+psycopg://user:pass@host:5432/dbname"
```

1) Initialize or reset the database (creates tables and seeds sample users)

```powershell
python reset_db.py
```

1) Run the application (serve over HTTPS in production)

```powershell
python run.py
```

Visit <https://localhost:5000> (behind a reverse proxy/HTTPS in production). Note: Secure cookies require HTTPS in browsers.

## Default Seed Users

When you run `reset_db.py`, three sample users are created with passwords set via secure hashing:

- `admin` / `admin123`
- `user1` / `letmein`
- `user2` / `welcome123`

On first successful login without MFA, you’ll be guided through MFA setup.

## Authentication Flow (Summary)

1. User submits username/password
2. If 3+ failures: show CAPTCHA; if 5+ failures: lock account for 5 minutes
3. If password OK and MFA enabled: prompt for TOTP
4. If password OK and no secret yet: guide through MFA setup with QR
5. On success: rotate session, log event, redirect to dashboard

See `AUTHENTICATION_FLOW.md` for a full diagram and details.

## Logging

- Rotating file at `logs/auth.log` (1MB, 5 backups)
- UTC timestamps
- JSON structured events (e.g., `login_success`, `password_failure`, `account_lockout`, `invalid_totp`, `logout`)
- Includes `username` and client IP (honors `X‑Forwarded‑For`)

## Security Notes

- Always deploy behind HTTPS; Secure cookies won’t be sent over HTTP
- Use a strong, rotated `SECRET_KEY` in production
- Provide real reCAPTCHA keys for CAPTCHA enforcement
- Consider external rate‑limit storage (Redis) for multi‑instance deployments
- Back up `instance/` database or use a managed DB in production

## Troubleshooting

- CAPTCHA not rendering: verify `RECAPTCHA_PUBLIC_KEY` and `RECAPTCHA_PRIVATE_KEY` are set in the environment
- Cookies not persisting in dev: Secure cookies require HTTPS; test with a proxy/SSL terminator or disable Secure flags only in a controlled dev environment
- Proxy IPs not shown: verify your reverse proxy sets `X‑Forwarded‑For`/`X‑Forwarded‑Proto`

## Conventions

- Project intentionally uses camelCase for variables and Title Case for user‑facing text. See `NAMING_CONVENTION_UPDATES.md` for details.

## License

This project is provided under the terms of the LICENSE file included in this repository.
