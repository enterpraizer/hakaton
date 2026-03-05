#!/usr/bin/env bash
# setup-server.sh — run once on a fresh VPS to prepare for CloudIaaS deployment
# Usage: bash setup-server.sh
set -euo pipefail

echo "==> Installing Docker..."
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER

echo "==> Installing Docker Compose plugin..."
apt-get install -y docker-compose-plugin

echo "==> Creating app directory..."
mkdir -p /opt/cloudiaas
cd /opt/cloudiaas

echo ""
echo "==> Now copy your .env file to /opt/cloudiaas/.env"
echo "    You can use: scp .env user@YOUR_SERVER_IP:/opt/cloudiaas/.env"
echo ""
echo "==> .env must contain:"
cat <<'EOF'
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=cloudiaas
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_ME

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your@gmail.com
EMAIL_PASSWORD=your-app-password

SECRET_KEY=CHANGE_ME_32_CHARS_RANDOM
FRONTEND_URL=https://your-frontend.vercel.app
APP_SECRET_KEY=CHANGE_ME
APP_REFRESH_SECRET_KEY=CHANGE_ME
APP_ALGORITHM=HS256
APP_ACCESS_TOKEN_EXPIRE_MINUTES=30
APP_REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=false

GEMINI_API_KEY=your-gemini-key
EOF

echo ""
echo "✅ Server ready! Push to main branch to trigger auto-deploy."
