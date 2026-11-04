# HandballDay

A matchday platform for Romanian women's handball (Liga Florilor 2026/27). A fan picks a club and a fixture, buys a ticket, optionally adds a custom jersey, and pays once through Stripe (test mode). The ticket becomes a QR code that club staff scan at the door.

> Unofficial student project (DAW course). Stripe runs in test mode only; fixtures and prices are demo data.

Build plan and grading map: [docs/PLAN.md](docs/PLAN.md). Database: [docs/DATABASE.md](docs/DATABASE.md).

## Stack

FastAPI, SQLAlchemy 2, PostgreSQL, React (Vite).

```
backend/app/
  models/         SQLAlchemy tables (mixins in base.py)
  repositories/   IRepository interface + SQL implementations
  services/       business rules; own the transaction
  routers/        HTTP controllers
  schemas/        Pydantic request/response models
  security/       password hashing
  seed/           demo data (clubs.json, fixtures, zones)
  errors.py       AppError family, mapped to JSON
  config.py       dev / test / prod settings (APP_ENV)
frontend/src/     React views; styles/ holds the five CSS files
```

## Run it locally

Needs Python 3.12, Node 22 and a running PostgreSQL.

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
# first time only: copy .env.example to .env (it overwrites an existing .env) and set DB_PASSWORD
python -m app.seed            # creates the database, tables and demo data
python run.py                 # API on http://localhost:3000
```

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173, proxies /api to the backend
```

## Accounts and roles

Registering makes a `fan` and logs you in (signed HttpOnly session cookie). Every POST needs the `X-CSRF-Token` header from `GET /api/csrf`; the frontend does this itself. To make staff or an admin (until the admin panel in M5):

```bash
python -m app.set_role you@example.com admin
python -m app.set_role you@example.com staff rapid-bucuresti
```

Security events (register, login, failed login, logout, forbidden, CSRF rejection) go to `backend/logs/activity.log`, rotating at 1 MB.

## Tests

```bash
cd backend && pytest          # uses the handballday_test database, rebuilt on every run
cd frontend && npm run lint && npm run build
```

GitHub Actions runs both on every push and pull request (`.github/workflows/ci.yml`).
