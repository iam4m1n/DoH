import socket
import struct
from records import RECORDS

DNS_PORT = 8053


def parse_qname(data, offset):
    labels = []
    while True:
        length = data[offset]
        if length == 0:
            offset += 1
            break
        labels.append(data[offset + 1: offset + 1 + length].decode())
        offset += length + 1
    return ".".join(labels) + ".", offset


def build_dns_response(data):
    # Header: 12 bytes
    transaction_id = data[:2]

    flags = b"\x81\x80"  # Standard query response, No error
    qdcount = b"\x00\x01"
    ancount = b"\x00\x01"
    nscount = b"\x00\x00"
    arcount = b"\x00\x00"

    header = transaction_id + flags + qdcount + ancount + nscount + arcount

    # Question
    offset = 12
    domain, offset = parse_qname(data, offset)
    qtype, qclass = struct.unpack("!HH", data[offset:offset + 4])
    question = data[12:offset + 4]

    # Check record
    if domain not in RECORDS:
        # NXDOMAIN
        flags = b"\x81\x83"
        header = transaction_id + flags + qdcount + b"\x00\x00" + nscount + arcount
        return header + question

    ip = RECORDS[domain]

    # Answer section
    name = b"\xc0\x0c"  # pointer to domain name
    type_a = struct.pack("!H", 1)
    class_in = struct.pack("!H", 1)
    ttl = struct.pack("!I", 60)
    rdlength = struct.pack("!H", 4)
    rdata = socket.inet_aton(ip)

    answer = name + type_a + class_in + ttl + rdlength + rdata

    return header + question + answer


def start_udp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", DNS_PORT))
    print(f"UDP DNS server listening on port {DNS_PORT}")

    while True:
        data, addr = sock.recvfrom(512)
        response = build_dns_response(data)
        sock.sendto(response, addr)


if __name__ == "__main__":
    start_udp_server()
