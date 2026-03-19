# SMF Lead Capture - Deployment Guide

Complete deployment guide for SMF Works customer zero setup.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Website Integration](#website-integration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

---

## Prerequisites

### Hardware Requirements
- **CPU**: 1 core minimum (2+ recommended)
- **RAM**: 1GB minimum (2GB recommended)
- **Storage**: 10GB minimum
- **OS**: Ubuntu 20.04+ LTS (or 22.04 LTS)

### Required Accounts
1. **Ubuntu VPS** - DigitalOcean, Linode, AWS, or any provider
2. **Domain** - smfworks.com (already have)
3. **Gmail/Google Workspace** - For SMTP email notifications
4. **GitHub** - Access to smfworks repositories

### Domain Setup
Point these DNS records to your server IP:

```
A     smfworks.com     → YOUR_SERVER_IP
A     api.smfworks.com → YOUR_SERVER_IP
CNAME www              → smfworks.com
```

---

## Server Setup

### 1. Create Ubuntu Server

**DigitalOcean example:**
```bash
# Create droplet
- Ubuntu 22.04 LTS
- Basic plan, $6/month (1GB RAM, 1 CPU, 25GB SSD)
- Datacenter: NYC or closest to you
- Authentication: SSH key (recommended)
```

### 2. Initial Server Setup

SSH into your server:
```bash
ssh root@YOUR_SERVER_IP
```

Update system:
```bash
apt update && apt upgrade -y
```

Install essential packages:
```bash
apt install -y curl wget git ufw nginx certbot python3-certbot-nginx
```

Create service user:
```bash
useradd -r -s /bin/false -m -d /opt/smf smf
usermod -aG www-data smf
```

### 3. Firewall Configuration

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw allow 5000/tcp  # For testing
ufw enable
```

### 4. Install Python

```bash
apt install -y python3 python3-pip python3-venv python3-dev
```

---

## Installation

### 1. Clone Repository

```bash
cd /opt
sudo git clone https://github.com/smfworks/smf-lead-capture.git
sudo chown -R smf:smf smf-lead-capture
```

### 2. Create Virtual Environment

```bash
sudo su - smf
cd /opt/smf-lead-capture
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create Data Directories

```bash
mkdir -p data models logs
```

Exit back to root:
```bash
exit
```

---

## Configuration

### 1. Copy Production Config

```bash
cd /opt/smf-lead-capture
sudo cp config.production.yaml config.yaml
```

### 2. Create Environment File

Create `.env` file:
```bash
sudo nano /opt/smf-lead-capture/.env
```

Add this content (fill in your values):
```bash
# ============================================
# SMF Lead Capture - Production Environment
# ============================================

# Security
SECRET_KEY=CHANGE_THIS_TO_A_RANDOM_STRING_32_CHARS
API_KEY=YOUR_SECURE_API_KEY_FOR_WEBSITE

# Database (SQLite is default, no setup needed)
DATABASE_URL=sqlite:///data/smf_leads.db

# SMTP Configuration (Gmail/Google Workspace)
# See section below for Gmail App Password setup
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=michael@smfworks.com
SMTP_PASSWORD=YOUR_GMAIL_APP_PASSWORD
FROM_EMAIL=michael@smfworks.com
FROM_NAME="SMF Works"
NOTIFICATION_EMAIL=michael@smfworks.com

# Optional: WhatsApp Business API (for hot lead alerts)
WHATSAPP_ENABLED=false
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=

# Optional: Telegram Bot (for hot lead alerts)
TELEGRAM_ENABLED=false
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Optional: HubSpot CRM Integration
CRM_PROVIDER=  # Set to "hubspot" to enable
HUBSPOT_API_KEY=

# Webhook Security
WEBHOOK_SECRET=ANOTHER_RANDOM_STRING

# Server Settings
FLASK_ENV=production
```

### 3. Gmail App Password Setup

**Required for SMTP email notifications:**

1. Go to https://myaccount.google.com/
2. Navigate to **Security**
3. Enable **2-Step Verification** (required for app passwords)
4. Go to **Security → App passwords**
5. Click **Select app** → **Other (Custom name)**
6. Name it "SMF Lead Capture"
7. Click **Generate**
8. Copy the 16-character password
9. Paste it in `SMTP_PASSWORD` above

### 4. Create Systemd Service

Create service file:
```bash
sudo nano /etc/systemd/system/smf-lead-capture.service
```

Add:
```ini
[Unit]
Description=SMF Lead Capture Service
After=network.target

[Service]
Type=simple
User=smf
Group=smf
WorkingDirectory=/opt/smf-lead-capture
Environment=PYTHONPATH=/opt/smf-lead-capture
EnvironmentFile=/opt/smf-lead-capture/.env
ExecStart=/opt/smf-lead-capture/venv/bin/python -m smf_lead_capture server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable smf-lead-capture
sudo systemctl start smf-lead-capture
```

Check status:
```bash
sudo systemctl status smf-lead-capture
```

View logs:
```bash
sudo journalctl -u smf-lead-capture -f
```

### 5. Nginx Reverse Proxy

Create Nginx config:
```bash
sudo nano /etc/nginx/sites-available/smf-api
```

Add:
```nginx
server {
    listen 80;
    server_name api.smfworks.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/smf-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. SSL Certificate (HTTPS)

```bash
sudo certbot --nginx -d api.smfworks.com
```

Follow prompts. Choose option to redirect HTTP to HTTPS.

Test auto-renewal:
```bash
sudo certbot renew --dry-run
```

---

## Website Integration

### 1. Update Website Environment

In your `smfworks-site/.env.local`:

```bash
NEXT_PUBLIC_SMF_API_URL=https://api.smfworks.com
NEXT_PUBLIC_SMF_API_KEY=YOUR_API_KEY_FROM_ENV
```

### 2. Deploy Website

```bash
cd /path/to/smfworks-site
vercel deploy --prod
```

### 3. Test Widget

Visit https://smfworks.com and verify:
- Chat widget appears in bottom-right
- Can type and send messages
- Qualification questions work

---

## Testing

### 1. API Health Check

```bash
curl https://api.smfworks.com/api/health
```

Should return:
```json
{"status": "ok"}
```

### 2. Create Test Lead

```bash
curl -X POST https://api.smfworks.com/api/v1/leads \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "message": "This is a test lead",
    "source": "website"
  }'
