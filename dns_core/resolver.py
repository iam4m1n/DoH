import socket
from packet import parse_qname, build_response
from records import RECORDS, UPSTREAM_SERVERS
import struct

def resolve_dns(data):
    transaction_id = data[:2]
    offset = 12
    domain, offset = parse_qname(data, offset)
    qtype, qclass = struct.unpack("!HH", data[offset:offset + 4])
    question_section = data[12:offset + 4]

    # Check local records
    if domain in RECORDS:
        return build_response(transaction_id, question_section, domain, RECORDS[domain])

    # Forward to upstream
    response = forward_to_upstream(data)
    if response:
        return response

    # NXDOMAIN if nothing found
    return build_response(transaction_id, question_section, domain, None)


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
