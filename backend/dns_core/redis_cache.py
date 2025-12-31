"""
Redis cache module for DNS records.
Uses Redis for caching DNS responses with proper TTL handling.
"""
import json
import hashlib
import redis
from django.conf import settings

# Redis connection (lazy initialization)
_redis_client = None

def get_redis_client():
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=False  # We'll handle encoding ourselves
        )
    return _redis_client

def normalize_domain(domain):
    """Normalize domain name for consistent key generation"""
    domain = domain.lower().strip()
    if not domain.endswith('.'):
        domain += '.'
    return domain

def normalize_value(value):
    """Normalize value for consistent key generation"""
    if isinstance(value, str):
        return value.lower().strip()
    return str(value)

def generate_cache_key(domain, record_type, value, priority=None):
    """
    Generate a unique Redis key for a DNS record.
    Format: dns:cache:{domain}:{record_type}:{value_hash}
    
    For MX records, priority is included in the hash.
    """
    domain = normalize_domain(domain)
    record_type = record_type.upper()
    value = normalize_value(value)
    
    # Create a unique identifier for this record
    # Include priority for MX records to distinguish different MX records
    key_parts = [domain, record_type, value]
    if priority is not None:
        key_parts.append(str(priority))
    
    # Create hash for the value part to handle special characters
    value_hash = hashlib.md5(':'.join(key_parts).encode('utf-8')).hexdigest()[:12]
    
    return f"dns:cache:{domain}:{record_type}:{value_hash}"

def generate_index_key(domain, record_type):
    """Generate key for the index set that tracks all cache keys for a domain/type"""
    domain = normalize_domain(domain)
    record_type = record_type.upper()
    return f"dns:cache:index:{domain}:{record_type}"

def get_cached_records(domain, record_type):
    """
    Get all cached records for a domain and record type.
    Returns list of dicts with record data.
    """
    try:
        r = get_redis_client()
        index_key = generate_index_key(domain, record_type)
        
        # Get all cache keys for this domain/type
        cache_keys = r.smembers(index_key)
        if not cache_keys:
            return []
        
        records = []
        for key_bytes in cache_keys:
            key = key_bytes.decode('utf-8')
            data = r.get(key)
            if data:
                try:
                    record = json.loads(data.decode('utf-8'))
                    records.append(record)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Invalid data, remove the key
                    r.delete(key)
                    r.srem(index_key, key_bytes)
        
        return records
    except Exception:
        # If Redis fails, return empty list (fallback to upstream)
        return []

def cache_record(domain, record_type, value, ttl, priority=None):
    """
    Cache a DNS record in Redis.
    Returns True if successful, False otherwise.
    """
    try:
        r = get_redis_client()
        cache_key = generate_cache_key(domain, record_type, value, priority)
        index_key = generate_index_key(domain, record_type)
        
        # Prepare record data
        record_data = {
            'domain': normalize_domain(domain),
            'record_type': record_type.upper(),
            'value': value,
            'ttl': int(ttl),
            'priority': priority,
            'cached_at': None  # We'll use Redis TTL instead
        }
        
        # Store in Redis with TTL
        # Use TTL + small buffer (60 seconds) to ensure we don't serve expired records
        redis_ttl = int(ttl) + 60
        r.setex(
            cache_key,
            redis_ttl,
            json.dumps(record_data)
        )
        
        # Add to index set (no expiration on index, keys expire themselves)
        r.sadd(index_key, cache_key)
        
        return True
    except Exception:
        return False

def delete_cached_records(domain, record_type):
    """
    Delete all cached records for a domain and record type.
    """
    try:
        r = get_redis_client()
        index_key = generate_index_key(domain, record_type)
        
        # Get all cache keys
        cache_keys = r.smembers(index_key)
        
        # Delete all keys
        if cache_keys:
            keys_to_delete = [k.decode('utf-8') for k in cache_keys]
            r.delete(*keys_to_delete)
        
        # Delete index
        r.delete(index_key)
        
        return True
    except Exception:
        return False

def get_cached_records_any(domain):
    """
    Get all cached records for a domain (any type).
    Returns list of dicts with record data.
    """
    try:
        r = get_redis_client()
        domain = normalize_domain(domain)
        
        # Get all index keys for this domain
        pattern = f"dns:cache:index:{domain}:*"
        index_keys = []
        for key_bytes in r.scan_iter(match=pattern):
            index_keys.append(key_bytes.decode('utf-8'))
        
        all_records = []
        for index_key in index_keys:
            cache_keys = r.smembers(index_key)
            for key_bytes in cache_keys:
                key = key_bytes.decode('utf-8')
                data = r.get(key)
                if data:
                    try:
                        record = json.loads(data.decode('utf-8'))
                        all_records.append(record)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
        
        return all_records
    except Exception:
        return []

