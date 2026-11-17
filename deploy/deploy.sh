#!/usr/bin/env bash
# Update a running server to the latest main. Run as the handballday user from /opt/handballday:
#   ./deploy/deploy.sh
# Needs: git, python3-venv, node 22, and sudo rights for restarting the service.
set -euo pipefail
cd "$(dirname "$0")/.."

git pull --ff-only

echo "== backend"
cd backend
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install --quiet -r requirements.txt
mkdir -p logs uploads
APP_ENV=prod .venv/bin/python -m app.seed   # idempotent: only adds what is missing
cd ..

echo "== frontend"
cd frontend
npm ci --silent
npm run build   # writes dist/, which Apache serves, .htaccess included
cd ..

echo "== restart"
sudo systemctl restart handballday
sleep 2
curl -fsS http://127.0.0.1:3000/api/health && echo " <- API is up"
