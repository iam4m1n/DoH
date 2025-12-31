"""
Run UDP/TCP DNS servers and the HTTPS DoH server in one command.
"""
import os
import sys
import subprocess
import threading
from pathlib import Path

from django.core.management.base import BaseCommand

from dns_core.tcp_server import start_tcp_server
from dns_core.udp_server import start_udp_server

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CERT_DIR = BASE_DIR / 'certs'
CERT_FILE = CERT_DIR / 'server.crt'
KEY_FILE = CERT_DIR / 'server.key'


class Command(BaseCommand):
    help = 'Run UDP/TCP DNS servers and HTTPS DoH server (gunicorn) together'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bind',
            type=str,
            default='0.0.0.0:8443',
            help='Address and port for HTTPS server (default: 0.0.0.0:8443)'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=2,
            help='Gunicorn worker processes (default: 2)'
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
            help='Gunicorn worker timeout in seconds (default: 120)'
        )

    def handle(self, *args, **options):
        bind_address = options['bind']
        workers = options['workers']
        cert_file = options['cert']
        key_file = options['key']
        timeout = options['timeout']

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

        try:
            import gunicorn  # noqa: F401
        except ImportError:
            self.stdout.write(
                self.style.ERROR(
                    f'\n❌ Gunicorn is not installed!\n\n'
                    f'Please install it:\n'
                    f'   pip install gunicorn\n'
                )
            )
            sys.exit(1)

        udp_thread = threading.Thread(target=start_udp_server, daemon=True)
        tcp_thread = threading.Thread(target=start_tcp_server, daemon=True)
        udp_thread.start()
        tcp_thread.start()

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ UDP/TCP DNS servers started on port 8053\n'
                f'✅ Starting HTTPS DoH server at https://{bind_address}\n'
                f'   Certificate: {cert_file}\n'
                f'   Key: {key_file}\n'
                f'   Workers: {workers}\n'
                f'   ⚠️  Using self-signed certificate - browser will show security warning\n\n'
            )
        )

        wsgi_module = 'backend.wsgi:application'
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
            subprocess.run(cmd, check=True)
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\n\nServers stopped.'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Gunicorn failed to start: {e}\n')
            )
            sys.exit(1)
