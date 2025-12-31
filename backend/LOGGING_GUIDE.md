# Logging System Guide

## Overview

The DNS Management System includes comprehensive logging for all requests, responses, and admin actions. All logs are stored in the `logs/` directory.

## Log Files

The system creates 5 separate log files:

1. **`logs/dns_queries.log`** - All DNS queries (UDP, TCP, DoH)
2. **`logs/api_requests.log`** - All API requests and responses
3. **`logs/admin_actions.log`** - Admin actions (add/edit/delete records, users)
4. **`logs/web_ui.log`** - Web UI actions (login, logout, queries)
5. **`logs/system.log`** - System events (server start, errors)

## Log Format

All logs use the following format:
```
YYYY-MM-DD HH:MM:SS - logger_name - LEVEL - Message
```

## What Gets Logged

### DNS Queries (`dns_queries.log`)
- Domain name queried
- Record type (A, AAAA, CNAME, etc.)
- Source (udp, tcp, doh-json, doh-binary)
- Status (success, nxdomain)
- Number of answers
- Cache status (CACHED or UPSTREAM)
- Client IP address

**Example:**
```
2024-01-15 10:30:45 - dns.queries - INFO - DNS Query | Domain: google.com. | Type: A | Source: doh-json | Status: success | Answers: 1 | Source: CACHED | Client: 127.0.0.1
```

### API Requests (`api_requests.log`)
- HTTP method (GET, POST, DELETE)
- Endpoint path
- User (username or anonymous)
- HTTP status code
- Response time (milliseconds)
- Client IP address

**Example:**
```
2024-01-15 10:30:45 - dns.api - INFO - API Request | Method: GET | Endpoint: /api/v1/dns-query | User: admin | Status: 200 | Response Time: 45ms | Client: 127.0.0.1
```

### Admin Actions (`admin_actions.log`)
- Action type (ADD_RECORD, EDIT_RECORD, DELETE_RECORD, ADD_USER, DELETE_USER)
- User who performed the action
- Resource type and ID
- Details (domain, record type, value, etc.)
- Success/failure status
- Client IP address

**Example:**
```
2024-01-15 10:30:45 - dns.admin - INFO - Admin Action | Action: ADD_RECORD | User: admin | Status: SUCCESS | Resource: DNSRecord (ID: 123) | Details: domain=example.com., type=A, value=192.168.1.1 | Client: 127.0.0.1
```

### Web UI Actions (`web_ui.log`)
- Action type (LOGIN, LOGOUT, DNS_QUERY, LOGIN_FAILED, DNS_QUERY_ERROR)
- User (username or anonymous)
- Details (domain, type, error messages)
- Client IP address

**Example:**
```
2024-01-15 10:30:45 - dns.web - INFO - Web Action | Action: DNS_QUERY | User: admin | Details: domain=google.com, type=A | Client: 127.0.0.1
```

### System Events (`system.log`)
- Event type (server_start, error, etc.)
- Event message

**Example:**
```
2024-01-15 10:30:45 - dns.system - INFO - System Event | Type: server_start | Message: UDP DNS server started on port 8053
```

## Viewing Logs

### View all DNS queries:
```bash
tail -f backend/logs/dns_queries.log
```

### View recent API requests:
```bash
tail -f backend/logs/api_requests.log
```

### View admin actions:
```bash
tail -f backend/logs/admin_actions.log
```

### Search for specific domain queries:
```bash
grep "google.com" backend/logs/dns_queries.log
```

### Search for errors:
```bash
grep -i error backend/logs/*.log
```

### View logs from a specific user:
```bash
grep "User: admin" backend/logs/admin_actions.log
```

## Log Rotation

Logs are written continuously and will grow over time. For production, consider:

1. **Implement log rotation** using tools like `logrotate`
2. **Set up log retention policies** (e.g., keep logs for 30 days)
3. **Monitor log file sizes** to prevent disk space issues

### Example logrotate configuration:
```bash
/home/am1n/4m1n/uni/network/project/backend/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 user group
}
```

## Log Analysis

### Count DNS queries by domain:
```bash
grep "DNS Query" backend/logs/dns_queries.log | awk -F'Domain: ' '{print $2}' | awk '{print $1}' | sort | uniq -c | sort -rn
```

### Count API requests by endpoint:
```bash
grep "API Request" backend/logs/api_requests.log | awk -F'Endpoint: ' '{print $2}' | awk '{print $1}' | sort | uniq -c | sort -rn
```

### Find failed login attempts:
```bash
grep "LOGIN_FAILED" backend/logs/web_ui.log
```

### Find slow API requests (>1000ms):
```bash
grep "API Request" backend/logs/api_requests.log | awk -F'Response Time: ' '{print $2}' | awk '{if ($1 > 1000) print}' 
```

## Security Considerations

⚠️ **Important**: Log files may contain sensitive information:
- User IP addresses
- Domain names queried
- Usernames
- Admin actions

**Recommendations:**
1. Restrict file permissions: `chmod 600 backend/logs/*.log`
2. Don't commit log files to version control (add to `.gitignore`)
3. Regularly review and clean up old logs
4. Consider encrypting log files for sensitive deployments

## Troubleshooting

### Logs not being created?
- Check that the `logs/` directory exists and is writable
- Verify the logger is imported correctly in modules
- Check for Python errors in the application logs

### Logs too verbose?
- Adjust log levels in `backend/dns_core/logger.py`
- Change `setLevel(logging.INFO)` to `setLevel(logging.WARNING)` for less verbose logs

### Logs missing information?
- Ensure all views are importing and using the logger functions
- Check that client IP extraction is working correctly

## Integration with Monitoring Tools

You can integrate these logs with monitoring tools like:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **Grafana Loki**
- **CloudWatch** (AWS)
- **Datadog**

Most tools can tail log files or use file-based log collectors.

