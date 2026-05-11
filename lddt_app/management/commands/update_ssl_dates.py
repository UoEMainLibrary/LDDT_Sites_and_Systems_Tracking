from django.core.management.base import BaseCommand

from lddt_app.models import Website

import socket
import ssl

from urllib.parse import urlparse


class Command(BaseCommand):
    help = "Populate SSL expiry, URL IP address and SSL provider"

    def get_hostname(self, url):
        """
        Extract hostname from URL.
        Supports:
        - https://example.com
        - http://example.com
        - example.com
        """

        if not url:
            return None

        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        parsed_url = urlparse(url)

        return parsed_url.hostname

    def get_ip_address(self, hostname):
        """
        Resolve hostname to IP address.
        """

        try:
            return socket.gethostbyname(hostname)

        except Exception as e:
            self.stdout.write(f" ✖ IP lookup failed: {e}")
            return None

    def get_ssl_provider(self, hostname):
        """
        Get SSL certificate issuer/provider.
        """

        try:
            context = ssl.create_default_context()

            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:

                    cert = ssock.getpeercert()

                    issuer = dict(x[0] for x in cert.get("issuer", []))

                    provider = (
                        issuer.get("organizationName")
                        or issuer.get("commonName")
                    )

                    return provider

        except Exception as e:
            self.stdout.write(f" ✖ SSL provider lookup failed: {e}")
            return None

    def handle(self, *args, **kwargs):

        websites = Website.objects.all()

        count = websites.count()
        current = 0

        for obj in websites:

            current += 1

            self.stdout.write("")
            self.stdout.write("=" * 60)
            self.stdout.write(
                f"[{current}/{count}] Processing: {obj.common_name}"
            )
            self.stdout.write("=" * 60)

            # --------------------------------------------------
            # SSL EXPIRY
            # --------------------------------------------------

            try:

                expiration = obj.ssl_expiration

                if expiration:
                    obj.ssl_expiry_date_new = expiration

                    self.stdout.write(
                        f" ✔ SSL expiry: {expiration}"
                    )

                else:
                    self.stdout.write(
                        " ✖ No SSL expiration data"
                    )

            except Exception as e:

                self.stdout.write(
                    f" ✖ SSL expiration lookup failed: {e}"
                )

            # --------------------------------------------------
            # HOSTNAME
            # --------------------------------------------------

            hostname = self.get_hostname(obj.url)

            if hostname:

                self.stdout.write(
                    f" ✔ Hostname: {hostname}"
                )

                # --------------------------------------------------
                # IP ADDRESS
                # --------------------------------------------------

                ip_address = self.get_ip_address(hostname)

                if ip_address:

                    obj.url_ip = ip_address

                    self.stdout.write(
                        f" ✔ IP address: {ip_address}"
                    )

                # --------------------------------------------------
                # SSL PROVIDER
                # --------------------------------------------------

                provider = self.get_ssl_provider(hostname)

                if provider:

                    obj.ssl_certificate_provider = provider

                    self.stdout.write(
                        f" ✔ SSL provider: {provider}"
                    )

                else:

                    self.stdout.write(
                        " ✖ No SSL provider found"
                    )

            else:

                self.stdout.write(
                    " ✖ Could not determine hostname"
                )

            # --------------------------------------------------
            # SAVE
            # --------------------------------------------------

            obj.save()

            self.stdout.write("-" * 60)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Finished updating SSL expiration dates, IP addresses and SSL providers."
            )
        )