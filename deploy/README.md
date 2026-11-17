# Deploying HandballDay

The barem's hosting criterion (7.02, 0,50 pt) says only that the site is **published and reachable online; even one HTML page is enough**. This folder is for the fuller setup: Apache serving the built app over HTTPS and proxying `/api` to the backend. That setup is also the only way to show the two criteria that need a web server (10.05 `.htaccess`, and a real HSTS header for 10.04).

## What you need

- A Linux server you control, **Ubuntu 24.04** (the backend needs Python 3.11 or newer; 22.04 ships 3.10): 1 GB of memory is enough.
- A name that points at it, with ports 80 and 443 open. A free provider name (for example an Azure `*.cloudapp.azure.com` name) works for Let's Encrypt.

## Oracle Cloud Free Tier (the route this project takes)

**Already running another server on Oracle (the HandballManager game server uses Caddy on ports 80 and 443)?** Create a *second* VM for this site and leave the first one alone: two web servers cannot share ports 80/443, and a mistake here must not touch a live game server. Always Free allows two Micro VMs, or an Ampere A1 allowance of 4 cores / 24 GB shared across instances; check Compute → Instances for what the first VM uses. Give this one its own SSH key and its own DuckDNS name:

```powershell
ssh-keygen -t ed25519 -f "$HOME\.ssh\handballday-oracle"
```

Paste the contents of `handballday-oracle.pub` when Oracle asks for the public key, then connect with `ssh -i "$HOME\.ssh\handballday-oracle" ubuntu@NEW_PUBLIC_IP`.

