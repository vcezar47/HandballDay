# Barem: where each criterion is proven

Source: `Barem_evaluare_proiect_web.pdf` (the course's grading sheet). Nine sections of 1.00 point each (notele 2 to 10); every row below is one line of that sheet, with its points.

Legend: ✅ done and proven · 🟡 done, but its final proof needs the site to be online (see [`deploy/README.md`](../deploy/README.md))

## Nota 2: Funcționalități de bază și arhitectura aplicației (1,00)

| # | Criterion | Pts | Status | Proof |
|---|---|:-:|:-:|---|
| 01 | Database in 3NF | 0,25 | ✅ | [`docs/DATABASE.md`](DATABASE.md): ER diagram, 1NF/2NF/3NF argument, deliberate choices (price snapshots, seat holds). Models in `backend/app/models/` |
| 02 | ≥4 complete use cases | 0,25 | ✅ | UC1 browse (clubs, fixtures, seats left), UC2 account, UC3 buy ticket with Stripe and QR, UC4 design a jersey, UC5 staff create/edit fixtures, UC6 scan ticket, UC7 admin (roles, clubs, uploads, delete, log). Walkthrough in [`docs/DEMO.md`](DEMO.md) |
| 03 | Software architecture (MVC, Repository) | 0,25 | ✅ | `models/` (Model), React pages (View), `routers/` (Controller), plus `repositories/` and `services/`. Example flow: `Fixtures.jsx` → `GET /api/fixtures` → `routers/catalog.py` → `CatalogService` → `FixtureRepository` → `Fixture` |
| 04 | Images, text, tables, links | 0,25 | ✅ | Club badges and logo (SVG), club descriptions, fixture and zone tables, nav/footer links, jersey drawings. Screenshots in [`docs/screenshots/`](screenshots/) |

## Nota 3: POO și controlul accesului (1,00)

| # | Criterion | Pts | Status | Proof |
|---|---|:-:|:-:|---|
| 01 | ≥3 classes | 0,25 | ✅ | 94 classes in `backend/app`: models, repositories, services, schemas, errors, gateways, validators (count: `grep -rh "^class " backend/app \| wc -l`) |
| 02 | ≥1 interface used | 0,25 | ✅ | `IRepository` (every repository), `PaymentGateway` (`StripeGateway`, `FakeGateway`; `backend/app/gateways/payment.py`), `FileValidator` (`ImageValidator`), `CaptchaVerifier` (Turnstile, none) |
| 03 | Authentication | 0,25 | ✅ | Email + argon2 hash, signed HttpOnly session cookie: `routers/auth.py`, `services/auth.py`. Tests: `tests/test_auth.py` |
| 04 | Authorization | 0,25 | ✅ | Roles fan/staff/admin via `require_role`, ownership checks (tickets, uploads, jerseys), staff limited to their club (`ensure_club_staff`). Tests: `tests/test_access.py`, `tests/test_staff.py`, `tests/test_admin.py` (guest 401, wrong role 403) |

## Nota 4: Concepte OOP și elemente interactive (1,00)

| # | Criterion | Pts | Status | Proof |
|---|---|:-:|:-:|---|
| 01 | Inheritance | 0,25 | ✅ | `SqlRepository(IRepository)` and every repository below it; `AppError` and its subclasses; models extend `IdMixin`/`CreatedAtMixin`; `FixtureDetail(FixtureOut)`; `StripeGateway(PaymentGateway)` |
| 02 | ≥2 exception types handled | 0,25 | ✅ | `backend/app/errors.py`: validation, auth, forbidden, not found, conflict, payment, payload too large; one handler turns them into JSON. Rate-limit errors have their own handler |
| 03 | Image carousel | 0,25 | ✅ | `frontend/src/Carousel.jsx` on the home page: autoplay, pause button, arrows, dots, swipe, arrow keys, pauses on hover/focus, off under reduced motion |
| 04 | Animation | 0,25 | ✅ | Flow background, page entrance transition, carousel slide, jersey colours that transition live (`styles/animations.css`, `styles/pages.css`) |

## Nota 5: Stilizare și design responsive (1,00)

| # | Criterion | Pts | Status | Proof |
|---|---|:-:|:-:|---|
| 01 | ≥2 CSS files, ≥10 properties | 0,50 | ✅ | Six files in `frontend/src/styles/` (`variables`, `base`, `layout`, `components`, `pages`, `animations`), well over 10 distinct properties |
| 02 | Responsive (desktop, tablet, phone) | 0,50 | ✅ | Mobile-first, breakpoints at 600 and 1024 px. Screenshots at 390, 768 and 1440 px in [`docs/screenshots/`](screenshots/) |

## Nota 6: Testare și automatizare (1,00)

| # | Criterion | Pts | Status | Proof |
|---|---|:-:|:-:|---|
| 01 | ≥5 unit tests | 0,25 | ✅ | 165 pytest tests in `backend/tests/` (`cd backend && pytest`) |
| 02 | Git | 0,25 | ✅ | `github.com/vcezar47/HandballDay`, one commit per phase |
| 03 | CI/CD (GitHub Actions) | 0,50 | ✅ | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml): backend tests on a Postgres service, frontend lint and build. Green runs on the repo's Actions tab (phases 0 to 4 at the time of writing; the phase 5 run was still queued) |

