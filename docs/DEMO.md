# Demo script for the oral exam (about 10 minutes)

## Before you start

1. PostgreSQL running; `cd backend && python -m app.seed` (fixtures are dated from the day you seed, so seed on the day of the exam).
2. Backend `python run.py`, frontend `npm run dev` (or `npm run build && npm run preview` to show the real CSP).
3. `stripe listen --events checkout.session.completed,checkout.session.expired --forward-to localhost:3000/api/webhooks/stripe` in its own terminal, with its `whsec_` secret in `backend/.env`.
4. Three accounts (register them in the site, then give two a role):
   ```bash
   python -m app.set_role fan@example.com fan
   python -m app.set_role staff@example.com staff minaur-baia-mare
   python -m app.set_role admin@example.com admin
   ```
5. Open `backend/logs/activity.log` in a tab, and the repo's Actions page (green runs).

## The walk-through

| Minute | Show | Say / point at |
|---|---|---|
| 0 | Home page, carousel (arrows, pause, swipe in the phone view) | Barem 4.03, 4.04. Responsive: resize to 390 px (5.02) |
| 1 | Clubs, a club page, fixtures with filters, a fixture with seats left | UC1, tables, images, links (2.04). View page source: title and description per page (8.01, Lighthouse 100) |
| 2 | Sign up: the CAPTCHA widget, then log in | 3.03, CAPTCHA 10.02; passwords are argon2 hashes |
| 3 | Fixture page as the fan: pick a zone, add a **jersey** (recolour live, name, number, upload a logo), pay with `4242 4242 4242 4242` | UC3 + UC4, Stripe 8.02. The webhook line in the Stripe terminal, then "My tickets" with the QR and the jersey |
| 5 | Log in as staff: edit a price, then **Scan tickets**: scan the code once (valid), again (rejected) | UC5, UC6, authorization 3.04: a fan opening `/staff` is sent away, and the API answers 403 |
| 6 | Log in as admin: change a role, delete the uploaded logo, read the Activity tab | UC7; the log file in the other tab shows the same events (7.01) |
| 7 | Security: in the browser console `fetch('/api/auth/login', {method: 'POST'})` shows 403 (CSRF 9.01); try an `.exe` renamed `.png` and a 13 MB file (9.04, 9.05); 11 quick wrong logins give 429 (10.01) | See the test names in [`BAREM.md`](BAREM.md) for each |
| 9 | `cd backend && pytest`, then the green Actions page | 6.01, 6.03 |

## Questions to expect, and short answers

- **Why is it in 3NF?** No column depends on another non-key column; the price copied onto a ticket is a recorded fact (what was paid), not a copy of the current price. Details in `docs/DATABASE.md`.
- **How do two people not buy the last seat?** Checkout locks the zone's row, counts the seats and inserts the pending tickets in one transaction; an unpaid hold expires after 35 minutes. Proven with two real connections.
- **How do you know a payment is genuine?** Only the signed webhook issues tickets; the amount must match the order, and a replay changes nothing.
- **What does the WebP re-encode protect against?** Metadata, appended bytes and low-bit hidden data do not survive; it is a mitigation, not a mathematical guarantee.
- **What is CSRF and how is it stopped?** A signed token in a cookie that must be echoed in a header; another site can make the browser send the cookie but cannot read the token.
- **What would you change for many users?** Rate-limit counters would move from memory to Redis, and uploads from local disk to object storage.
