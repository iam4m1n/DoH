from django.contrib import admin
from .models import DNSRecord

@admin.register(DNSRecord)
class DNSRecordAdmin(admin.ModelAdmin):
    list_display = ['domain', 'record_type', 'value', 'ttl', 'priority']
    list_filter = ['record_type']
    search_fields = ['domain', 'value']