## Nota 7: Monitorizare și publicare (1,00)

| # | Criterion | Pts | Status | Proof |
|---|---|:-:|:-:|---|
| 01 | Activity log file | 0,50 | ✅ | `backend/logs/activity.log` (rotating, one JSON-safe line per event): register, login and failures, logout, forbidden, CSRF and CAPTCHA rejections, checkout, payments, scans, uploads, role and club changes. Viewer: Admin → Activity. Tests: `tests/test_activity.py`, `tests/test_admin.py` |
| 02 | Hosting | 0,50 | 🟡 | Deployment files are ready (`deploy/`, `frontend/public/.htaccess`). The sheet accepts even one published HTML page. **Needs your hosting decision**, see below |

## Nota 8: Optimizare și servicii externe (1,00)

| # | Criterion | Pts | Status | Proof |
|---|---|:-:|:-:|---|
| 01 | SEO ≥90 on Lighthouse | 0,50 | ✅ | Lighthouse SEO **100** on home, club page, fixture list and fixture page (mobile and desktop), run against the production build; per-page title, description and canonical (`Seo.jsx`), `robots.txt`, `sitemap.xml`, alt text, crawlable links. Re-run on the live URL once it exists (`deploy/README.md`) |
| 02 | Online payments (Stripe) | 0,50 | ✅ | Stripe Checkout in test mode, signed webhook, idempotent fulfilment; a real test-card purchase was run end to end. `backend/app/gateways/payment.py`, `services/orders.py`, `tests/test_orders.py` |

## Nota 9: Securitate, nivelul I (1,00)

| # | Criterion | Pts | Status | Proof |
|---|---|:-:|:-:|---|
| 01 | CSRF | 0,20 | ✅ | Signed double-submit token on every non-GET request: `security/csrf.py`, `tests/test_csrf.py` |
| 02 | XSS | 0,20 | ✅ | React escaping only (a test scans the frontend for `dangerouslySetInnerHTML`, `innerHTML`, `eval`), CSP without `unsafe-inline` scripts, display names and jersey text restricted to a safe character set. `tests/test_xss.py` (script payloads); also tried in the browser with an `<img onerror>` name |
| 03 | SQL injection | 0,20 | ✅ | ORM only, bound parameters, validated input. Tests: `test_auth.py` (`' OR 1=1 --` as password and email), `test_catalog.py` (as a club slug) |
| 04 | Max 12 MB upload | 0,20 | ✅ | Refused by `Content-Length` and again while streaming, so a lying header cannot get past: `routers/jersey.py`; `tests/test_uploads.py` (both paths, 413); checked against the running server |
| 05 | Allowed extensions | 0,20 | ✅ | Only png/jpg/jpeg/webp, checked on the name and on the real content, which must match: `services/uploads.py`; `tests/test_uploads.py` (`.exe` renamed `.png`, `.svg`, `.php`, `.gif`) |

## Nota 10: Securitate, nivelul II (1,00)

| # | Criterion | Pts | Status | Proof |
|---|---|:-:|:-:|---|
| 01 | Rate limiting (100 requests a minute) | 0,20 | ✅ | `backend/app/limits.py`: one budget of 100 requests a minute per visitor across the API (the 101st gets a 429 with `Retry-After`), and stricter limits on login, register, checkout and upload. `tests/test_hardening.py` |
| 02 | CAPTCHA | 0,20 | ✅ | Cloudflare Turnstile on register, login and logo upload, verified on the server and failing closed: `security/captcha.py`; `tests/test_hardening.py` |
| 03 | Steganography protection | 0,20 | ✅ | Every upload is decoded, stripped of metadata, resized and re-encoded as lossy WebP; the original is never stored. `tests/test_uploads.py` (EXIF removed, appended payload gone). A mitigation, not a proof, and the oral exam answer should say so |
| 04 | Security headers, grade A | 0,20 | 🟡 | `nosniff`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, strict CSP, plus HSTS over HTTPS: `security/headers.py` (API) and `frontend/public/.htaccess` (pages); tests keep them in step. The grade itself must be read with the Security Headers Inspector on the page you hand in, and HSTS only exists over HTTPS |
| 05 | `.htaccess` | 0,20 | 🟡 | `frontend/public/.htaccess`: blocks `.env`, `.git`, source, log and config files (403), no directory listing, plus SPA routing, API proxy, compression, caching, headers and the HTTPS redirect. Needs Apache to show the 403s: `deploy/README.md` |

## What the hosting decision still decides

See the end of [`deploy/README.md`](../deploy/README.md): 7.02 (0,50) needs something published; 10.04 (0,20) and 10.05 (0,20) need the pages served by Apache over HTTPS to be shown convincingly.
