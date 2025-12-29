from django.core.management.base import BaseCommand
from dns_core.tcp_server import start_tcp_server


class Command(BaseCommand):
    help = 'Start the TCP DNS server on port 8053'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting TCP DNS server...'))
        try:
            start_tcp_server()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nTCP DNS server stopped.'))

