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