```

### 3. Check Dashboard

Visit https://api.smfworks.com and verify lead appears.

### 4. Verify Email

Check that you received a notification email.

### 5. Test Chat Widget

1. Go to https://smfworks.com
2. Click chat widget
3. Complete conversation
4. Verify lead appears in dashboard

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u smf-lead-capture -n 50

# Check permissions
sudo chown -R smf:smf /opt/smf-lead-capture

# Test manually
sudo su - smf
cd /opt/smf-lead-capture
source venv/bin/activate
python -m smf_lead_capture server
```

### Emails Not Sending

```bash
# Test SMTP manually
telnet smtp.gmail.com 587

# Check logs for SMTP errors
sudo journalctl -u smf-lead-capture -f | grep -i smtp

# Verify app password is correct
# Re-generate if needed
```

### Widget Not Loading

1. Check browser console for CORS errors
2. Verify `cors_origins` in config.yaml includes your domain
3. Check API URL is correct in website .env

### Database Issues

```bash
# Check database file exists
ls -la /opt/smf-lead-capture/data/

# Check permissions
sudo chown smf:smf /opt/smf-lead-capture/data/smf_leads.db
sudo chmod 664 /opt/smf-lead-capture/data/smf_leads.db
```

### Nginx Errors

```bash
# Test config
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Restart nginx
sudo systemctl restart nginx
```

---

## Maintenance

### Backup Database

```bash
# Daily backup script
sudo nano /opt/backup-leads.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/backups"
DB_PATH="/opt/smf-lead-capture/data/smf_leads.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
sqlite3 $DB_PATH ".backup '$BACKUP_DIR/smf_leads_$DATE.db'"

# Keep only last 30 days
find $BACKUP_DIR -name "smf_leads_*.db" -mtime +30 -delete
```

Make executable and add to cron:
```bash
sudo chmod +x /opt/backup-leads.sh
sudo crontab -e
```

Add line:
```
0 2 * * * /opt/backup-leads.sh
```

### Update Application

```bash
# Pull latest changes
sudo su - smf
cd /opt/smf-lead-capture
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
exit
sudo systemctl restart smf-lead-capture
```

### Monitor Disk Space

```bash
# Check disk usage
df -h

# Check database size
ls -lh /opt/smf-lead-capture/data/
```

### Log Rotation

Create logrotate config:
```bash
sudo nano /etc/logrotate.d/smf-lead-capture
```

Add:
```
/opt/smf-lead-capture/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 smf smf
}
```

---

## Security Checklist

- [ ] Firewall enabled (ufw)
- [ ] SSH key authentication only
- [ ] Automatic security updates
- [ ] SSL certificate installed
- [ ] Strong SECRET_KEY and API_KEY
- [ ] Database backups configured
- [ ] Logs rotated
- [ ] Service running as non-root user

---

## Next Steps

After successful deployment:

1. **Enable WhatsApp** - Get Meta Business verification
2. **Enable Telegram** - Create bot with BotFather
3. **Train ML Model** - After 100+ leads collected
4. **Add Team Members** - Multi-user support
5. **Customize Qualification** - Adjust questions for your business

---

## Support

For issues:
1. Check logs: `sudo journalctl -u smf-lead-capture -f`
2. Review this guide
3. Check GitHub issues: https://github.com/smfworks/smf-lead-capture/issues

---

*Last updated: March 2026*
