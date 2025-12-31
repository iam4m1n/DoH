"""
Django management command to run the development server with HTTPS support.
Uses gunicorn with SSL certificates.
"""
import os
import sys
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CERT_DIR = BASE_DIR / 'certs'
CERT_FILE = CERT_DIR / 'server.crt'
KEY_FILE = CERT_DIR / 'server.key'


class Command(BaseCommand):
    help = 'Run development server with HTTPS support using gunicorn (self-signed certificate)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--bind',
            type=str,
            default='0.0.0.0:8443',
            help='Address and port to bind to (default: 0.0.0.0:8443)'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=2,
            help='Number of worker processes (default: 2)'
        )
        parser.add_argument(
            '--cert',
            type=str,
            default=str(CERT_FILE),
            help=f'Path to SSL certificate (default: {CERT_FILE})'
        )
        parser.add_argument(
            '--key',
            type=str,
            default=str(KEY_FILE),
            help=f'Path to SSL private key (default: {KEY_FILE})'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=120,
            help='Worker timeout in seconds (default: 120)'
        )
    
    def handle(self, *args, **options):
        bind_address = options['bind']
        workers = options['workers']
        cert_file = options['cert']
        key_file = options['key']
        timeout = options['timeout']
        
        # Check if certificates exist
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            self.stdout.write(
                self.style.ERROR(
                    f'\n❌ SSL certificates not found!\n'
                    f'   Certificate: {cert_file}\n'
                    f'   Key: {key_file}\n\n'
                    f'Please generate certificates first:\n'
                    f'   cd backend\n'
                    f'   chmod +x generate_certificates.sh\n'
                    f'   ./generate_certificates.sh\n'
                )
            )
            sys.exit(1)
        
        # Check if gunicorn is installed
        try:
            import gunicorn
        except ImportError:
            self.stdout.write(
                self.style.ERROR(
                    f'\n❌ Gunicorn is not installed!\n\n'
                    f'Please install it:\n'
                    f'   pip install gunicorn\n'
                )
            )
            sys.exit(1)
        
        # Get the WSGI application path
        wsgi_module = 'backend.wsgi:application'
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Starting HTTPS server with gunicorn...\n'
                f'   Address: https://{bind_address}\n'
                f'   Certificate: {cert_file}\n'
                f'   Key: {key_file}\n'
                f'   Workers: {workers}\n'
                f'   ⚠️  Using self-signed certificate - browser will show security warning\n\n'
            )
        )
        
        # Build gunicorn command
        cmd = [
            'gunicorn',
            wsgi_module,
            '--bind', bind_address,
            '--keyfile', key_file,
            '--certfile', cert_file,
            '--workers', str(workers),
            '--timeout', str(timeout),
            '--access-logfile', '-',
            '--error-logfile', '-',
            '--log-level', 'info',
        ]
        
        try:
            # Run gunicorn
            subprocess.run(cmd, check=True)
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\n\nServer stopped.'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Gunicorn failed to start: {e}\n')
            )
            sys.exit(1)

