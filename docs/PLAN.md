# HandballDay: build plan

A matchday platform for real handball clubs. A fan picks a club and a fixture, buys a ticket, optionally adds a custom jersey, and pays once through Stripe (test mode). The ticket becomes a QR code that club staff scan at the door.

Stack: FastAPI + SQLAlchemy 2 + PostgreSQL, React (Vite). Reused from the lab scaffold; its plaintext-password auth is replaced in M1.

Data: the Romanian Liga Florilor 2026/27, 14 clubs, seeded from the HandballManager repo (see section 5).

Source of truth for grading: the criteria below come from the summary in `Site-DAW/docs/BAREM.md`. The original `Barem_evaluare_proiect_web.md` was not available, so compare this table against it before M1.

Legend: ⬜ not started · 🟡 partial · ✅ done

## 1. Use cases (barem 2.02 needs ≥4)

| UC | Actor | What happens |
|---|---|---|
| UC1 Browse | guest | List clubs and upcoming fixtures, open a fixture, see zones, prices and seats left |
| UC2 Account | guest | Register, log in, log out |
| UC3 Buy ticket | fan | Choose fixture and zone, pay with Stripe, get a QR ticket in "My tickets" |
| UC4 Design jersey | fan | Pick club template, colours, name, number, upload a logo, preview live, add to the same checkout |
| UC5 Manage fixtures | club staff | Create and edit fixtures, set zone prices and quotas |
| UC6 Scan ticket | club staff | Validate a QR code at the door; a used ticket is rejected |
| UC7 Administer | admin | Manage clubs and users, moderate uploads, read the activity log |

## 2. Barem mapping

| # | Criterion | Milestone | How we satisfy it | Status |
|---|---|:-:|---|:-:|
| 2.01 | DB in 3NF | M0 | Schema in section 4, written up in `docs/DATABASE.md` with an ER diagram; price snapshots on line items justified there | ✅ |
| 2.02 | ≥4 use cases | M2–M5 | UC1–UC7 above (UC1 and UC2 done) | 🟡 |
| 2.03 | MVC / Repository | M0 | `models/`, `repositories/` (with `IRepository`), `services/`, `routers/` (controllers), React pages as views | ✅ |
| 2.04 | Images, text, tables, links | M2 | Club pages, fixture tables, nav and footer links, club colours, logo and club badges (SVG; real crests stay out of the repo) | ✅ |
| 3.01 | ≥3 classes | M0 | Models, repositories, services, errors, gateways | ✅ |
| 3.02 | ≥1 interface | M3 | `IRepository`, `PaymentGateway` (Stripe and fake implementations), `FileValidator` (`ImageValidator`) | ✅ |
| 3.03 | Authentication | M1 | Email + argon2 hash, signed HttpOnly session cookie | ✅ |
| 3.04 | Authorization | M1 | Roles fan / staff / admin, dependency `require_role(...)`, ownership checks on tickets, orders and designs, staff limited to their own club | ✅ |
| 4.01 | Inheritance | M0 | Repositories extend a base, errors extend `AppError`, models extend mixins | ✅ |
| 4.02 | ≥2 exception types | M1 | `AppError` family (validation, auth, forbidden, not found, conflict, payment) mapped to JSON by handlers | ✅ |
| 4.03 | Image carousel | M2 | Home carousel of upcoming matches: autoplay, pause, arrows, dots, swipe, keyboard, reduced-motion aware | ✅ |
| 4.04 | Animation | M2, M4 | Existing flow background, page transitions, jersey preview recolouring live | ✅ |
| 5.01 | ≥2 CSS files, ≥10 properties | M2 | Split `styles.css` into `variables`, `base`, `layout`, `components`, `pages`, `animations` | ✅ |
| 5.02 | Responsive | M2 | Mobile-first, breakpoints near 600 and 1024 px, screenshots at 390 / 768 / 1440 px in `docs/screenshots/` | ✅ |
| 6.01 | ≥5 unit tests | M1+ | pytest from M1 on, target 40+; a few Vitest tests for the jersey and carousel logic | 🟡 |
| 6.02 | Git | M0 | This repo; small commits per task | 🟡 |
| 6.03 | GitHub Actions CI | M0 | Backend tests against a Postgres service container, frontend lint and build | 🟡 |
| 7.01 | Activity log file | M1, M3, M5 | `backend/logs/activity.log`, rotating; register, login, failures, orders, scans, admin actions; viewer in admin panel | 🟡 |
| 7.02 | Hosting | M6 | Apache VPS or equivalent, see decision D3 | ⬜ |
| 8.01 | Lighthouse SEO ≥90 | M2, M6 | Per-page title, meta description, canonical, `robots.txt`, `sitemap.xml`, alt text, crawlable links; measured on the deployed site | 🟡 |
| 8.02 | Stripe payments | M3 | Hosted Checkout Session in test mode, webhook with signature check, idempotent fulfilment; a test-card purchase was run end to end | ✅ |
| 9.01 | CSRF | M1 | Double-submit token middleware plus SameSite=Lax, tested | ✅ |
| 9.02 | XSS | M2, M5 | React escaping only (no `dangerouslySetInnerHTML`), strict CSP, jersey text restricted to a safe character set, test with `<script>` payloads | 🟡 |
| 9.03 | SQL injection | M1 | ORM only, bound parameters, Pydantic validation, test with `' OR 1=1 --` | ✅ |
| 9.04 | Max 12 MB upload | M4 | Reject by `Content-Length` and again while streaming, so a lying header can't bypass it | ✅ |
| 9.05 | Allowed extensions | M4 | Whitelist png / jpg / jpeg / webp, checked on name and on real file content | ✅ |
| 10.01 | Rate limiting | M5 | slowapi: strict on login, register and checkout, loose elsewhere | ⬜ |
| 10.02 | CAPTCHA | M5 | Cloudflare Turnstile (free, has test keys) on register, login and jersey upload | ⬜ |
| 10.03 | Steganography protection | M4 | Decode, strip metadata, resize and re-encode every upload to lossy WebP; original is discarded | ✅ |
| 10.04 | Security headers grade A | M5, M6 | CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy; graded on the live site | ⬜ |
| 10.05 | `.htaccess` | M6 | SPA fallback, `/api` proxy, compression, caching, headers, HTTPS redirect | ⬜ |

## 3. Milestones

Each milestone ends with tests passing and a commit. Sizes: S ≈ an evening, M ≈ a few evenings, L ≈ a week.

### M0: Foundations (S) ✅ built, CI not yet seen green
- Restructure `backend/app/` into `models/`, `repositories/`, `services/`, `routers/`, `schemas/`, `security/`, `errors.py`.
- Move `config.py` to environment-based classes (dev / test / prod).
- Models for the schema in section 4, `IRepository` base, seed script with the 14 Liga Florilor clubs (section 5).
- Test setup: pytest, a `handballday_test` database created per run.
- CI workflow: backend tests with Postgres service, frontend lint and build.
- Frontend: put the standard `vite` scripts back in `package.json` (the `&` workaround is no longer needed), switch to `react-router`, split the CSS.
- Write `docs/DATABASE.md` and a real `README.md`.

Done when: `pytest` and CI are green on an empty-ish app and `npm run dev` works from the new folder.

### M1: Auth and access control (M) ✅ built; frontend route guards moved to M3
- argon2 password hashing, register / login / logout / me, signed HttpOnly session cookie, `Secure` in production.
- CSRF middleware and a `GET /api/csrf` endpoint; the frontend sends `X-CSRF-Token`.
- Role dependencies, ownership helpers, `AppError` handlers.
- Activity logger (rotating file).
- Frontend: register form (reuse `AuthForm` and the eye toggle), route guards (UX only; the server is the real check). Guards wait for M3, when the first staff page exists to guard.
- Tests: wrong password, duplicate email, CSRF rejected, guest 401, fan 403 on staff routes, SQL-injection input.

Done when: barem 3.03, 3.04, 4.02, 9.01, 9.03 have a test each and the plaintext path is gone.

