from django.core.management.base import BaseCommand
from lddt_app.models import Website

import ipaddress
import socket
import ssl

from urllib.parse import urlparse


class Command(BaseCommand):
    help = "Populate SSL expiry, URL IP address, SSL provider and URL access scope"

    def get_hostname(self, url):
        if not url:
            return None

        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        parsed_url = urlparse(url)

        return parsed_url.hostname

    def get_ip_address(self, hostname):
        try:
            return socket.gethostbyname(hostname)

        except Exception as e:
            self.stdout.write(f" ✖ IP lookup failed: {e}")
            return None

    def get_ssl_provider(self, hostname):
        try:
            context = ssl.create_default_context()

            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    issuer = dict(x[0] for x in cert.get("issuer", []))

                    return (
                        issuer.get("organizationName")
                        or issuer.get("commonName")
                    )

        except Exception as e:
            self.stdout.write(f" ✖ SSL provider lookup failed: {e}")
            return None

    def get_access_scope_from_ip(self, ip_address):
        if not ip_address:
            return None

        try:
            ip = ipaddress.ip_address(ip_address)

            if ip.is_private:
                return "EDLAN_ONLY"

            return "GLOBAL"

        except ValueError:
            return None

    def handle(self, *args, **kwargs):
        websites = Website.objects.all()

        count = websites.count()

        for current, obj in enumerate(websites, start=1):
            self.stdout.write("")
            self.stdout.write("=" * 60)
            self.stdout.write(f"[{current}/{count}] Processing: {obj.common_name}")
            self.stdout.write("=" * 60)

            # --------------------------------------------------
            # SSL EXPIRY
            # --------------------------------------------------
            try:
                expiration = obj.ssl_expiration

                if expiration:
                    obj.ssl_expiry_date_new = expiration
                    self.stdout.write(f" ✔ SSL expiry: {expiration}")
                else:
                    self.stdout.write(" ✖ No SSL expiration data")

            except Exception as e:
                self.stdout.write(f" ✖ SSL expiration lookup failed: {e}")

            # --------------------------------------------------
            # HOSTNAME
            # --------------------------------------------------
            hostname = self.get_hostname(obj.url)

            if not hostname:
                self.stdout.write(" ✖ Could not determine hostname")
                obj.save()
                self.stdout.write("-" * 60)
                continue

            self.stdout.write(f" ✔ Hostname: {hostname}")

            # --------------------------------------------------
            # IP ADDRESS
            # --------------------------------------------------
            ip_address = self.get_ip_address(hostname)

            if ip_address:
                obj.url_ip = ip_address
                self.stdout.write(f" ✔ IP address: {ip_address}")
            else:
                self.stdout.write(" ✖ No IP address found")

            # --------------------------------------------------
            # URL ACCESS SCOPE
            # --------------------------------------------------

            if ip_address:
                auto_scope = self.get_access_scope_from_ip(ip_address)
            else:
                auto_scope = None

            if auto_scope:

                # Empty value -> auto populate
                if obj.url_access_scope in [None, ""]:

                    obj.url_access_scope = auto_scope
                    obj.url_access_scope_manual = False

                    self.stdout.write(
                        f" ✔ URL access scope set automatically: {obj.get_url_access_scope_display()}"
                    )

                # Different from auto -> manual override
                elif obj.url_access_scope != auto_scope:

                    obj.url_access_scope_manual = True

                    self.stdout.write(
                        f" ✔ URL access scope kept manually: {obj.get_url_access_scope_display()}"
                    )

                # Same as auto -> automatic
                else:

                    obj.url_access_scope_manual = False

                    self.stdout.write(
                        f" ✔ URL access scope confirmed automatic: {obj.get_url_access_scope_display()}"
                    )

            else:
                self.stdout.write(
                    " ✖ Could not determine automatic URL access scope"
                )

            # --------------------------------------------------
            # SSL PROVIDER
            # --------------------------------------------------
            provider = self.get_ssl_provider(hostname)

            if provider:
                obj.ssl_certificate_provider = provider
                self.stdout.write(f" ✔ SSL provider: {provider}")
            else:
                self.stdout.write(" ✖ No SSL provider found")

            # --------------------------------------------------
            # SAVE
            # --------------------------------------------------
            obj.save()

            self.stdout.write("-" * 60)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Finished updating SSL expiration dates, IP addresses, SSL providers and URL access scopes."
            )
        )