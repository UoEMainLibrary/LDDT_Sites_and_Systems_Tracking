from django.core.management.base import BaseCommand
from django.utils import timezone

from lddt_app.models import Vm


class Command(BaseCommand):
    help = "Copy SSH-fetched VM values into the main VM fields and stamp cron run time"

    def handle(self, *args, **kwargs):
        total = Vm.objects.count()
        current = 0
        updated = 0
        skipped = 0
        now = timezone.now()

        for obj in Vm.objects.all():
            current += 1

            self.stdout.write(f"Checking {obj.hostname} ({current} of {total})")

            if not obj.fetch_details:
                skipped += 1
                self.stdout.write(f"Skipped {obj.hostname} because fetch_details is disabled")
                self.stdout.write("***********************************")
                continue

            self.stdout.write(f"Updating {obj.hostname} ({current} of {total})")

            details = obj.fetch_ssh_details()

            if details is None:
                skipped += 1
                self.stdout.write(f"Skipped {obj.hostname} because fetch_details is disabled")
                self.stdout.write("***********************************")
                continue

            if details.get("error"):
                skipped += 1
                self.stdout.write(f"Skipped {obj.hostname}: {details['error']}")
                self.stdout.write("Existing values were left unchanged")
                self.stdout.write("***********************************")
                continue

            obj.db = details["db"]
            obj.nginx = details["nginx"]
            obj.puppet_controlled = details["puppet_controlled"]
            obj.httpd = details["httpd"]
            obj.vmfs_root_used = details["vmfs_root_used"]
            obj.vmfs_apps_used = details["vmfs_apps_used"]
            obj.vmfs_data_used = details["vmfs_data_used"]
            obj.ip_address = details["ip_address"]
            obj.processors = details["processors"]
            obj.memory = details["memory"]
            obj.last_patch_days_ago = details["last_patch_days_ago"]
            obj.system_check = details["system_check"]
            obj.last_health_check = now
            obj.last_cron_run = now

            obj.save(update_fields=[
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
            ])
            updated += 1

            self.stdout.write(f"Updated {obj.hostname}")
            self.stdout.write("***********************************")

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished. Total: {total}, Updated: {updated}, Skipped: {skipped}"
            )
        )