### M2: Clubs, fixtures, public site (M) ✅ built; Lighthouse SEO is measured in M6, Vitest tests not added
- Endpoints and pages: club list, club page, fixture list with filters, fixture detail with zones and seats left.
- Home page: carousel of upcoming matches; keep the "Something is taking shape" hero as the landing.
- SEO component (title, description, canonical), `robots.txt`, `sitemap.xml` (served by the backend from the database, `PUBLIC_URL` sets the host).
- Responsive pass and screenshots at three widths (`docs/screenshots/`).

Done when: a guest can browse everything (UC1), and 2.04, 4.03, 5.01, 5.02 have proof.

### M3: Tickets, Stripe, QR, staff tools (L) ✅ built and checked with a real Stripe test purchase; no camera scanning
- `PaymentGateway` interface with `StripeGateway` and `FakeGateway` (used in tests).
- Checkout: create an order and a Stripe Checkout Session; webhook `checkout.session.completed` verifies the signature and issues tickets once (idempotent on the session id).
- Capacity is enforced inside one transaction, so two fans can't take the last seat.
- Ticket code = unguessable random token; QR rendered from it. "My tickets" page.
- Staff pages: create and edit fixtures and zone prices (UC5), scan page (UC6) that validates and marks a ticket used. Start with a code field, add camera scanning last.
- Local webhook testing with `stripe listen`.

Done when: a test-card purchase yields a QR ticket, the same ticket scans once and is rejected the second time, 3.02 and 8.02 have proof.

### M4: Jersey studio and uploads (L) ✅ built; starting from a real player's name is not done
- Jersey templates as SVG with CSS variables; live preview as the fan changes colours, name and number.
- Name and number validated to a safe character set and length.
- Upload pipeline: 12 MB cap, extension whitelist, content check with Pillow, then decode and re-encode to lossy WebP with metadata stripped (10.03). Random stored filenames, stored under `backend/uploads/` and served through a route, never executed.
- Jersey lines join the same order and Stripe session as tickets.
- Pickup at the match the jersey was bought for (D2): each jersey line points at a fixture, so there is no address handling.
- Optional, cheap: let the fan start from a real player of that club (name and number from the roster) or type a custom one.

Done when: a fan buys a ticket plus a jersey in one payment, and 4.04, 9.04, 9.05, 10.03 have tests (oversize file, `.exe` renamed to `.png`, file with a payload appended).

### M5: Hardening and admin (M)
- slowapi rate limits with 429 responses and a test.
- Turnstile on register, login and upload (test keys locally).
- Security headers middleware, tuned so Stripe redirect and the SPA still work.
- Admin panel: clubs, users and roles, upload moderation, activity log viewer (UC7).
- XSS test with script payloads in the jersey name and the display name.

Done when: 10.01, 10.02, 9.02, 7.01 have proof and a full pass through the app produces a readable activity log.

### M6: Deploy and prove it (M)
- Host on a server with Apache `mod_rewrite`, `mod_proxy`, `mod_headers` and HTTPS (D3).
- `.htaccess` for SPA fallback, `/api` proxy, compression, caching, HTTPS redirect, headers.
- Production env vars, Stripe webhook pointed at the public URL.
- Run Lighthouse (SEO ≥90) and a security-headers scan (grade A); fix what they flag.
- Fill `docs/BAREM.md` with a proof link per criterion, take screenshots, a green CI run, a short demo script for the oral exam.

Done when: every row in section 2 is ✅ with proof.

### M7 (optional): HandballManager kit export
Only if time remains. Export a jersey design as a small JSON file the game can import. Depends on how the game stores kits; read that code first (not checked yet).

## 4. Database (3NF draft)

Money is stored as integer bani/cents. Orders have no stored total: it is computed from line items. Line items keep a price snapshot, because the price at purchase time must not change when a fixture is later repriced.

