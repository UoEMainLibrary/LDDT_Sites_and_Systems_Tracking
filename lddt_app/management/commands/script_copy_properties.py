from django.core.management.base import BaseCommand
from django.utils import timezone

from lddt_app.models import Vm


class Command(BaseCommand):
    help = "Copy SSH-fetched VM values into the main VM fields and stamp cron run time"

    def handle(self, *args, **kwargs):
        total = Vm.objects.count()
        updated = 0
        skipped = 0
        failed = 0
        now = timezone.now()

        update_fields = [
            "db",
            "nginx",
            "puppet_controlled",
            "httpd",
            "vmfs_root_used",
            "vmfs_apps_used",
            "vmfs_data_used",
            "ip_address",
            "processors",
            "memory",
            "last_patch_days_ago",
            "system_check",
            "last_health_check",
            "last_cron_run",
        ]

        for current, obj in enumerate(Vm.objects.all(), start=1):
            self.stdout.write(f"Checking {obj.hostname} ({current} of {total})")

            if not obj.fetch_details:
                skipped += 1
                self.stdout.write(
                    f"Skipped {obj.hostname} because fetch_details is disabled"
                )
                self.stdout.write("***********************************")
                continue

            self.stdout.write(f"Updating {obj.hostname} ({current} of {total})")

            try:
                details = obj.fetch_all_ssh_details()

                for field_name, value in details.items():
                    setattr(obj, field_name, value)

                obj.last_health_check = now
                obj.last_cron_run = now

                obj.save(update_fields=update_fields)

                updated += 1
                self.stdout.write(self.style.SUCCESS(f"Updated {obj.hostname}"))

            except Exception as e:
                failed += 1
                skipped += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"Skipped {obj.hostname}: SSH detail fetch failed: {e}"
                    )
                )
                self.stdout.write("Existing values were left unchanged")

            self.stdout.write("***********************************")

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished. Total: {total}, Updated: {updated}, "
                f"Skipped: {skipped}, Failed: {failed}"
            )
        )