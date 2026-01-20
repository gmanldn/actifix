# Admin Authentication Setup

This document explains how the admin authentication system works in Actifix and how to manage admin credentials.

## Overview

Actifix uses a secure authentication system with:
- **PBKDF2-HMAC-SHA256** password hashing with 100,000 iterations
- **Role-based access control (RBAC)** with multiple roles
- **JWT token-based authentication** for API access
- **SQLite database** for storing user credentials and tokens

## Admin User Setup

### Credentials

The admin username is always `admin`. Choose the password when you run either:

- `ACTIFIX_ADMIN_PASSWORD=<your-password> python3 scripts/setup_admin.py`
- `ACTIFIX_ADMIN_PASSWORD=<your-password> python3 scripts/update_admin_password.py`

If the environment variable is absent, each script will prompt you interactively and abort when you cancel.

### Security Notice

⚠️ **IMPORTANT SECURITY INFORMATION:**

- The password is **NOT** stored in plain text anywhere in the codebase
- The password is hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations
- Only the **hashed version** is stored in the database (`data/actifix.db`)
- The plain text password is only used during authentication and is never persisted

### Password Hash Format

The password hash is stored in the format:
```
<salt_hex>$<pwdhash_hex>
```

Example hash:
```
d052263db72ebcfc59804a1efeb553207af4d9201183e01bb501e752cbc1ac18$17bd83c47e53937bfecc354052367f43bbc4c0c069eaa678df4bd84855688a44
```

## Managing Admin Credentials

### Update Admin Password

To update the admin password, use the provided script:

```bash
python3 scripts/update_admin_password.py
```

This script will:
1. Hash the new password using PBKDF2-HMAC-SHA256
2. Update the password in the database
3. Display the new credentials

### Create New Admin User

If you need to create additional admin users, use the `/api/auth/create-first-user` endpoint with a JSON body that contains `username` and `password` fields, or call `user_manager.create_user(...)` supplying the desired credentials and `{AuthRole.ADMIN}`.

## Authentication Flow

### 1. Login

To authenticate and get a token:

```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "<your-password>"}'
```

Response:
```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "user_id": "admin",
    "username": "admin",
    "roles": ["admin"],
    "is_active": true
  }
}
```

### 2. Use Token for API Access

Include the token in the Authorization header:

```bash
curl -X GET http://localhost:5001/api/health \
  -H "Authorization: Bearer <your_token_here>"
```

### 3. Token Validation

Tokens are validated automatically by the API server. Invalid or expired tokens will return:

```json
{
  "error": "Invalid token"
}
```

## User Roles and Permissions

### Available Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| **ADMIN** | Full system access | All permissions |
| **OPERATOR** | Manage tickets and config | read_tickets, create_tickets, update_tickets, manage_config, view_logs |
| **VIEWER** | Read-only access | read_tickets, view_logs |
| **SYSTEM** | System operations | All permissions (special role) |

### Admin Permissions

Admin users have the following permissions:
- `read_tickets` - View all tickets
- `create_tickets` - Create new tickets
- `update_tickets` - Update ticket status
- `delete_tickets` - Delete tickets
- `manage_config` - Modify system configuration
- `manage_users` - Create/update/delete users
- `manage_plugins` - Manage plugins
- `view_logs` - View system logs
- `view_audit` - View audit logs

## Database Schema

### auth_users Table

```sql
CREATE TABLE auth_users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    roles TEXT NOT NULL,  -- JSON array of role strings
    created_at TEXT NOT NULL,
    last_login TEXT,
    is_active BOOLEAN DEFAULT 1
);
```

### auth_tokens Table

```sql
CREATE TABLE auth_tokens (
    token_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL,  -- SHA256 hash of token
    token_type TEXT NOT NULL,  -- 'bearer' or 'api_key'
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    last_used TEXT,
    is_revoked BOOLEAN DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES auth_users(user_id)
);
```

### auth_events Table

```sql
CREATE TABLE auth_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    user_id TEXT,
    ip_address TEXT,
    success BOOLEAN NOT NULL,
    details TEXT
);
```

## Security Features

### 1. Password Hashing

- Uses PBKDF2-HMAC-SHA256 with 100,000 iterations
- Unique salt for each password
- Constant-time comparison to prevent timing attacks

### 2. Token Security

- Tokens are hashed before storage (SHA256)
- Tokens expire after 24 hours (configurable)
- Tokens can be revoked individually or all tokens for a user
- Last used timestamp tracking

### 3. Audit Logging

All authentication events are logged:
- Successful logins
- Failed login attempts
- Token creation and revocation
- User management actions

### 4. Rate Limiting

The API implements rate limiting to prevent brute force attacks:
- Per-user rate limits
- Configurable limits per endpoint
- Automatic blocking after threshold

## Troubleshooting

### Can't Log In

1. **Check if admin user exists:**
   ```bash
   sqlite3 data/actifix.db "SELECT user_id, username, is_active FROM auth_users WHERE user_id = 'admin';"
   ```

2. **Reset password:**
   ```bash
   python3 scripts/update_admin_password.py
   ```

3. **Check auth database location:**
   ```bash
   python3 -c "from actifix.state_paths import get_actifix_paths; print(get_actifix_paths().state_dir)"
   ```

### Token Issues

1. **Token expired:**
   - Log in again to get a new token
   - Tokens expire after 24 hours by default

2. **Token revoked:**
   - All tokens are revoked on password change
   - Log in again to get a new token

3. **Invalid token:**
   - Ensure the token is correctly formatted
   - Check that the Authorization header is: `Bearer <token>`

### Database Issues

1. **Auth database not found:**
   - Ensure the application has been run at least once
   - Check the state directory location

2. **Corrupted auth database:**
   - Backup the database
   - Delete the auth.db file
   - Restart the application to recreate it

## API Endpoints

### Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | Authenticate user and get token |
| `/api/auth/create-first-user` | POST | Create first admin user |

### Protected Endpoints (Require Authentication)

All API endpoints except `/api/auth/login` and `/api/auth/create-first-user` require authentication.

Example protected endpoints:
- `/api/health` - System health check
- `/api/stats` - Ticket statistics
- `/api/tickets` - List tickets
- `/api/logs` - View logs
- `/api/system` - System information

## Best Practices

1. **Change Default Password**
   - Always change the default password after initial setup
   - Use a strong, unique password

2. **Token Management**
   - Store tokens securely
   - Revoke tokens when not needed
   - Use short-lived tokens for production

3. **User Management**
   - Create separate users for different purposes
   - Assign minimal required permissions
   - Regularly review user accounts

4. **Audit Logging**
   - Monitor authentication events
   - Review failed login attempts
   - Track user activity

5. **Database Security**
   - Backup the auth database regularly
   - Restrict file permissions on auth.db
   - Store database in secure location

## Files

| File | Purpose |
|------|---------|
| `src/actifix/security/auth.py` | Authentication and authorization implementation |
| `scripts/setup_admin.py` | Script to create admin user |
| `scripts/update_admin_password.py` | Script to update admin password |
| `data/actifix.db` | Main database (contains auth tables) |
| `data/auth.db` | Separate auth database (if configured) |

## Version

Authentication System: v1.0.0  
Last Updated: 2026-01-20
