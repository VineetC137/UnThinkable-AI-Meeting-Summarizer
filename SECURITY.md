# Security Setup Guide

## 🔒 Critical Security Steps

Before running this application, you **MUST** complete these security configuration steps:

### 1. Environment Configuration

#### Backend Environment (Required)
```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` and replace these critical values:
- `SECRET_KEY`: Generate a secure 32+ character secret key
- `POSTGRES_PASSWORD`: Use a strong password if using external database
- API keys for external services (only if using):
  - `OPENAI_API_KEY`
  - `GOOGLE_API_KEY` 
  - `ANTHROPIC_API_KEY`
  - `HUGGINGFACE_TOKEN`

#### Docker Environment (For Docker deployment)
```bash
cp .env.docker.example .env.docker
```

Edit `.env.docker` and update:
- `POSTGRES_PASSWORD`: Strong database password
- `SECRET_KEY`: Same value as backend/.env
- `GF_SECURITY_ADMIN_PASSWORD`: Secure Grafana password

### 2. Security Verification

Run these commands to verify your setup is secure:

```bash
# Verify sensitive files are not tracked
git status
# Should NOT show .env files in untracked files

# Verify sensitive files are ignored
git check-ignore backend/.env .env.docker
# Should return the file paths (meaning they're ignored)

# Check for any accidental commits of secrets
git log --grep="password\|secret\|key" --oneline
```

### 3. Production Security Checklist

- [ ] All `.env` files are configured with secure values
- [ ] Database passwords are strong and unique
- [ ] JWT secret key is cryptographically secure (32+ characters)
- [ ] API keys are valid and restricted to necessary permissions
- [ ] SSL certificates are configured for production domains
- [ ] Firewall rules restrict access to necessary ports only
- [ ] Regular security updates are applied to dependencies

## 🚨 Security Warnings

- **Never commit** `.env` files to version control
- **Never expose** API keys in client-side code
- **Always use** HTTPS in production
- **Regularly rotate** API keys and passwords
- **Monitor** application logs for suspicious activity

## 📞 Security Issues

If you discover a security vulnerability, please:
1. Do NOT create a public GitHub issue
2. Email security concerns to the maintainer
3. Allow time for fixes before public disclosure