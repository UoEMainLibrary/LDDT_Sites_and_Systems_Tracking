from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.utils import timezone

from lddt_app.models import Website, Type  # change your_app


class Command(BaseCommand):
    help = "Generate TXT SSL report for Website objects with type=SITE only"

    def handle(self, *args, **options):
        now = timezone.now()
        today = now.date()
        week_from_now = today + timedelta(days=7)

        report_lines = [
            "=" * 70,
            "TRACKING REPORT",
            f"Generated at: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 70,
        ]

        # --------------------------------------------------
        # Run update_ssl_dates FIRST
        # --------------------------------------------------
        try:
            call_command("update_ssl_dates")

        except Exception as e:
            report_lines.append(f"update_ssl_dates: FAILED ({e})")

        report_lines.append("")

        # --------------------------------------------------
        # Get SITE type
        # --------------------------------------------------
        try:
            site_type = Type.objects.get(name="SITE")
        except Type.DoesNotExist:
            self.stderr.write(self.style.ERROR('Type "SITE" does not exist.'))
            return
        except Type.MultipleObjectsReturned:
            self.stderr.write(self.style.ERROR('More than one Type with name "SITE" exists.'))
            return

        # Only SITE websites
        site_websites = list(
            Website.objects.select_related("type")
            .filter(type_id=site_type.id)
            .order_by("url")
        )

        # --------------------------------------------------
        # Update ssl_expiry_date_new ONLY for SITE
        # --------------------------------------------------
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

        # Refresh list
        site_websites = list(
            Website.objects.select_related("type")
            .filter(type_id=site_type.id)
            .order_by("url")
        )

        total_services = len(site_websites)

        # --------------------------------------------------
        # Expiring / expired
        # --------------------------------------------------
        expiring_this_week = [
            w for w in site_websites
            if w.ssl_expiry_date_new
            and today <= w.ssl_expiry_date_new <= week_from_now
        ]
        expiring_this_week.sort(key=lambda x: (x.ssl_expiry_date_new, x.url or ""))

        expired_services = [
            w for w in site_websites
            if w.ssl_expiry_date_new
            and w.ssl_expiry_date_new < today
        ]
        expired_services.sort(key=lambda x: (x.ssl_expiry_date_new, x.url or ""))

        # --------------------------------------------------
        # Build report
        # --------------------------------------------------
        report_lines.extend([
            "-" * 70,
            "SSL CERTIFICATES STATUS:",
            f"Total: {updated_count} services",
            f"Failed updates: {failed_count}",
            "Services expiring this week",

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
            "Services with expired date:",
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
            f"Total expired: {len(expired_services)}",
            "-" * 70,
        ])

        # --------------------------------------------------
        # Save file (overwrite to avoid confusion)
        # --------------------------------------------------
        output_dir = Path(settings.BASE_DIR) / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        file_path = output_dir / "site_ssl_report.txt"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        self.stdout.write(self.style.SUCCESS(f"Report saved to: {file_path}"))
