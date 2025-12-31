import socket
import struct
from datetime import timedelta
from django.utils import timezone
from .packet import parse_qname, build_response, TYPE_MAP, build_query, parse_dns_response
from .records import UPSTREAM_SERVERS
from records.models import DNSRecord
from .redis_cache import (
    get_cached_records,
    get_cached_records_any,
    cache_record,
    delete_cached_records
)

def resolve_dns(data):
    transaction_id = data[:2]
    offset = 12
    domain, offset = parse_qname(data, offset)
    qtype, qclass = struct.unpack("!HH", data[offset:offset + 4])
    question_section = data[12:offset + 4]
    qtype_name = TYPE_MAP.get(qtype, str(qtype))

    # Check Redis cache first
    cached_records = []
    if qtype_name == "ANY":
        cached_records = get_cached_records_any(domain)
    else:
        cached_records = get_cached_records(domain, qtype_name)
    
    # Also check manual records from database
    manual_records = []
    if qtype_name == "ANY":
        manual_records = DNSRecord.objects.filter(domain=domain, is_manual=True)
    else:
        manual_records = DNSRecord.objects.filter(domain=domain, record_type=qtype_name, is_manual=True)
    
    # Combine cached and manual records
    answers = []
    for record in cached_records:
        answers.append({
            "type": record["record_type"],
            "value": record["value"],
            "ttl": record["ttl"],  # Redis TTL is handled by Redis expiration
            "priority": record.get("priority"),
        })
    
    for record in manual_records:
        answers.append({
            "type": record.record_type,
            "value": record.value,
            "ttl": record.ttl,
            "priority": record.priority,
        })
    
    if answers:
        return build_response(transaction_id, question_section, answers)
    
    # Forward to upstream if no valid cached records
    response = forward_to_upstream(data)
    if response:
        # Cache the upstream response
        cache_upstream_response(domain, qtype_name, response)
        return response

    # NXDOMAIN if nothing found
    return build_response(transaction_id, question_section, [], rcode=3)


def forward_to_upstream(data):
    for server, port in UPSTREAM_SERVERS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            sock.sendto(data, (server, port))
            resp, _ = sock.recvfrom(512)
            sock.close()
            return resp
        except Exception:
            continue
    return None

def cache_upstream_response(domain, qtype_name, response_data):
    """Cache upstream DNS response in Redis"""
    try:
        parsed = parse_dns_response(response_data)
        if parsed.get("Status") != 0:
            return  # Don't cache errors

        # Collect all answers first (cache all types, not just the queried type)
        answers = []
        for answer in parsed.get("Answer", []):
            answer_domain = answer.get("name", domain)
            record_type = answer.get("type")
            value = answer.get("data")
            ttl = answer.get("ttl", 60)
            
            if not value:
                continue
            
            # Handle MX records (priority is in the value string like "10 mail.example.com.")
            priority = None
            if record_type == "MX":
                parts = value.split(" ", 1)
                if len(parts) == 2:
                    try:
                        priority = int(parts[0])
                        value = parts[1]
                    except ValueError:
                        pass

            answers.append((answer_domain, record_type, value, ttl, priority))

        # Delete existing cached records per (domain, type) once
        to_delete = set((a[0], a[1]) for a in answers)
        for d_domain, d_type in to_delete:
            delete_cached_records(d_domain, d_type)

        # Cache all records in Redis
        for answer_domain, record_type, value, ttl, priority in answers:
            cache_record(answer_domain, record_type, value, ttl, priority)
    except Exception:
        # Silently fail caching to not break DNS resolution
        pass

def resolve_dns_json(domain, qtype_name):
    # Check local records first
    if not domain.endswith("."):
        domain = domain + "."
    
    # Check Redis cache first
    cached_records = []
    if qtype_name == "ANY":
        cached_records = get_cached_records_any(domain)
    else:
        cached_records = get_cached_records(domain, qtype_name)
    
    # Also check manual records from database
    manual_records = []
    if qtype_name == "ANY":
        manual_records = DNSRecord.objects.filter(domain=domain, is_manual=True)
    else:
        manual_records = DNSRecord.objects.filter(domain=domain, record_type=qtype_name, is_manual=True)
    
    # Combine cached and manual records
    answers = []
    for record in cached_records:
        answers.append({
            "name": domain,
            "type": record["record_type"],
            "ttl": record["ttl"],
            "data": record["value"],
        })
    
    for record in manual_records:
        answers.append({
            "name": domain,
            "type": record.record_type,
            "ttl": record.ttl,
            "data": record.value,
        })
    
    if answers:
        return {
            "Status": 0,
            "Question": [{"name": domain, "type": qtype_name}],
            "Answer": answers,
        }
    
    # Forward to upstream if no valid cached records
    _, query = build_query(domain, qtype_name)
    response = forward_to_upstream(query)
    if response:
        # Cache the upstream response
        cache_upstream_response(domain, qtype_name, response)
        return parse_dns_response(response)
    return {
        "Status": 3,
        "Question": [{"name": domain, "type": qtype_name}],
        "Answer": [],
    }
