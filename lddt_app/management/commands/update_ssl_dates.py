from django.core.management.base import BaseCommand
from django.utils import timezone

from lddt_app.models import Website

import ipaddress
import requests
import socket
import ssl
import time

from urllib.parse import urlparse


class Command(BaseCommand):
    help = "Populate SSL expiry, URL IP address, SSL provider, URL access scope and HTTP status"

    def normalise_url(self, url):
        if not url:
            return None

        if not url.startswith(("http://", "https://")):
            return f"https://{url}"

        return url

    def get_hostname(self, url):
        url = self.normalise_url(url)

        if not url:
            return None

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

    def update_http_status(self, obj):
        url = self.normalise_url(obj.url)

        obj.last_checked = timezone.now()
        obj.http_status_code = None
        obj.response_time_ms = None
        obj.last_error = None

        if not url:
            obj.http_check_status = "ERROR"
            obj.last_error = "No URL provided"
            self.stdout.write(" ✖ HTTP check failed: No URL provided")
            return

        try:
            start_time = time.monotonic()

            response = requests.get(
                url,
                timeout=10,
                allow_redirects=True,
                headers={
                    "User-Agent": "LDDS-Website-Monitor/1.0"
                }
            )

            end_time = time.monotonic()

            obj.http_status_code = response.status_code
            obj.response_time_ms = int((end_time - start_time) * 1000)

            if response.status_code == 200:
                obj.http_check_status = "OK"

            elif response.status_code == 403:
                obj.http_check_status = "BLOCKED"

            elif 300 <= response.status_code < 400:
                obj.http_check_status = "REDIRECT"

            elif response.history:
                obj.http_check_status = "REDIRECT"

            else:
                obj.http_check_status = "ERROR"
                obj.last_error = f"Unexpected HTTP status: {response.status_code}"

            self.stdout.write(
                f" ✔ HTTP check: {obj.http_check_status} | HTTP {obj.http_status_code} | {obj.response_time_ms}ms"
            )

        except requests.exceptions.SSLError as e:
            obj.http_check_status = "SSL_ERROR"
            obj.last_error = str(e)
            self.stdout.write(f" ✖ HTTP check SSL ERROR: {e}")

        except requests.exceptions.Timeout as e:
            obj.http_check_status = "OFFLINE"
            obj.last_error = str(e)
            self.stdout.write(f" ✖ HTTP check OFFLINE / TIMEOUT: {e}")

        except requests.exceptions.ConnectionError as e:
            obj.http_check_status = "OFFLINE"
            obj.last_error = str(e)
            self.stdout.write(f" ✖ HTTP check OFFLINE / CONNECTION ERROR: {e}")

        except Exception as e:
            obj.http_check_status = "ERROR"
            obj.last_error = str(e)
            self.stdout.write(f" ✖ HTTP check ERROR: {e}")

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
            # HTTP / HTTPS STATUS CHECK
            # --------------------------------------------------
            self.update_http_status(obj)

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

                if obj.url_access_scope in [None, ""]:
                    obj.url_access_scope = auto_scope
                    obj.url_access_scope_manual = False

                    self.stdout.write(
                        f" ✔ URL access scope set automatically: {obj.get_url_access_scope_display()}"
                    )

                elif obj.url_access_scope != auto_scope:
                    obj.url_access_scope_manual = True

                    self.stdout.write(
                        f" ✔ URL access scope kept manually: {obj.get_url_access_scope_display()}"
                    )

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
                "Finished updating SSL expiry dates, IP addresses, SSL providers, URL access scopes and HTTP statuses."
            )
        )