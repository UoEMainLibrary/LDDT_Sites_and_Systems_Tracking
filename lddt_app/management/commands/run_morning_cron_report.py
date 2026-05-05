from datetime import timedelta
from pathlib import Path
import re
import socket

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.utils import timezone

from lddt_app.models import Website, Type, Vm


class Command(BaseCommand):
    help = "Run morning SSL + VM checks and generate TXT report"

    def parse_percent(self, value):
        if value is None:
            return None

        value = str(value).strip()
        match = re.match(r"^(\d+)%$", value)
        if match:
            return int(match.group(1))

        return None

    def parse_int(self, value):
        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def handle(self, *args, **options):
        now = timezone.now()
        today = now.date()
        week_from_now = today + timedelta(days=7)
        vm_hostname = socket.gethostname()

        # --------------------------------------------------
        # Run refresh commands
        # --------------------------------------------------
        try:
            call_command("update_ssl_dates")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"update_ssl_dates failed: {e}"))

        try:
            call_command("script_copy_properties")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"script_copy_properties failed: {e}"))

        # --------------------------------------------------
        # Websites / SSL section
        # --------------------------------------------------
        try:
            site_type = Type.objects.get(name="SITE")
        except Type.DoesNotExist:
            self.stderr.write(self.style.ERROR('Type "SITE" does not exist.'))
            return
        except Type.MultipleObjectsReturned:
            self.stderr.write(self.style.ERROR('More than one Type with name "SITE" exists.'))
            return

        site_websites = list(
            Website.objects.select_related("type")
            .filter(type_id=site_type.id)
            .order_by("url")
        )

        for website in site_websites:
            try:
                expiry_date = website.ssl_expiration
                website.ssl_expiry_date_new = expiry_date
                website.save(update_fields=["ssl_expiry_date_new"])
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"Failed to update SSL for {website.url}: {e}")
                )

        site_websites = list(
            Website.objects.select_related("type")
            .filter(type_id=site_type.id)
            .order_by("url")
        )

        expiring_this_week = [
            w for w in site_websites
            if w.ssl_expiry_date_new and today <= w.ssl_expiry_date_new <= week_from_now
        ]
        expiring_this_week.sort(key=lambda x: (x.ssl_expiry_date_new, x.url or ""))

        expired_services = [
            w for w in site_websites
            if w.ssl_expiry_date_new and w.ssl_expiry_date_new < today
        ]
        expired_services.sort(key=lambda x: (x.ssl_expiry_date_new, x.url or ""))

        # --------------------------------------------------
        # VM section
        # --------------------------------------------------
        vms = list(Vm.objects.all().order_by("hostname"))

        total_vms = len(vms)
        low_space_vms = []
        old_patch_vms = []

        for vm in vms:
            root_free = self.parse_percent(vm.vmfs_root_used)
            apps_free = self.parse_percent(vm.vmfs_apps_used)
            data_free = self.parse_percent(vm.vmfs_data_used)

            low_mounts = []

            if root_free is not None and root_free < 10:
                low_mounts.append(f"root: {root_free}% free")

            if apps_free is not None and apps_free < 10:
                low_mounts.append(f"apps: {apps_free}% free")

            if data_free is not None and data_free < 10:
                low_mounts.append(f"data: {data_free}% free")

            if low_mounts:
                low_space_vms.append(
                    f"- {vm.hostname or '-'} | "
                    f"ip_address: {vm.ip_address or '-'} | "
                    f"{', '.join(low_mounts)}"
                )

            last_patch_days = self.parse_int(vm.last_patch_days_ago)

            if last_patch_days is not None and last_patch_days > 38:
                old_patch_vms.append(
                    f"- {vm.hostname or '-'} | "
                    f"ip_address: {vm.ip_address or '-'} | "
                    f"last patched: {last_patch_days} days ago"
                )

        # --------------------------------------------------
        # Build report
        # --------------------------------------------------
        report_lines = [
            f"TRACKING REPORT ({vm_hostname})",
            f"Generated at: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "=" * 60,
            "WEBSITES AND SSL CERTIFICATES",
            "=" * 60,
            "",
            f"Total: {len(site_websites)} services",
            "",
            f"Services with expiring SSL cert this week: {len(expiring_this_week)}",
        ]

        if expiring_this_week:
            report_lines.append("-" * 60)
            for w in expiring_this_week:
                days_left = (w.ssl_expiry_date_new - today).days
                report_lines.append(
                    f"- {w.url or '-'} | "
                    f"expires: {w.ssl_expiry_date_new} | "
                    f"expire in: {days_left} days"
                )

        report_lines.extend([
            "",
            f"Services with expired date: {len(expired_services)}",
        ])

        if expired_services:
            report_lines.append("-" * 60)
            for w in expired_services:
                days_expired = (today - w.ssl_expiry_date_new).days
                report_lines.append(
                    f"- {w.url or '-'} | "
                    f"expired: {w.ssl_expiry_date_new} | "
                    f"expired: {days_expired} days ago"
                )

        report_lines.extend([
            "",
            "",
            "=" * 60,
            "VM's",
            "=" * 60,
            "",
            f"Total: {total_vms} machines",
            "",
            f"VMs with less than 10% free space: {len(low_space_vms)}",
        ])

        if low_space_vms:
            report_lines.append("-" * 60)
            report_lines.extend(low_space_vms)

        report_lines.extend([
            "",
            f"VM's patched over 38 days ago: {len(old_patch_vms)}",
        ])

        if old_patch_vms:
            report_lines.append("-" * 60)
            report_lines.extend(old_patch_vms)

        # --------------------------------------------------
        # Save report
        # --------------------------------------------------
        output_dir = Path(settings.BASE_DIR) / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        file_path = output_dir / "tracking_morning_report.txt"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        self.stdout.write(self.style.SUCCESS(f"Report saved to: {file_path}"))