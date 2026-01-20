# Quick Admin Setup Guide

This guide provides a quick reference for setting up and using admin authentication in Actifix.

## Quick Start

### 1. Update Admin Password

Run the password update script:

```bash
ACTIFIX_ADMIN_PASSWORD=<your-password> python3 scripts/update_admin_password.py
```

If you omit `ACTIFIX_ADMIN_PASSWORD`, the script will prompt you to enter a secure password interactively.

### 2. Login to Get Token

```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "<your-password>"}'
```

Save the token from the response.

### 3. Use Token for API Access

```bash
curl -X GET http://localhost:5001/api/health \
  -H "Authorization: Bearer <your-token>"
```

## Credentials

- **Username:** `admin`
- **Password:** (as provided when running the setup script)
- **Role:** `admin` (full access)

## Security

⚠️ **Important:**
- Password is hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations
- Only the hash is stored in the database
- Plain text password is never persisted

## Common Commands

### Check if admin user exists
```bash
sqlite3 data/actifix.db "SELECT user_id, username, is_active FROM auth_users WHERE user_id = 'admin';"
```

### View all users
```bash
sqlite3 data/actifix.db "SELECT user_id, username, roles, is_active FROM auth_users;"
```

### Revoke all tokens for admin
```python
from actifix.security.auth import get_token_manager
token_manager = get_token_manager()
token_manager.revoke_all_user_tokens('admin')
```

## Troubleshooting

### Can't log in?
1. Run `python3 scripts/update_admin_password.py` to reset password
2. Check if auth database exists: `ls -la data/actifix.db`
3. Verify admin user: `sqlite3 data/actifix.db "SELECT * FROM auth_users WHERE user_id='admin';"`

### Token expired?
- Log in again to get a new token
- Tokens expire after 24 hours

### Need to create additional admin users?
Use the API endpoint:
```bash
curl -X POST http://localhost:5001/api/auth/create-first-user \
  -H "Content-Type: application/json" \
  -d '{"username": "newadmin", "password": "newpassword"}'
```

## Files

- `scripts/update_admin_password.py` - Update admin password
- `scripts/setup_admin.py` - Create new admin user
- `docs/ADMIN_AUTHENTICATION.md` - Full documentation
- `src/actifix/security/auth.py` - Authentication implementation

## Next Steps

1. Read `docs/ADMIN_AUTHENTICATION.md` for detailed information
2. Explore the API endpoints in `src/actifix/api.py`
3. Review security features in `src/actifix/security/`

---

**Last Updated:** 2026-01-20  
**Version:** 1.0.0
