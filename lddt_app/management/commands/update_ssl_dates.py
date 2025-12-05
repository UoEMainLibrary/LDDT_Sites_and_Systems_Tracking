from django.core.management.base import BaseCommand
from lddt_app.models import Website


class Command(BaseCommand):
    help = "Populate ssl_expiry_date_new from ssl_expiration property"

    def handle(self, *args, **kwargs):
        count = Website.objects.count()
        current = 0

        for obj in Website.objects.all():
            current += 1
            self.stdout.write(f"[{current}/{count}] Updating {obj.common_name}")

            expiration = obj.ssl_expiration  # <-- property call

            if expiration:
                obj.ssl_expiry_date_new = expiration
                obj.save(update_fields=["ssl_expiry_date_new"])
                self.stdout.write(f" ✔ Saved {expiration}")
            else:
                self.stdout.write(" ✖ No certificate data")

            self.stdout.write("----------------------------")

        self.stdout.write(self.style.SUCCESS("Finished updating SSL expiration dates."))