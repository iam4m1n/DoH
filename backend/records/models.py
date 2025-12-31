from django.db import models
from django.utils import timezone
from datetime import timedelta

class DNSRecord(models.Model):
    domain = models.CharField(max_length=255)
    record_type = models.CharField(max_length=10, default="A")
    value = models.CharField(max_length=255)
    ttl = models.IntegerField(default=60)
    priority = models.IntegerField(null=True, blank=True)
    cached_at = models.DateTimeField(auto_now_add=True)
    is_manual = models.BooleanField(default=False)  # True for admin-added records, False for cached

    class Meta:
        indexes = [
            models.Index(fields=['domain', 'record_type']),
            models.Index(fields=['cached_at']),
        ]

    def is_expired(self):
        """Check if the record has expired based on TTL"""
        if self.is_manual:
            return False  # Manual records don't expire
        expiration_time = self.cached_at + timedelta(seconds=self.ttl)
        return timezone.now() > expiration_time

    def __str__(self):
        return f"{self.domain} {self.record_type} {self.value}"
