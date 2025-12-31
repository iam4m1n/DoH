from rest_framework import serializers
from .models import DNSRecord


class DNSRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DNSRecord
        fields = [
            "id",
            "domain",
            "record_type",
            "value",
            "ttl",
            "priority",
            "cached_at",
            "is_manual",
        ]
        read_only_fields = ["cached_at", "is_manual"]

    def validate_domain(self, value):
        """
        Ensure domain ends with a dot (FQDN format),
        which is required by DNS protocol.
        """
        if not value.endswith("."):
            raise serializers.ValidationError(
                "Domain name must be a fully qualified domain name (end with a dot)."
            )
        return value

    def validate_record_type(self, value):
        """
        Restrict record types to supported ones.
        """
        allowed_types = {"A", "AAAA", "CNAME", "MX", "TXT", "PTR", "NS"}
        value = value.upper()
        if value not in allowed_types:
            raise serializers.ValidationError(
                f"Unsupported record type. Allowed types: {', '.join(allowed_types)}"
            )
        return value

    def validate(self, attrs):
        """
        Record-type–specific validation.
        """
        record_type = attrs.get("record_type")
        value = attrs.get("value")
        priority = attrs.get("priority")

        if record_type == "A":
            # IPv4 validation is optional but recommended
            import socket
            try:
                socket.inet_aton(value)
            except OSError:
                raise serializers.ValidationError(
                    {"value": "Invalid IPv4 address for A record."}
                )

        if record_type == "MX" and priority is None:
            raise serializers.ValidationError(
                {"priority": "MX records require a priority value."}
            )

        return attrs
