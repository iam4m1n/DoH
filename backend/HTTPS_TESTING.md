# HTTPS Testing Guide

## Quick Start

### 1. Generate SSL Certificates

```bash
cd backend
chmod +x generate_certificates.sh
./generate_certificates.sh
```

This will create:
- `backend/certs/server.crt` (certificate)
- `backend/certs/server.key` (private key)

### 2. Start HTTPS Server

```bash
cd backend
python manage.py runserver_https
```

The server will start using gunicorn with SSL:
- HTTPS server on `https://localhost:8443` (or `https://0.0.0.0:8443`)

**Note**: This uses gunicorn which is more reliable than the development server for HTTPS.

## Testing HTTPS

### Test 1: Using curl (Skip Certificate Verification)

```bash
# Test DoH JSON endpoint
curl -k "https://localhost:8443/api/v1/dns-query?name=google.com&type=A" \
  -H "Accept: application/dns-json"

# Test DoH binary endpoint (requires base64 encoded query)
curl -k "https://localhost:8443/api/v1/dns-query?dns=<base64-encoded-query>"
```

### Test 2: Using curl (With Certificate)

```bash
# Specify the certificate file
curl --cacert backend/certs/server.crt \
  "https://localhost:8443/api/v1/dns-query?name=google.com&type=A" \
  -H "Accept: application/dns-json"
```

### Test 3: Using Browser

1. Start the HTTPS server
2. Open browser and go to: `https://localhost:8443/api/v1/dns-query?name=google.com&type=A`
3. Browser will show a security warning (expected for self-signed certificates)
4. Click "Advanced" → "Proceed to localhost (unsafe)" or similar
5. You should see the JSON DNS response

### Test 4: Using Python requests

```python
import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Test DoH JSON
response = requests.get(
    "https://localhost:8443/api/v1/dns-query",
    params={"name": "google.com", "type": "A"},
    headers={"Accept": "application/dns-json"},
    verify=False  # Skip certificate verification
)

print(response.json())
```

### Test 5: Using dig with DoH (via curl proxy)

```bash
# Use curl as a proxy to test DoH over HTTPS
curl -k -X POST "https://localhost:8443/api/v1/dns-query" \
  -H "Content-Type: application/dns-json" \
  -d '{"name": "example.com", "type": "A"}'
```

## Expected Behavior

### ✅ What Should Work:
- HTTPS connection is established
- DNS queries work over HTTPS
- JSON and binary formats both work
- Admin endpoints work over HTTPS

### ⚠️ What to Expect:
- **Browser Security Warning**: Browsers will show a warning because the certificate is self-signed. This is normal and expected.
- **Certificate Verification Errors**: Tools like curl will show certificate errors unless you use `-k` flag or specify the certificate.

## Troubleshooting

### Error: "SSL certificates not found"
**Solution**: Run `./generate_certificates.sh` first

### Error: "Address already in use"
**Solution**: 
- Check if port 8443 is already in use: `lsof -i :8443`
- Kill the process or use a different port: `python manage.py runserver_https --https-port 9443`

### Error: "Connection refused"
**Solution**: 
- Make sure the server is running
- Check firewall settings
- Verify you're using the correct port (8443)

### Browser shows "Not Secure" warning
**Solution**: This is expected for self-signed certificates. Click "Advanced" and proceed.

## Alternative: Using Gunicorn Directly

You can also run gunicorn directly (the management command does this for you):

```bash
# Run with HTTPS directly
gunicorn backend.wsgi:application \
  --bind 0.0.0.0:8443 \
  --keyfile backend/certs/server.key \
  --certfile backend/certs/server.crt \
  --workers 2 \
  --timeout 120
```

The `runserver_https` command does this automatically for you.

## Security Notes

⚠️ **Important**: Self-signed certificates are for **testing only**. They:
- Are not trusted by browsers by default
- Should NOT be used in production
- Do not provide real security (anyone can create them)

For production, you should:
- Use certificates from a trusted Certificate Authority (CA)
- Use Let's Encrypt for free SSL certificates
- Configure proper HTTPS settings in Django settings.py