1. **Check the account.** In cloud.oracle.com open Compute → Instances. "Always Free" shapes are `VM.Standard.E2.1.Micro` (AMD, 1 GB) and `VM.Standard.A1.Flex` (ARM, up to 4 cores / 24 GB, often "out of capacity": retry later or pick the Micro). Either runs this app; everything in it has ARM builds.
2. **Create the instance.** Image: Ubuntu **24.04** (not 22.04: its Python is too old). Keep the default network, tick "assign a public IPv4 address", and add your SSH public key (or let Oracle generate one and download it). Connect with `ssh -i KEY ubuntu@PUBLIC_IP`. Do not terminate the instance later: its public IP goes with it. Oracle may reclaim an Always Free instance that sits idle for a week, so open the site once the day before the exam.
3. **Open ports 80 and 443 in two places** (Oracle blocks them twice):
   - Cloud side: Networking → Virtual cloud networks → your VCN → Subnet → Security list → Add ingress rules: source `0.0.0.0/0`, TCP, destination port `80`, and another for `443`.
   - Machine side (Oracle's Ubuntu image ships with iptables rules that reject everything but SSH):
     ```bash
     sudo iptables -I INPUT 1 -m state --state NEW -p tcp --dport 80 -j ACCEPT
     sudo iptables -I INPUT 1 -m state --state NEW -p tcp --dport 443 -j ACCEPT
     sudo netfilter-persistent save
     ```
4. **Get a name.** Oracle gives only an IP, and Let's Encrypt needs a name. Free option: sign in at duckdns.org, create a subdomain (for example `handballday.duckdns.org`) and set its IP to the instance's public IP. Use that name wherever the guide says `YOUR.DOMAIN.EXAMPLE`.
5. **On a 1 GB Micro, add swap and skip building on the server:**
   ```bash
   sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```
   Build the frontend on your own computer (`cd frontend && npm run build`), upload it (this includes the hidden `.htaccess`), and run the deploy script without Node:
   ```bash
   scp -r -i KEY frontend/dist/. ubuntu@PUBLIC_IP:/opt/handballday/frontend/dist/
   SKIP_FRONTEND=1 bash deploy/deploy.sh
   ```
   (Run `mkdir -p /opt/handballday/frontend/dist` on the server first; on the Ampere shape you can build on the server instead and skip this.)
6. Continue with "First setup" below. On Oracle's Ubuntu the sudo user is `ubuntu`, which is "you" in that section; the `handballday` account only runs the API.

## AWS EC2 (alternative to Oracle)

Same app, same "First setup" below; only the cloud steps differ. AWS needs one firewall instead of Oracle's two, and the Ubuntu image has no blocking iptables rules.

1. **Check what you have left:** Billing → Free Tier (credits, and when the free period ends). Set a budget alert first: Billing → Budgets → a small monthly budget (for example 5 USD) with an email alert.
2. **SSH key:** reuse the Windows key from the Oracle section (`ssh-keygen -t ed25519 -f "$HOME\.ssh\handballday-aws"`), then EC2 → Key pairs → Actions → Import key pair and paste the `.pub` file. This avoids the `.pem` permission problems OpenSSH has on Windows.
3. **Launch the instance:** EC2 → Launch instance → Ubuntu Server **24.04** LTS, a type marked "Free tier eligible" (`t3.micro` or `t4g.micro`, both 1 GB), your imported key, 8 to 16 GB disk.
4. **Security group** (in the same wizard): allow SSH (22) from "My IP", HTTP (80) and HTTPS (443) from anywhere.
5. **Fixed address:** EC2 → Elastic IPs → Allocate, then Associate it with the instance (without one the public IP changes whenever the instance is stopped). AWS charges a small hourly fee for public IPv4 addresses unless your free plan covers it, so release it when you are done.
6. **Name:** a DuckDNS subdomain pointing at the Elastic IP, exactly as in the Oracle section. Connect with `ssh -i "$HOME\.ssh\handballday-aws" ubuntu@ELASTIC_IP`.
7. Skip the iptables lines, add the 2 GB swap from the Oracle section (1 GB machines need it), and continue with "First setup".
8. **After the exam:** terminate the instance and release the Elastic IP so nothing keeps billing.

## First setup (once)

```bash
sudo apt update
sudo apt install -y apache2 postgresql python3-venv git certbot python3-certbot-apache
# Node is only needed to build on the server; the recommended route builds on your PC and uploads dist/.
sudo a2enmod rewrite proxy proxy_http headers deflate expires ssl

# you (the sudo user, "ubuntu" on Oracle) own the code and run deployments;
# a separate no-login account runs the API, so a bug in it cannot rewrite the code
sudo useradd --system --no-create-home --shell /usr/sbin/nologin handballday
sudo git clone https://github.com/vcezar47/HandballDay.git /opt/handballday
sudo chown -R "$USER": /opt/handballday

# database
sudo -u postgres psql -c "CREATE USER handballday WITH PASSWORD 'CHOOSE-ONE';"
sudo -u postgres psql -c "CREATE DATABASE handballday OWNER handballday;"
```

Then, as yourself, in this order (the order matters: the service must exist and be able to write its folders before the deploy script restarts it):

```bash
cd /opt/handballday
cp backend/.env.production.example backend/.env && nano backend/.env      # fill in every value; Ctrl+O, Enter, Ctrl+X to save
mkdir -p backend/logs backend/uploads frontend/dist
sudo chown handballday: backend/logs backend/uploads
sudo chgrp handballday backend/.env && sudo chmod 640 backend/.env        # the API reads its settings from here
sudo cp deploy/handballday.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable handballday          # enabled, started by the deploy script
```

Upload the frontend you built on your own computer (`cd frontend && npm run build`, then the `scp` command from the Oracle section, with your key and address), and run `SKIP_FRONTEND=1 bash deploy/deploy.sh` from `/opt/handballday`.

Then wire Apache (replace the name) and get the certificate:

```bash
sudo cp deploy/apache-vhost.conf /etc/apache2/sites-available/handballday.conf
sudo sed -i 's/YOUR.DOMAIN.EXAMPLE/YOURNAME.duckdns.org/' /etc/apache2/sites-available/handballday.conf
sudo cp deploy/apache-hardening.conf /etc/apache2/conf-available/handballday-hardening.conf
sudo a2ensite handballday && sudo a2enconf handballday-hardening && sudo a2dissite 000-default
sudo apache2ctl configtest && sudo systemctl reload apache2
sudo certbot --apache -d YOURNAME.duckdns.org
```

In the Stripe dashboard (test mode) add a webhook endpoint `https://YOUR.DOMAIN.EXAMPLE/api/webhooks/stripe` for `checkout.session.completed` and `checkout.session.expired`, and put its signing secret in `backend/.env`, then `sudo systemctl restart handballday`. Create real Turnstile keys for the domain in Cloudflare and put them in the same file.

Later updates: `bash deploy/deploy.sh`.

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

Then `curl -I http://localhost:8080/.env` and the other checks above (use `http://localhost:8080`; HSTS is not sent over plain HTTP, so it cannot be seen here). To include the `/api` proxy, start the backend on your machine and bridge the container's 127.0.0.1:3000 to it:

```bash
docker run -d --name hd-socat --network container:<apache container name> alpine/socat tcp-listen:3000,fork,reuseaddr tcp:host.docker.internal:3000
```

Then `curl http://localhost:8080/api/health` answers through Apache.

## What your decision changes (see also `docs/BAREM.md`)

| Barem row | Points | Needs a live site? |
|---|:-:|---|
| 7.02 hosting | 0,50 | Yes, but only "something published and reachable" |
| 8.01 Lighthouse SEO ≥ 90 | 0,50 | Measured locally already (100); redo on the live URL for the screenshot |
| 10.04 headers, grade A | 0,20 | The grade is read from the page you hand in; HSTS exists only over HTTPS |
| 10.05 `.htaccess` | 0,20 | Needs Apache, local or hosted |
