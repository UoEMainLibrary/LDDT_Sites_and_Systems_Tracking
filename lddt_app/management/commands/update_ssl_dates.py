from django.core.management.base import BaseCommand
from lddt_app.models import Website
import socket
from urllib.parse import urlparse


class Command(BaseCommand):
    help = "Populate SSL expiry and URL IP address"

    def handle(self, *args, **kwargs):
        count = Website.objects.count()
        current = 0

        for obj in Website.objects.all():
            current += 1

            self.stdout.write(f"[{current}/{count}] Processing {obj.common_name}")

            # ----------------------------
            # SSL EXPIRY
            # ----------------------------
            expiration = obj.ssl_expiration

            if expiration:
                obj.ssl_expiry_date_new = expiration
                self.stdout.write(f" ✔ SSL expiry: {expiration}")
            else:
                self.stdout.write(" ✖ No certificate data")

            # ----------------------------
            # URL -> IP
            # ----------------------------
            if obj.url:
                try:
                    parsed_url = urlparse(obj.url)

                    # Handle URLs with or without https://
                    hostname = parsed_url.netloc or parsed_url.path

                    ip_address = socket.gethostbyname(hostname)

                    obj.url_ip = ip_address

                    self.stdout.write(f" ✔ IP: {ip_address}")

                except Exception as e:
                    self.stdout.write(f" ✖ IP lookup failed: {e}")

            obj.save()

            self.stdout.write("----------------------------")

        self.stdout.write(
            self.style.SUCCESS(
                "Finished updating SSL expiration dates and IP addresses."
            )
        )