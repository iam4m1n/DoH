from django.core.management.base import BaseCommand
from dns_core.udp_server import start_udp_server


class Command(BaseCommand):
    help = 'Start the UDP DNS server on port 8053'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting UDP DNS server...'))
        try:
            start_udp_server()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nUDP DNS server stopped.'))

