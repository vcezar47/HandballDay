# Deploying HandballDay

The barem's hosting criterion (7.02, 0,50 pt) says only that the site is **published and reachable online; even one HTML page is enough**. This folder is for the fuller setup: Apache serving the built app over HTTPS and proxying `/api` to the backend. That setup is also the only way to show the two criteria that need a web server (10.05 `.htaccess`, and a real HSTS header for 10.04).

## What you need

- A Linux server you control (Ubuntu 22.04 or newer is assumed): 1 GB of memory is enough.
- A name that points at it, with ports 80 and 443 open. A free provider name (for example an Azure `*.cloudapp.azure.com` name) works for Let's Encrypt.

## First setup (once)

```bash
sudo apt update
sudo apt install -y apache2 postgresql python3-venv git certbot python3-certbot-apache
# Node 22 from NodeSource (or nvm), then:
sudo a2enmod rewrite proxy proxy_http headers deflate expires ssl

sudo useradd --system --create-home --shell /usr/sbin/nologin handballday
sudo git clone https://github.com/vcezar47/HandballDay.git /opt/handballday
sudo chown -R handballday:handballday /opt/handballday

# database
sudo -u postgres psql -c "CREATE USER handballday WITH PASSWORD 'CHOOSE-ONE';"
sudo -u postgres psql -c "CREATE DATABASE handballday OWNER handballday;"
```

Then, as the `handballday` user: copy `backend/.env.production.example` to `backend/.env` and fill in every value (it explains each one), and run `./deploy/deploy.sh` to build everything once.

As root:

```bash
cp deploy/apache-vhost.conf /etc/apache2/sites-available/handballday.conf   # edit YOUR.DOMAIN.EXAMPLE
cp deploy/apache-hardening.conf /etc/apache2/conf-available/handballday-hardening.conf
cp deploy/handballday.service /etc/systemd/system/
a2ensite handballday && a2enconf handballday-hardening && a2dissite 000-default
systemctl daemon-reload && systemctl enable --now handballday
certbot --apache -d YOUR.DOMAIN.EXAMPLE
systemctl reload apache2
```

In the Stripe dashboard (test mode) add a webhook endpoint `https://YOUR.DOMAIN.EXAMPLE/api/webhooks/stripe` for `checkout.session.completed` and `checkout.session.expired`, and put its signing secret in `backend/.env`, then `systemctl restart handballday`. Create real Turnstile keys for the domain in Cloudflare and put them in the same file.

Later updates: `./deploy/deploy.sh`.

## Checks that are the proof for the barem

```bash
# 10.05: private files are refused, the listing is off, unknown pages still load the app
curl -I https://YOUR.DOMAIN.EXAMPLE/.env             # 403
curl -I https://YOUR.DOMAIN.EXAMPLE/.git/config      # 403
curl -I https://YOUR.DOMAIN.EXAMPLE/assets/          # 403 or 404, never a file list
curl -I https://YOUR.DOMAIN.EXAMPLE/clubs            # 200 (the app)
curl -I https://YOUR.DOMAIN.EXAMPLE/assets/nope.js   # 404, not an HTML page
curl -I http://YOUR.DOMAIN.EXAMPLE/                  # 301 to https

# 10.04: look at the headers, then run the Security Headers Inspector extension on the page
curl -sI https://YOUR.DOMAIN.EXAMPLE/ | grep -i -E "strict-transport|content-security|x-frame|x-content|referrer|permissions"

# 10.01: the 101st request inside a minute is blocked
for i in $(seq 1 105); do curl -s -o /dev/null -w "%{http_code} " https://YOUR.DOMAIN.EXAMPLE/api/health; done
```

Run Lighthouse (Chrome DevTools, "SEO" category) on `/`, `/clubs`, `/fixtures` and one fixture page, and keep a screenshot of each score. Locally the production build scores 100 on all four.

## Without a server of your own

- **Only 7.02 (0,50 pt)**: publish the built `frontend/dist` as a static site (GitHub Pages, for example). The pages load; data and payments need the backend, so this proves hosting but not the rest.
- **10.05 and 10.04 without a server**: both can be demonstrated on your own machine with Apache in a container, see below; say so at the exam.

## Trying the `.htaccess` on your own machine (needs Docker Desktop running)

```bash
cd frontend && npm run build && cd ..
docker run --rm -p 8080:80 \
  -v "$PWD/frontend/dist:/usr/local/apache2/htdocs:ro" \
  -v "$PWD/deploy/httpd-test.conf:/usr/local/apache2/conf/httpd.conf:ro" httpd:2.4
```

Then `curl -I http://localhost:8080/.env` and the other checks above (replace the address; HSTS is not sent over plain HTTP, and the `/api` proxy needs the backend reachable at 127.0.0.1:3000 inside the container, so it is not part of this local test).

## What your decision changes (see also `docs/BAREM.md`)

| Barem row | Points | Needs a live site? |
|---|:-:|---|
| 7.02 hosting | 0,50 | Yes, but only "something published and reachable" |
| 8.01 Lighthouse SEO ≥ 90 | 0,50 | Measured locally already (100); redo on the live URL for the screenshot |
| 10.04 headers, grade A | 0,20 | The grade is read from the page you hand in; HSTS exists only over HTTPS |
| 10.05 `.htaccess` | 0,20 | Needs Apache, local or hosted |
