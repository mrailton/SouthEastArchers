# External Database Access Guide

This guide explains how to access the MySQL database externally for your Dokploy deployment.

## Table of Contents

- [Quick Access Methods](#quick-access-methods)
- [Security Considerations](#security-considerations)
- [Access via Dokploy](#access-via-dokploy)
- [Access via Port Forwarding](#access-via-port-forwarding)
- [Access via SSH Tunnel](#access-via-ssh-tunnel)
- [Tools and Clients](#tools-and-clients)
- [Troubleshooting](#troubleshooting)

## Quick Access Methods

### Method 1: Dokploy Web Console (Easiest)

1. **Log into Dokploy dashboard**
2. **Navigate to your application**
3. **Click on the `db` service**
4. **Click "Console" or "Terminal"**
5. **Run MySQL commands:**
   ```bash
   mysql -u appuser -p southeastarchers
   # Enter password when prompted
   ```

**Pros:**
- ✅ No setup required
- ✅ Works from anywhere
- ✅ No ports to expose

**Cons:**
- ❌ Web-based only
- ❌ No GUI tools
- ❌ Limited functionality

### Method 2: SSH Tunnel (Recommended for GUI Tools)

Use an SSH tunnel to securely connect database clients:

```bash
# Create SSH tunnel to Dokploy server
ssh -L 3307:localhost:3306 user@dokploy-server.com

# Keep this terminal open
# In another terminal or GUI tool, connect to:
# Host: localhost
# Port: 3307
# User: appuser
# Password: <your-db-password>
# Database: southeastarchers
```

**Pros:**
- ✅ Secure (encrypted)
- ✅ Use any GUI tool
- ✅ No firewall changes needed
- ✅ Recommended by security best practices

**Cons:**
- ❌ Requires SSH access to server
- ❌ Tunnel must stay open

### Method 3: Expose MySQL Port (Not Recommended)

Only use this in development or with proper firewall rules.

**Update `docker/docker-compose.yml`:**

```yaml
services:
  db:
    image: mysql:8.4
    ports:
      - "3306:3306"  # Already exposed
      # OR for custom external port:
      - "${MYSQL_EXTERNAL_PORT:-33060}:3306"
```

**Connect directly:**
```bash
mysql -h dokploy-server.com -P 3306 -u appuser -p southeastarchers
```

**⚠️ Security Warning:**
- Exposes database to internet
- Use strong passwords
- Configure firewall rules
- Consider IP whitelisting

## Security Considerations

### ✅ Recommended Practices

1. **Use SSH tunnels** for external access
2. **Never expose MySQL directly** to the internet without firewall
3. **Use strong passwords** (generated, 32+ characters)
4. **Limit access by IP** if exposing port
5. **Use read-only users** for reporting/analysis
6. **Regular backups** before making changes
7. **Monitor access logs**

### ⚠️ What NOT to Do

- ❌ Don't use port 3306 publicly without firewall
- ❌ Don't use weak passwords (e.g., "password", "123456")
- ❌ Don't give root access externally
- ❌ Don't skip SSL/TLS in production

## Access via Dokploy

### Using Dokploy Console

**Step 1: Access Console**
```
Dokploy Dashboard → Application → db service → Console
```

**Step 2: Common Commands**
```bash
# Connect to database
mysql -u appuser -p southeastarchers

# Show tables
SHOW TABLES;

# View users
SELECT id, name, email, is_admin FROM users LIMIT 10;

# View memberships
SELECT u.name, m.status, m.expiry_date 
FROM memberships m 
JOIN users u ON m.user_id = u.id 
ORDER BY m.expiry_date DESC 
LIMIT 10;

# Exit
exit;
```

### Using Dokploy Database Tools

Some Dokploy installations include phpMyAdmin or Adminer:

```
Dokploy Dashboard → Database → Adminer (if available)
```

## Access via Port Forwarding

### Docker Port Forward

If you have Docker access on the Dokploy server:

```bash
# SSH into Dokploy server
ssh user@dokploy-server.com

# Find the MySQL container
docker ps | grep mysql

# Port forward
docker port <container-id>
# Shows: 3306/tcp -> 0.0.0.0:3306

# From your local machine
mysql -h dokploy-server.com -P 3306 -u appuser -p southeastarchers
```

### Configure Firewall (if needed)

**On Dokploy server:**

```bash
# Using UFW (Ubuntu)
sudo ufw allow from <your-ip> to any port 3306
sudo ufw status

# Using firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="<your-ip>/32" port protocol="tcp" port="3306" accept'
sudo firewall-cmd --reload
```

## Access via SSH Tunnel

### Using Command Line

```bash
# Create tunnel
ssh -L 3307:localhost:3306 user@dokploy-server.com

# Connect via tunnel (from another terminal)
mysql -h 127.0.0.1 -P 3307 -u appuser -p southeastarchers
```

### Using MySQL Workbench

1. **Open MySQL Workbench**
2. **Create new connection**
3. **Connection Method:** Standard TCP/IP over SSH
4. **SSH Configuration:**
   - SSH Hostname: `dokploy-server.com:22`
   - SSH Username: `your-ssh-user`
   - SSH Key File: `/path/to/your/ssh-key`
5. **MySQL Configuration:**
   - MySQL Hostname: `localhost` (or `db` if Docker network)
   - MySQL Port: `3306`
   - Username: `appuser`
   - Password: `<your-db-password>`
   - Default Schema: `southeastarchers`
6. **Test Connection**
7. **Connect**

### Using TablePlus

1. **Create New Connection → MySQL**
2. **Switch to SSH tab**
3. **Enable "Use SSH Tunnel"**
4. **SSH Settings:**
   - Host: `dokploy-server.com`
   - Port: `22`
   - User: `your-ssh-user`
   - Key: Select your SSH key
5. **Connection Settings:**
   - Host: `localhost`
   - Port: `3306`
   - User: `appuser`
   - Password: `<your-db-password>`
   - Database: `southeastarchers`
6. **Test & Connect**

### Using DBeaver

1. **Database → New Database Connection → MySQL**
2. **Main tab:**
   - Host: `localhost`
   - Port: `3307` (local tunnel port)
   - Database: `southeastarchers`
   - Username: `appuser`
   - Password: `<your-db-password>`
3. **SSH tab:**
   - Enable "Use SSH Tunnel"
   - Host: `dokploy-server.com`
   - Port: `22`
   - Username: `your-ssh-user`
   - Authentication: Private Key
   - Key: Browse to your SSH key
4. **Test Connection → Finish**

## Tools and Clients

### Recommended GUI Tools

| Tool | Platform | Features | Cost |
|------|----------|----------|------|
| [MySQL Workbench](https://www.mysql.com/products/workbench/) | Win/Mac/Linux | Official, full-featured | Free |
| [TablePlus](https://tableplus.com/) | Mac/Win/Linux | Modern, fast | Paid |
| [DBeaver](https://dbeaver.io/) | Win/Mac/Linux | Universal DB tool | Free |
| [HeidiSQL](https://www.heidisql.com/) | Windows | Lightweight, fast | Free |
| [Sequel Ace](https://sequel-ace.com/) | Mac | MySQL-focused | Free |

### Command Line Tools

```bash
# MySQL CLI (official)
mysql -h host -P port -u appuser -p southeastarchers

# mycli (enhanced CLI with autocomplete)
pip install mycli
mycli -h host -P port -u appuser -p southeastarchers

# Execute SQL from file
mysql -h host -P port -u appuser -p southeastarchers < backup.sql

# Dump database
mysqldump -h host -P port -u appuser -p southeastarchers > backup.sql
```

## Common Tasks

### View Database Info

```sql
-- Show all tables
SHOW TABLES;

-- Describe table structure
DESCRIBE users;

-- Show table creation SQL
SHOW CREATE TABLE users;

-- Count records
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM memberships WHERE status = 'active';

-- Recent activity
SELECT * FROM payments ORDER BY created_at DESC LIMIT 10;
```

### Create Read-Only User

For analysts or reporting tools:

```sql
-- Create read-only user
CREATE USER 'readonly'@'%' IDENTIFIED BY 'strong-password-here';

-- Grant read-only access
GRANT SELECT ON southeastarchers.* TO 'readonly'@'%';

-- Flush privileges
FLUSH PRIVILEGES;

-- Test connection with this user
```

### Backup Database

```bash
# Full backup
mysqldump -h localhost -P 3307 -u appuser -p southeastarchers > backup_$(date +%Y%m%d).sql

# Compress backup
mysqldump -h localhost -P 3307 -u appuser -p southeastarchers | gzip > backup_$(date +%Y%m%d).sql.gz

# Backup specific tables only
mysqldump -h localhost -P 3307 -u appuser -p southeastarchers users memberships > users_backup.sql
```

### Restore Database

```bash
# Restore from backup
mysql -h localhost -P 3307 -u appuser -p southeastarchers < backup.sql

# Restore from compressed backup
gunzip < backup.sql.gz | mysql -h localhost -P 3307 -u appuser -p southeastarchers
```

## Troubleshooting

### Can't Connect - Connection Refused

**Possible causes:**
- MySQL not running
- Port not exposed
- Firewall blocking

**Solutions:**
```bash
# Check if MySQL container is running
docker ps | grep mysql

# Check MySQL logs
docker logs <mysql-container-id>

# Test port
telnet dokploy-server.com 3306
# or
nc -zv dokploy-server.com 3306
```

### Can't Connect - Access Denied

**Check credentials:**
```bash
# Via Dokploy console
docker exec -it <mysql-container> mysql -u root -p
# Enter MYSQL_ROOT_PASSWORD

# Show users
SELECT user, host FROM mysql.user;

# Reset appuser password if needed
ALTER USER 'appuser'@'%' IDENTIFIED BY 'new-password';
FLUSH PRIVILEGES;
```

### Connection Times Out

**Check firewall:**
```bash
# On server
sudo ufw status
sudo iptables -L -n | grep 3306

# Check if port is listening
netstat -tlnp | grep 3306
# or
ss -tlnp | grep 3306
```

### SSH Tunnel Not Working

**Verify SSH access:**
```bash
# Test SSH connection
ssh user@dokploy-server.com

# Check SSH config
cat ~/.ssh/config

# Verbose SSH tunnel
ssh -v -L 3307:localhost:3306 user@dokploy-server.com
```

### Can't Find Database

**Check database exists:**
```sql
-- Show all databases
SHOW DATABASES;

-- Use specific database
USE southeastarchers;

-- If database missing, check environment variables
```

## Environment Variables

Remember your database credentials from `.env`:

```bash
MYSQL_ROOT_PASSWORD=<root-password>
MYSQL_DATABASE=southeastarchers
MYSQL_USER=appuser
MYSQL_PASSWORD=<your-password>
```

To view in Dokploy:
```
Dashboard → Application → Environment Variables
```

## Best Practices

### For Development
- ✅ Use SSH tunnel
- ✅ Use read-only user for querying
- ✅ Test queries on local database first
- ✅ Back up before running migrations

### For Production
- ✅ **Always use SSH tunnel**
- ✅ **Never expose MySQL directly**
- ✅ Regular automated backups
- ✅ Monitor database performance
- ✅ Use connection pooling
- ✅ Limit concurrent connections

### For Security
- ✅ Strong passwords (32+ chars)
- ✅ Rotate passwords regularly
- ✅ Monitor access logs
- ✅ Use SSL/TLS for connections
- ✅ Principle of least privilege
- ✅ Regular security audits

## Quick Reference

### SSH Tunnel Commands

```bash
# Basic tunnel
ssh -L 3307:localhost:3306 user@server.com

# Background tunnel
ssh -fN -L 3307:localhost:3306 user@server.com

# Tunnel with key
ssh -i ~/.ssh/id_rsa -L 3307:localhost:3306 user@server.com

# Multiple tunnels
ssh -L 3307:localhost:3306 -L 8080:localhost:80 user@server.com
```

### MySQL Connection Strings

```bash
# CLI
mysql -h HOST -P PORT -u USER -p DATABASE

# With SSH tunnel
mysql -h 127.0.0.1 -P 3307 -u appuser -p southeastarchers

# Connection URL
mysql://appuser:password@host:3306/southeastarchers

# With SSL
mysql -h HOST -P PORT -u USER -p --ssl-mode=REQUIRED DATABASE
```

## Related Documentation

- [Dokploy Documentation](https://docs.dokploy.com/)
- [MySQL Documentation](https://dev.mysql.com/doc/)
- [Docker Compose Guide](../docker/README.md)
- [Deployment Guide](DOKPLOY_DEPLOYMENT.md)

---

**Security Reminder:** Always use SSH tunnels for external database access in production environments. Never expose MySQL directly to the internet without proper security measures.
