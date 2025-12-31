# DNS over HTTPS (DoH) System

A DNS server implementation with DNS over HTTPS (DoH) support, local record management, and upstream forwarding capabilities.

## Features

### ✅ Implemented Features

1. **DNS Server (UDP & TCP)**
   - UDP DNS server on port 8053
   - TCP DNS server on port 8053
   - Standard DNS protocol support

2. **DNS over HTTPS (DoH)**
   - GET and POST methods supported
   - Binary format (`application/dns-message`)
   - JSON format (`application/dns-json`)
   - Endpoint: `/api/v1/dns-query`

3. **Record Management**
   - Add DNS records (POST `/api/v1/admin/record`)
   - List DNS records (GET `/api/v1/admin/records`)
   - Delete DNS records (DELETE `/api/v1/admin/record/<domain>`)
   - Admin authentication required

4. **Upstream Forwarding**
   - Automatically forwards queries to upstream DNS servers (8.8.8.8, 1.1.1.1)
   - Falls back if local records not found

5. **Supported Record Types**
   - A (IPv4)
   - AAAA (IPv6)
   - CNAME
   - MX (with priority)
   - TXT
   - PTR
   - NS

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. **Start Redis server** (required for DNS caching):
```bash
# On Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# On macOS
brew install redis
brew services start redis

# Or run Redis in Docker
docker run -d -p 6379:6379 redis:latest
```

3. Run migrations:
```bash
cd backend
python manage.py migrate
```

4. Create a superuser (for admin access):
```bash
python manage.py createsuperuser
```

## Usage

### One Command (UDP + TCP + HTTPS DoH)

```bash
cd backend

# First, generate SSL certificates (one-time setup)
chmod +x generate_certificates.sh
./generate_certificates.sh

# Run everything together
python manage.py run_all
```

The DoH endpoint will be available at:
- HTTPS: `https://localhost:8443/api/v1/dns-query` (⚠️ self-signed certificate)

### Run Separately (optional)

**UDP Server:**
```bash
cd backend
python manage.py start_udp_server
```

**TCP Server:**
```bash
cd backend
python manage.py start_tcp_server
```

**HTTPS (with self-signed certificate):**
```bash
cd backend
python manage.py runserver_https
```

### Testing DNS Queries

**Using dig (UDP/TCP):**
```bash
dig @localhost -p 8053 example.com
dig @localhost -p 8053 example.com +tcp
```

**Using curl (DoH - JSON - HTTPS with self-signed cert):**
```bash
# Skip certificate verification for self-signed cert
curl -k "https://localhost:8443/api/v1/dns-query?name=example.com&type=A" \
  -H "Accept: application/dns-json"

# Or specify the certificate
curl --cacert backend/certs/server.crt \
  "https://localhost:8443/api/v1/dns-query?name=example.com&type=A" \
  -H "Accept: application/dns-json"
```

**Using curl (DoH - Binary - HTTPS):**
```bash
# First, create a DNS query (requires base64 encoding)
curl -k "https://localhost:8443/api/v1/dns-query?dns=<base64-encoded-dns-query>"
```

### Managing Records

**Add a record (HTTPS only):**
```bash
curl -k -X POST https://localhost:8443/api/v1/admin/record \
  -H "Content-Type: application/json" \
  -u admin:password \
  -d '{
    "domain": "example.com.",
    "record_type": "A",
    "value": "192.168.1.1",
    "ttl": 3600
  }'
```

**List records (HTTPS only):**
```bash
curl -k https://localhost:8443/api/v1/admin/records \
  -u admin:password
```

**Delete a record (HTTPS only):**
```bash
curl -k -X DELETE https://localhost:8443/api/v1/admin/record/example.com. \
  -u admin:password
```

## Project Structure

```
backend/
├── dns_core/          # DNS core functionality
│   ├── packet.py      # DNS packet parsing/building
│   ├── resolver.py    # DNS resolution logic
│   ├── udp_server.py  # UDP DNS server
│   ├── tcp_server.py  # TCP DNS server
│   └── management/    # Django management commands
├── records/            # DNS record management
│   ├── models.py      # DNSRecord model
│   ├── views.py       # API endpoints
│   └── serializers.py # Data validation
└── backend/           # Django settings
```

## Implementation Status

**Core Features: ~95% Complete**
- ✅ DNS packet parsing and building
- ✅ UDP/TCP DNS servers
- ✅ DoH endpoint (GET/POST, binary/JSON)
- ✅ Local record storage (Django models)
- ✅ Upstream DNS forwarding
- ✅ Record management API
- ✅ Admin authentication
- ✅ Support for A, AAAA, CNAME, MX, TXT, PTR, NS records

**Optional/Bonus Features:**
- ✅ Caching (Redis implemented)
- ⚠️ Logging (not implemented)
- ⚠️ Web UI (frontend/index.html is empty)
- ⚠️ CLI tool (not implemented)
- ✅ HTTPS with self-signed certificates (implemented)

## Notes

- Domain names must end with a dot (.) in FQDN format
- MX records require a priority value
- Admin endpoints require authentication (use Django admin user)
- The system checks Redis cache first, then manual records, then forwards to upstream DNS servers
- **Redis is required** for DNS caching functionality
- Cached records automatically expire based on their TTL values
- Manual records (admin-added) are stored in the database and never expire

