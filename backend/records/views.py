import base64
import binascii
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q, Count
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from dns_core.resolver import resolve_dns, resolve_dns_json
from dns_core.packet import TYPE_CODE, TYPE_MAP

from .models import DNSRecord
from .serializers import DNSRecordSerializer
from .renderers import DNSJsonRenderer, DNSMessageRenderer
from .forms import DNSRecordForm, DNSQueryForm, LoginForm, UserCreateForm

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
        # Mark admin-added records as manual (they don't expire)
        record = serializer.save(is_manual=True)
        return Response({"status": "ok", "id": record.id})
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

# ==================== Web UI Views ====================

def is_admin(user):
    """Check if user is admin (staff)"""
    return user.is_authenticated and user.is_staff

def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            from django.contrib.auth import authenticate
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome, {user.username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'records/login.html', {'form': form})

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def dashboard(request):
    """Main dashboard view"""
    # Get statistics
    total_records = DNSRecord.objects.count()
    manual_records = DNSRecord.objects.filter(is_manual=True).count()
    cached_records = DNSRecord.objects.filter(is_manual=False).count()
    
    # Get recent records
    recent_records = DNSRecord.objects.order_by('-cached_at')[:10]
    
    # Record type distribution
    record_types = DNSRecord.objects.values('record_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'total_records': total_records,
        'manual_records': manual_records,
        'cached_records': cached_records,
        'recent_records': recent_records,
        'record_types': record_types,
        'is_admin': request.user.is_staff,
    }
    return render(request, 'records/dashboard.html', context)

@login_required
def query_dns(request):
    """DNS query interface"""
    result = None
    error = None
    
    if request.method == 'POST':
        form = DNSQueryForm(request.POST)
        if form.is_valid():
            domain = form.cleaned_data['domain']
            record_type = form.cleaned_data['record_type']
            
            # Ensure domain ends with dot
            if not domain.endswith('.'):
                domain += '.'
            
            try:
                result = resolve_dns_json(domain, record_type)
            except Exception as e:
                error = str(e)
    else:
        form = DNSQueryForm()
    
    context = {
        'form': form,
        'result': result,
        'error': error,
        'is_admin': request.user.is_staff,
    }
    return render(request, 'records/query.html', context)

@login_required
def records_list(request):
    """List all DNS records (read-only for normal users)"""
    search_query = request.GET.get('search', '')
    record_type_filter = request.GET.get('type', '')
    
    records = DNSRecord.objects.all()
    
    # Apply filters
    if search_query:
        records = records.filter(
            Q(domain__icontains=search_query) |
            Q(value__icontains=search_query)
        )
    
    if record_type_filter:
        records = records.filter(record_type=record_type_filter)
    
    # Separate manual and cached records
    manual_records = records.filter(is_manual=True).order_by('-cached_at')
    cached_records = records.filter(is_manual=False).order_by('-cached_at')
    
    # Get available record types for filter
    available_types = DNSRecord.objects.values_list('record_type', flat=True).distinct()
    
    context = {
        'manual_records': manual_records,
        'cached_records': cached_records,
        'search_query': search_query,
        'record_type_filter': record_type_filter,
        'available_types': available_types,
        'is_admin': request.user.is_staff,
        'record_types': TYPE_MAP.values(),
    }
    return render(request, 'records/records_list.html', context)

@login_required
@user_passes_test(is_admin)
def add_record_view(request):
    """Add DNS record (admin only)"""
    if request.method == 'POST':
        form = DNSRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.is_manual = True
            record.save()
            messages.success(request, f'Record {record.domain} ({record.record_type}) added successfully!')
            return redirect('records_list')
    else:
        form = DNSRecordForm()
    
    context = {
        'form': form,
        'is_admin': True,
    }
    return render(request, 'records/add_record.html', context)

@login_required
@user_passes_test(is_admin)
def edit_record_view(request, record_id):
    """Edit DNS record (admin only)"""
    record = get_object_or_404(DNSRecord, id=record_id)
    
    if request.method == 'POST':
        form = DNSRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, f'Record updated successfully!')
            return redirect('records_list')
    else:
        form = DNSRecordForm(instance=record)
    
    context = {
        'form': form,
        'record': record,
        'is_admin': True,
    }
    return render(request, 'records/edit_record.html', context)

@login_required
@user_passes_test(is_admin)
def delete_record_view(request, record_id):
    """Delete DNS record (admin only)"""
    record = get_object_or_404(DNSRecord, id=record_id)
    
    if request.method == 'POST':
        domain = record.domain
        record.delete()
        messages.success(request, f'Record {domain} deleted successfully!')
        return redirect('records_list')
    
    context = {
        'record': record,
        'is_admin': True,
    }
    return render(request, 'records/delete_record.html', context)

@login_required
@user_passes_test(is_admin)
def users_list(request):
    """List all users (admin only)"""
    users = User.objects.all().order_by('-date_joined')
    
    # Separate admins and normal users
    admin_users = users.filter(is_staff=True)
    normal_users = users.filter(is_staff=False)
    
    context = {
        'admin_users': admin_users,
        'normal_users': normal_users,
        'is_admin': True,
    }
    return render(request, 'records/users_list.html', context)

@login_required
@user_passes_test(is_admin)
def add_user_view(request):
    """Add normal user (admin only)"""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Ensure new users are NOT staff (normal users only)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('users_list')
    else:
        form = UserCreateForm()
    
    context = {
        'form': form,
        'is_admin': True,
    }
    return render(request, 'records/add_user.html', context)

@login_required
@user_passes_test(is_admin)
def delete_user_view(request, user_id):
    """Delete user (admin only)"""
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deleting yourself
    if user.id == request.user.id:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('users_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('users_list')
    
    context = {
        'user': user,
        'is_admin': True,
    }
    return render(request, 'records/delete_user.html', context)
