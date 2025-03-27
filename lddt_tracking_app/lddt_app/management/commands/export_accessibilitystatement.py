import csv
from django.core.management.base import BaseCommand
from lddt_app.models import * # Replace with your actual model

class Command(BaseCommand):
    help = 'Export data from SQLite to CSV'

    def handle(self, *args, **kwargs):
        # Define the file path for the CSV file
        file_path = 'export_AccessStatement.csv'

        # Open or create the CSV file
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Get the headers from your model fields
            headers = [field.name for field in AccessStatement._meta.fields]
            writer.writerow(headers)  # Write headers to the CSV file

            # Query the data from the model
            for obj in AccessStatement.objects.all():
                writer.writerow([getattr(obj, field) for field in headers])


        self.stdout.write(self.style.SUCCESS(f'Data exported successfully to {file_path}'))