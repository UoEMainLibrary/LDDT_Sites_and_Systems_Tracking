from django.core.management.base import BaseCommand
from lddt_app.services.sync import sync_analytics_data

class Command(BaseCommand):
    help = "Sync Google Analytics data"

    def handle(self, *args, **kwargs):
        sync_analytics_data()
        self.stdout.write(self.style.SUCCESS("Analytics synced successfully"))