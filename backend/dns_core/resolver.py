import socket
import struct
from .packet import parse_qname, build_response, TYPE_MAP, build_query, parse_dns_response
from .records import UPSTREAM_SERVERS
from records.models import DNSRecord

def resolve_dns(data):
    transaction_id = data[:2]
    offset = 12
    domain, offset = parse_qname(data, offset)
    qtype, qclass = struct.unpack("!HH", data[offset:offset + 4])
    question_section = data[12:offset + 4]
    qtype_name = TYPE_MAP.get(qtype, str(qtype))

    answers = []
    if qtype_name == "ANY":
        records = DNSRecord.objects.filter(domain=domain)
    else:
        records = DNSRecord.objects.filter(domain=domain, record_type=qtype_name)
        
    print("records:", records)
    for record in records:
        answers.append(
            {
                "type": record.record_type,
                "value": record.value,
                "ttl": record.ttl,
                "priority": record.priority,
            }
        )
    if answers:
        return build_response(transaction_id, question_section, answers)
    
    print("This is what i want:", data)
    
    # Forward to upstream
    response = forward_to_upstream(data)
    if response:
        print("This is what i want:", response)
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

def resolve_dns_json(domain, qtype_name):
    # Check local records first
    if not domain.endswith("."):
        domain = domain + "."
    
    answers = []
    if qtype_name == "ANY":
        records = DNSRecord.objects.filter(domain=domain)
    else:
        records = DNSRecord.objects.filter(domain=domain, record_type=qtype_name)
    
    for record in records:
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
    
    # Forward to upstream if no local records
    _, query = build_query(domain, qtype_name)
    response = forward_to_upstream(query)
    if response:
        return parse_dns_response(response)
    return {
        "Status": 3,
        "Question": [{"name": domain, "type": qtype_name}],
        "Answer": [],
    }
