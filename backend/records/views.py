import base64
import binascii
import json
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from dns_core.resolver import resolve_dns, resolve_dns_json
from dns_core.packet import TYPE_CODE

from .models import DNSRecord
from .serializers import DNSRecordSerializer
from .renderers import DNSJsonRenderer, DNSMessageRenderer

@api_view(['GET', 'POST'])
@renderer_classes([DNSJsonRenderer, DNSMessageRenderer])
def doh_query(request):
    accept = request.headers.get("Accept", "")
    
    if request.method == 'GET':
        # Check for DNS-JSON format first
        if "application/dns-json" in accept or request.GET.get("name"):
            qname = request.GET.get("name")
            qtype = request.GET.get("type", "A").upper()
            if not qname:
                return HttpResponse(
                    json.dumps({"error": "missing name parameter for dns-json"}),
                    content_type='application/dns-json',
                    status=400
                )
            if qtype not in TYPE_CODE:
                return HttpResponse(
                    json.dumps({"error": "unsupported type"}),
                    content_type='application/dns-json',
                    status=400
                )
            # Return DNS-JSON response using DRF Response with renderer
            response_data = resolve_dns_json(qname, qtype)
            return Response(response_data)
        
        # Otherwise, expect binary DNS message
        dns_b64 = request.GET.get('dns')
        if not dns_b64:
            return Response({"error": "missing dns parameter"}, status=400)
        try:
            data = base64.urlsafe_b64decode(dns_b64 + "==")
        except (binascii.Error, ValueError):
            return Response({"error": "invalid dns parameter"}, status=400)
        response = resolve_dns(data)
        # Return binary DNS message using Response with DNSMessageRenderer
        # The renderer will set the content type based on Accept header
        return Response(response)
    
    else:  # POST
        # Check for DNS-JSON format
        if request.content_type == "application/dns-json":
            payload = request.data or {}
            qname = payload.get("name")
            qtype = payload.get("type", "A").upper()
            if not qname:
                return HttpResponse(
                    json.dumps({"error": "missing name"}),
                    content_type='application/dns-json',
                    status=400
                )
            if qtype not in TYPE_CODE:
                return HttpResponse(
                    json.dumps({"error": "unsupported type"}),
                    content_type='application/dns-json',
                    status=400
                )
            # Return DNS-JSON response using DRF Response with renderer
            response_data = resolve_dns_json(qname, qtype)
            return Response(response_data)
        
        # Otherwise, expect binary DNS message
        data = request.body
        response = resolve_dns(data)
        # Return binary DNS message using Response with DNSMessageRenderer
        # The renderer will set the content type based on Accept header
        return Response(response)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def add_record(request):
    serializer = DNSRecordSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": "ok"})
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_records(request):
    records = DNSRecord.objects.all()
    serializer = DNSRecordSerializer(records, many=True)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_record(request, domain):
    DNSRecord.objects.filter(domain=domain).delete()
    return Response({"status": "deleted"})
