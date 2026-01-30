# Security Hardening Guide

This guide covers security best practices for deploying and operating Actifix in production environments.

## Authentication & Authorization

### Admin Authentication
- **Requirement**: Set admin password before production deployment
- **Setup**: `python3 scripts/set_admin_password.py`
- **Storage**: Uses OS keychain (macOS/Linux) or encrypted storage
- **See**: `docs/ADMIN_AUTHENTICATION.md` for full details

### API Token Authentication
- **JWT tokens**: Enabled by default for API access
- **Configuration**: See `src/actifix/security/auth.py`
- **Best practice**: Rotate tokens every 90 days
- **Local-only default**: API binds to 127.0.0.1 by default

### Rate Limiting
- **Per-minute limits**: Configured in `src/actifix/security/rate_limiter.py`
- **Per-hour limits**: Protects against sustained abuse
- **Per-day limits**: Global throttling
- **Override**: Set `ACTIFIX_RATE_LIMIT_DISABLED=1` for testing only

## Secret Management

### API Keys & Credentials
- **Storage**: Use OS credential manager via `scripts/set_api.py`
- **Never commit**: API keys, passwords, tokens to git
- **Environment variables**: Prefer for deployment
- **Scanning**: Pre-commit hooks scan for leaked secrets

### Secrets Scanner
- **Automatic**: Runs on every commit via pre-commit hooks
- **Manual**: `python3 -m actifix.security.secrets_scanner`
- **Coverage**: Detects AWS, OpenAI, GitHub, Stripe keys
- **Action**: Fails commit if secrets detected

## Network Security

### Default Binding
- **API**: 127.0.0.1 (localhost only)
- **Modules**: 127.0.0.1 (localhost only)
- **Production**: Use reverse proxy (nginx, Caddy) for external access

### HTTPS/TLS
- **Requirement**: Always use HTTPS in production
- **Implementation**: Configure reverse proxy with valid certificates
- **Let's Encrypt**: Recommended for free certificates
- **HSTS**: Enable Strict-Transport-Security headers

### CORS
- **Default**: Restricted to localhost origins
- **Production**: Configure allowed origins explicitly
- **Never use**: `Access-Control-Allow-Origin: *` in production

## Data Security

### Database Encryption
- **Location**: `data/actifix.db`
- **Permissions**: Set to 600 (owner read/write only)
- **Backup**: Encrypt backups before remote storage
- **At-rest**: Use filesystem encryption (LUKS, FileVault)

### Ticket Data
- **Sanitization**: `quarantine.py` isolates sensitive data
- **Redaction**: `secrets_scanner.py` redacts before storage
- **Webhooks**: Ticket data sanitized before external transmission
- **Export**: `diagnostics.py` sanitizes before bundle creation

### Log Security
- **Location**: `.actifix/logs/`
- **Rotation**: Automatic with size limits
- **Retention**: Configure cleanup policy
- **Sensitive data**: Never log passwords, API keys, tokens

## Webhook Security

### Configuration
- **HTTPS only**: Never use HTTP for webhooks
- **Validation**: Verify webhook signatures when available
- **Timeouts**: 5-second default prevents hanging
- **Retry logic**: Limited retries with exponential backoff

### Slack/Discord Alerts
- **Webhook URLs**: Store in environment variables
- **Sanitization**: High-priority alerts sanitize sensitive data
- **Testing**: Use dedicated test channels

## Ticket Throttling

### Flood Protection
- **Emergency brake**: Activates during ticket floods
- **Per-priority limits**: Separate limits for P2/P3/P4
- **Configuration**: `src/actifix/security/ticket_throttler.py`
- **Monitoring**: Check `ticket_throttle_history.json`

## Deployment Hardening

### Pre-Production Checklist
- [ ] Admin password set and secured
- [ ] API keys stored in credential manager
- [ ] Database permissions set to 600
- [ ] HTTPS configured with valid certificate
- [ ] Rate limiting enabled
- [ ] Secret scanning enabled in CI/CD
- [ ] Webhook URLs use HTTPS
- [ ] CORS configured for production origins
- [ ] Log rotation configured
- [ ] Backup encryption enabled
- [ ] Firewall rules limit API access
- [ ] Security headers configured (CSP, HSTS, X-Frame-Options)

### Monitoring
- **Failed auth attempts**: Monitor via logs
- **Rate limit hits**: Check rate limiter metrics
- **Secret leaks**: Pre-commit hook blocks commits
- **Webhook failures**: Review webhook logs
- **Database locks**: Monitor lock contention

### Incident Response
1. **Compromised credentials**: Rotate immediately via `set_api.py`
2. **Secret leak**: Revoke leaked credentials, audit git history
3. **Unauthorized access**: Review auth logs, reset admin password
4. **Data breach**: Follow incident response plan, notify affected parties

## Regular Maintenance

### Weekly
- Review authentication logs
- Check rate limiter metrics
- Verify backup integrity

### Monthly
- Rotate API tokens
- Review and update CORS origins
- Audit webhook configurations
- Update dependencies

### Quarterly
- Security audit of custom code
- Review and update this guide
- Penetration testing (if applicable)
- Credential rotation for service accounts

## References

- **Admin Auth**: `docs/ADMIN_AUTHENTICATION.md`
- **Secrets Scanner**: `src/actifix/security/secrets_scanner.py`
- **Rate Limiter**: `src/actifix/security/rate_limiter.py`
- **Credentials**: `src/actifix/security/credentials.py`
- **Ticket Throttler**: `src/actifix/security/ticket_throttler.py`

## Reporting Security Issues

**Do not** open public GitHub issues for security vulnerabilities.

Instead:
1. Email security findings to the maintainers
2. Include detailed reproduction steps
3. Wait for acknowledgment before public disclosure
4. Follow responsible disclosure timeline (90 days)

---

*Last updated: 2026-01-30*
