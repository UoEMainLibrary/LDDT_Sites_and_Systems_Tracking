from datetime import timedelta
from pathlib import Path
import re

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

    def handle(self, *args, **options):
        now = timezone.now()
        today = now.date()
        week_from_now = today + timedelta(days=7)

        report_lines = [
            "=" * 70,
            "TRACKING REPORT",
            f"Generated at: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 70,
            "",
        ]

        # --------------------------------------------------
        # Run refresh commands
        # --------------------------------------------------
        report_lines.extend([
            "REFRESH COMMANDS",
            "-" * 70,
        ])

        try:
            call_command("update_ssl_dates")
            report_lines.append("update_ssl_dates: OK")
        except Exception as e:
            report_lines.append(f"update_ssl_dates: FAILED ({e})")

        try:
            call_command("script_copy_properties")
            report_lines.append("script_copy_properties: OK")
        except Exception as e:
            report_lines.append(f"script_copy_properties: FAILED ({e})")

        report_lines.extend([
            "",
            "=" * 70,
            "SSL CERTIFICATES STATUS",
            "=" * 70,
        ])

        # --------------------------------------------------
        # SSL section
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

        updated_count = 0
        failed_count = 0

        for website in site_websites:
            try:
                expiry_date = website.ssl_expiration
                website.ssl_expiry_date_new = expiry_date
                website.save(update_fields=["ssl_expiry_date_new"])
                updated_count += 1
            except Exception:
                failed_count += 1

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

        report_lines.extend([
            f"Total SITE services: {len(site_websites)}",
            f"Updated SSL values: {updated_count}",
            f"Failed SSL updates: {failed_count}",
            "",
            "Services expiring this week",
            "-" * 70,
        ])

        if expiring_this_week:
            for w in expiring_this_week:
                days_left = (w.ssl_expiry_date_new - today).days
                report_lines.append(
                    f"- {w.url or '-'} | "
                    f"common_name: {w.common_name or '-'} | "
                    f"expires: {w.ssl_expiry_date_new} | "
                    f"days_left: {days_left}"
                )
        else:
            report_lines.append("No SITE services expiring this week.")

        report_lines.extend([
            "",
            f"Total expiring this week: {len(expiring_this_week)}",
            "",
            "Services with expired date",
            "-" * 70,
        ])

        if expired_services:
            for w in expired_services:
                days_expired = (today - w.ssl_expiry_date_new).days
                report_lines.append(
                    f"- {w.url or '-'} | "
                    f"common_name: {w.common_name or '-'} | "
                    f"expired: {w.ssl_expiry_date_new} | "
                    f"days_expired: {days_expired}"
                )
        else:
            report_lines.append("No expired SITE services.")

        report_lines.extend([
            "",
            f"Total expired: {len(expired_services)}",
            "",
            "=" * 70,
            "VM STATUS",
            "=" * 70,
        ])

        # --------------------------------------------------
        # VM section
        # --------------------------------------------------
        vms = list(Vm.objects.all().order_by("hostname"))

        total_vms = len(vms)
        vms_with_hostname = sum(1 for vm in vms if vm.hostname and str(vm.hostname).strip())

        low_space_vms = []

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

        report_lines.extend([
            f"Total VMs: {total_vms}",
            f"VMs with hostname: {vms_with_hostname}",
            "",
            "VMs with less than 10% free space",
            "-" * 70,
        ])

        if low_space_vms:
            report_lines.extend(low_space_vms)
        else:
            report_lines.append("No VMs with less than 10% free space.")

        report_lines.extend([
            "",
            f"Total VMs with low space: {len(low_space_vms)}",
            "",
            "=" * 70,
        ])

        # --------------------------------------------------
        # Save report
        # --------------------------------------------------
        output_dir = Path(settings.BASE_DIR) / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        file_path = output_dir / "run_morning_cron_report.txt"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        self.stdout.write(self.style.SUCCESS(f"Report saved to: {file_path}"))
