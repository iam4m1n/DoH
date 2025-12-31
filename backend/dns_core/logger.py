"""
DNS System Logger
Logs all DNS queries, API requests, and admin actions
"""
import logging
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Create logs directory if it doesn't exist
try:
    BASE_DIR = Path(settings.BASE_DIR)
except (ImproperlyConfigured, AttributeError):
    BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# DNS Query Logger
dns_logger = logging.getLogger('dns.queries')
dns_logger.setLevel(logging.INFO)
if not dns_logger.handlers:
    dns_handler = logging.FileHandler(LOGS_DIR / 'dns_queries.log')
    dns_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    dns_logger.addHandler(dns_handler)
    dns_logger.propagate = False

# API Request Logger
api_logger = logging.getLogger('dns.api')
api_logger.setLevel(logging.INFO)
if not api_logger.handlers:
    api_handler = logging.FileHandler(LOGS_DIR / 'api_requests.log')
    api_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    api_logger.addHandler(api_handler)
    api_logger.propagate = False

# Admin Action Logger
admin_logger = logging.getLogger('dns.admin')
admin_logger.setLevel(logging.INFO)
if not admin_logger.handlers:
    admin_handler = logging.FileHandler(LOGS_DIR / 'admin_actions.log')
    admin_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    admin_logger.addHandler(admin_handler)
    admin_logger.propagate = False

# Web UI Logger
web_logger = logging.getLogger('dns.web')
web_logger.setLevel(logging.INFO)
if not web_logger.handlers:
    web_handler = logging.FileHandler(LOGS_DIR / 'web_ui.log')
    web_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    web_logger.addHandler(web_handler)
    web_logger.propagate = False

# General System Logger
system_logger = logging.getLogger('dns.system')
system_logger.setLevel(logging.INFO)
if not system_logger.handlers:
    system_handler = logging.FileHandler(LOGS_DIR / 'system.log')
    system_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    system_logger.addHandler(system_handler)
    system_logger.propagate = False


def log_dns_query(domain, record_type, source='unknown', status='success', 
                  answer_count=0, from_cache=False, client_ip=None):
    """Log a DNS query"""
    cache_status = 'CACHED' if from_cache else 'UPSTREAM'
    log_msg = (
        f"DNS Query | Domain: {domain} | Type: {record_type} | "
        f"Source: {source} | Status: {status} | Answers: {answer_count} | "
        f"Source: {cache_status} | Client: {client_ip or 'N/A'}"
    )
    dns_logger.info(log_msg)


def log_api_request(method, endpoint, user=None, status_code=200, 
                    response_time=None, client_ip=None):
    """Log an API request"""
    username = user.username if user and hasattr(user, 'username') else 'anonymous'
    log_msg = (
        f"API Request | Method: {method} | Endpoint: {endpoint} | "
        f"User: {username} | Status: {status_code} | "
        f"Response Time: {response_time or 'N/A'}ms | Client: {client_ip or 'N/A'}"
    )
    api_logger.info(log_msg)


def log_admin_action(action, user, resource_type, resource_id=None, 
                     details=None, success=True, client_ip=None):
    """Log an admin action (add/edit/delete records, users, etc.)"""
    status = 'SUCCESS' if success else 'FAILED'
    resource_info = f" | Resource: {resource_type}"
    if resource_id:
        resource_info += f" (ID: {resource_id})"
    if details:
        resource_info += f" | Details: {details}"
    client_str = f" | Client: {client_ip}" if client_ip else ""
    
    log_msg = (
        f"Admin Action | Action: {action} | User: {user.username} | "
        f"Status: {status}{resource_info}{client_str}"
    )
    admin_logger.info(log_msg)


def log_web_action(action, user=None, details=None, client_ip=None):
    """Log web UI actions (login, logout, queries, etc.)"""
    username = user.username if user and hasattr(user, 'username') else 'anonymous'
    details_str = f" | Details: {details}" if details else ""
    client_str = f" | Client: {client_ip}" if client_ip else ""
    
    log_msg = f"Web Action | Action: {action} | User: {username}{details_str}{client_str}"
    web_logger.info(log_msg)


def log_system_event(event_type, message, level='info'):
    """Log system events (server start, errors, etc.)"""
    log_func = getattr(system_logger, level.lower(), system_logger.info)
    log_msg = f"System Event | Type: {event_type} | Message: {message}"
    log_func(log_msg)


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip
