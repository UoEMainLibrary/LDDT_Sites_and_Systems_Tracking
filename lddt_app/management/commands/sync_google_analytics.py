from datetime import date

from django.core.management.base import BaseCommand

from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Metric,
)
from google.oauth2 import service_account

from lddt_app.models import GoogleAnalyticsStats


CREDENTIALS_PATH = "credentional/google_analytics_sa.json"
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


class Command(BaseCommand):
    help = "Sync Google Analytics stats for all GA4 properties"

    # ---------- Google clients ----------

    def get_admin_client(self):
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH,
            scopes=SCOPES,
        )
        return AnalyticsAdminServiceClient(credentials=credentials)

    def get_data_client(self):
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH,
            scopes=SCOPES,
        )
        return BetaAnalyticsDataClient(credentials=credentials)

    # ---------- GA logic ----------

    def list_all_properties(self):
        """
        List all GA4 properties accessible by the service account.
        Works by:
          - Listing all accounts
          - Listing properties for each account individually
        """

        client = self.get_admin_client()
        properties = []

        # List accounts
        accounts = client.list_accounts()

        for account in accounts:
            account_id = account.name.split('/')[-1]  # e.g. accounts/123 -> 123

            request = {
                "filter": f"parent:accounts/{account_id}"
            }

            # List properties under this account
            for prop in client.list_properties(request=request):
                properties.append({
                    "id": prop.name.split("/")[-1],
                    "name": prop.display_name,
                })

        return properties

    def fetch_active_users(self, property_id, start_date, end_date):
        client = self.get_data_client()

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[
                DateRange(start_date=start_date, end_date=end_date)
            ],
            metrics=[
                Metric(name="activeUsers"),
            ],
        )

        response = client.run_report(request)

        if not response.rows:
            return 0

        return sum(
            int(row.metric_values[0].value)
            for row in response.rows
        )

    # ---------- Django command ----------

    def handle(self, *args, **kwargs):
        today = date.today()

        properties = self.list_all_properties()
        self.stdout.write(f"Found {len(properties)} GA4 properties")

        for prop in properties:
            daily_users = self.fetch_active_users(
                prop["id"], "yesterday", "yesterday"
            )

            monthly_users = self.fetch_active_users(
                prop["id"], "30daysAgo", "today"
            )

            GoogleAnalyticsStats.objects.update_or_create(
                property_id=prop["id"],
                date=today,
                defaults={
                    "property_name": prop["name"],
                    "daily_users": daily_users,
                    "monthly_users": monthly_users,
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✔ Synced {prop['name']} ({prop['id']})"
                )
            )