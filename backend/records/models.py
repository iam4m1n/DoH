from django.db import models

class DNSRecord(models.Model):
    domain = models.CharField(max_length=255)
    record_type = models.CharField(max_length=10, default="A")
    value = models.CharField(max_length=255)
    ttl = models.IntegerField(default=60)
    priority = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.domain} {self.record_type} {self.value}"
