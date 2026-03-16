# Tango Finance

Tango Finance is a Django web application for personal transaction tracking with multi-currency support, AI-assisted input, and admin-side risk monitoring.

## What This Project Implements
- User authentication (custom email-based user model)
- Transaction CRUD with ownership checks
- Category management per user
- Multi-currency transactions with GBP normalization
- AI-assisted transaction recording endpoints
- OTP-protected sensitive account operations
- Audit logs for transaction lifecycle events
- Risk alerts for abnormal expense behavior
- Admin ban/unban (soft disable, no data deletion)

## Architecture Summary
- `finance/views.py`: web views (dashboard/profile/OTP flows)
- `finance/api_views.py`: REST endpoints
- `finance/services/transactions.py`: shared transaction business logic
- `finance/services/risk.py`: heuristic + optional LLM risk scoring
- `finance/models.py`: domain models (`Transaction`, `Category`, `AuditLog`, `RiskAlert`)
- `finance/templates/` + `finance/static/`: frontend templates and assets

## Requirements
- Python 3.12
- Django 6.0.1
- Dependencies in `requirements.txt`

## Setup
```bash
conda activate tango-finance
cd /Users/hutianze/Django-finance/django_finances
pip install -r requirements.txt
```

Create `.env` in project root.

## Environment Variables
| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | none | Django secret key |
| `DEBUG` | No | `True` | Debug mode |
| `GROQ_API_KEY` | No | none | AI chat + optional LLM risk |
| `CF_TURNSTILE_SECRET_KEY` | No | none | Turnstile server validation |
| `ENABLE_LLM_RISK` | No | `False` | Enable LLM-enhanced risk scoring |
| `DATABASE_URL` | No (local), Yes (Render) | none | Production PostgreSQL connection |
| `ALLOWED_HOSTS` | No | `127.0.0.1,localhost` | Comma-separated host allowlist |
| `CSRF_TRUSTED_ORIGINS` | No | none | Comma-separated trusted HTTPS origins |
| `REDIS_URL` | No | none | Optional Redis cache backend |

## Run
```bash
python manage.py migrate
python manage.py runserver
```

- App: `http://127.0.0.1:8000/finance/`
- Admin: `http://127.0.0.1:8000/admin/`

## Test
```bash
python manage.py check
python manage.py test
```

Current baseline: **19 tests passing**.

## CI
GitHub Actions workflow runs on push/PR:
- install dependencies
- migrate
- `manage.py check`
- `manage.py test`

Workflow file: `.github/workflows/ci.yml`

## Render Deployment
This repository includes `render.yaml` and `build.sh` for one-click Render setup.

### Option A: Blueprint deploy (recommended)
1. Push this repository to GitHub.
2. In Render dashboard, choose **New +** -> **Blueprint**.
3. Select this repository.
4. Render will create:
   - Web service: `tango-finance`
   - PostgreSQL database: `tango-finance-db`
5. After first deploy, set required secrets in Render:
   - `GROQ_API_KEY` (optional if using AI chat)
   - `CF_TURNSTILE_SECRET_KEY` (optional)
   - `REDIS_URL` (optional)
6. Open the web URL and test `/finance/` and `/admin/`.

### Option B: Manual web service
If not using Blueprint, create a Python web service and set:
- Build command: `./build.sh`
- Start command: `gunicorn django_finances.wsgi:application`

## Replit Deployment
This repository includes:
- `.replit`
- `scripts/replit_start.sh`

Steps:
1. Import the GitHub repo into Replit.
2. Add Secrets:
   - `DJANGO_SECRET_KEY` (required)
   - `DEBUG=False`
   - `ALLOWED_HOSTS=<your-replit-domain>,127.0.0.1,localhost`
   - `CSRF_TRUSTED_ORIGINS=https://<your-replit-domain>`
   - `CF_TURNSTILE_SECRET_KEY` (required for OTP/captcha flows)
   - Optional: `GROQ_API_KEY`, `ENABLE_LLM_RISK`
3. Click **Run**. Replit will install dependencies, run migrations, collect static files, and start Gunicorn on `$PORT`.

## API Endpoints (Authenticated)
- `POST /finance/api/agent/transaction/`
- `POST /finance/api/chat/`

## Security and Integrity Controls
- POST + CSRF for destructive operations
- Soft-ban via `is_active=False` (no record deletion)
- `transaction.atomic()` on critical write paths
- Transaction type canonicalization to `Income`/`Expense`
- Structured API error responses
- User-facing error pages for 400/403/404/500

## Admin Features
- Users: list/search/filter + ban/unban actions
- Transactions: searchable/filterable records
- Audit logs: read-only action trace
- Risk alerts: severity/score/status/source overview
- Admin “View site” points to `/finance/`

## Known Limitations
- Development email backend is console-based by default.
- Exchange-rate API may fail without network; fallback rates are used.
- LLM risk scoring is optional and off by default (`ENABLE_LLM_RISK=False`).
- Redis is configured as cache backend in settings; tests use local in-memory cache overrides where needed.

## Quick Verification Checklist
1. Register/login with a test account.
2. Add income and expense transactions in different currencies.
3. Confirm monthly net balance updates correctly.
4. Open admin and verify Risk Alerts and user ban/unban actions.
5. Run `python manage.py test` and confirm all tests pass.

## Recent Changes (This Submission)
- Introduced service-layer transaction logic.
- Added DRF serializers for API request validation.
- Added CI pipeline (`check + test`).
- Added risk alert model and scoring service.
- Hardened API/web error handling and security flows.
- Standardized runtime UI text to English.