| Table | Key columns |
|---|---|
| `roles` | id, name (fan / staff / admin) |
| `users` | id, email (unique), display_name, password_hash, role_id → roles, club_id → clubs (nullable, staff only), created_at |
| `leagues` | id, name, country |
| `venues` | id, name, city, address |
| `clubs` | id, league_id, venue_id, name, slug (unique), city, founded_year, description, primary_color, secondary_color |
| `players` (optional, M2) | id, club_id, first_name, last_name, position, shirt_number, nationality |
| `zones` | id, venue_id, name, capacity (unique on venue + name) |
| `fixtures` | id, home_club_id, away_club_id, venue_id, kickoff_at, status |
| `fixture_zones` | fixture_id, zone_id, price_bani, quota (PK on the pair) |
| `orders` | id, user_id, status, created_at, paid_at |
| `payments` | id, order_id, provider, provider_ref (unique), amount_bani, status |
| `tickets` | id, order_id, fixture_id, zone_id, code (unique), price_bani, status, used_at, scanned_by → users |
| `jersey_templates` | id, name, svg_key |
| `uploads` | id, user_id, stored_name, mime, size_bytes, created_at |
| `jersey_designs` | id, user_id, club_id, template_id, primary_color, secondary_color, name_text, number, logo_upload_id → uploads (nullable) |
| `jersey_items` | id, order_id, design_id, fixture_id (pickup match), size, price_bani |

The activity log is a file (barem 7.01), not a table.

## 5. Decisions and seed data

| # | Decision | Status |
|---|---|---|
| D1 | League and clubs | **Decided:** Liga Florilor 2026/27, all 14 clubs, real data from the HandballManager repo |
| D2 | Jersey delivery | **Decided:** pickup at the match the jersey is bought for |
| D3 | Hosting | **Open.** Build locally first and decide before M6. Check the original barem for whether 7.02 is required for your target grade |
| D4 | Solo project accepted | **Decided:** yes. Still compare this plan with the original `Barem_evaluare_proiect_web.md` |

### Seed data (from `D:\Github Desktop\HandballManager`)

| What | Source | Note |
|---|---|---|
| Name, city, founded year, stadium, capacity, description | `HandballManager.Core/Data/InitialData2026/LigaFlorilor/*.json` | 14 files, one per club |
| Kit colours (primary, secondary) | `HandballManager.Core/Engine2D/KitColours.Generated.cs` and the overrides in `KitColours.cs` | Extracted from club crests by a script, so treat as approximate; Târgu Mureș is hand-corrected. Galați has a colour entry but is not in the 2026/27 data |
| Players (optional) | `docs/season-2026-27/LigaFlorilor/roster.csv` | Import name, position, shirt number, nationality only; birthdates are not needed |
| Fixtures | not in the data | Generate a double round robin (14 clubs, 26 rounds) from the club list, with kickoff dates in the near future. Label it demo data |
| Ticket zones | not in the data | Split each stadium capacity into 3 zones (for example 20 / 50 / 30 %) with different prices |

The clubs are Minaur Baia Mare, CSM Corona Brașov, SCM Universitatea Craiova, CSM București, CSM Iași 2020, CSM Târgu Mureș, CSU Știința București, Dunărea Brăila, Gloria Bistrița, SCM Râmnicu Vâlcea, Rapid București, CSM Slatina, CSM Târgu Jiu and HC Zalău.

## 6. Known risks

- **Scope:** M3 and M4 are each a week of work. If time runs short, drop M4's logo upload only after 9.04, 9.05 and 10.03 have a home elsewhere, because those criteria need an upload feature to exist. The cheapest fallback is a club-supporter avatar upload.
- **Real clubs:** names and facts are fine for a course project. Keep crest images and player photos out of the repo (the game's colour data is already derived from crests), draw generic jerseys in the club colours, and show an "unofficial student project, Stripe test mode" notice. This matters more if the site goes public.
- **Google Play:** do not link ticket purchases to in-game rewards without reading the store's billing policy first.
- **Steganography:** re-encoding to lossy WebP defeats appended data and LSB payloads in practice, but is a mitigation, not a proof. Say so at the oral exam.
- **Stripe locally:** webhooks need `stripe listen` running; without it the order stays pending.
