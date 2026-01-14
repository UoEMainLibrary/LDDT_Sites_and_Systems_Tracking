from datetime import date, datetime

from django.core.management.base import BaseCommand

from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import ( RunReportRequest, DateRange, Metric, Dimension, OrderBy, FilterExpression, Filter)
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
        client = self.get_admin_client()
        properties = []

        accounts = client.list_accounts()
        for account in accounts:
            account_id = account.name.split("/")[-1]  # e.g. accounts/123 -> 123
            request = {"filter": f"parent:accounts/{account_id}"}

            for prop in client.list_properties(request=request):
                properties.append(
                    {
                        "id": prop.name.split("/")[-1],
                        "name": prop.display_name,
                    }
                )

        return properties

    def fetch_active_users(self, property_id, start_date, end_date):
        client = self.get_data_client()

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[Metric(name="activeUsers")],
        )

        response = client.run_report(request)

        if not response.rows:
            return 0

        return sum(int(row.metric_values[0].value) for row in response.rows)

    def fetch_earliest_data_date(self, property_id):
        """
        Query GA for the earliest date that has active users > 0.
        Returns a string in YYYYMMDD or None if no data.
        """
        client = self.get_data_client()

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date="2015-08-14", end_date="today")],  # <-- changed here
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="activeUsers")],
            order_bys=[OrderBy(dimension={"dimension_name": "date", "order_type": 1})],  # Ascending order by date
            limit=100000,
        )

        response = client.run_report(request)

        if not response.rows:
            return None

        for row in response.rows:
            date_str = row.dimension_values[0].value  # 'YYYYMMDD'
            active_users = int(row.metric_values[0].value)
            if active_users > 0:
                return date_str

        return None

    # ---------- Django command ----------

    def handle(self, *args, **kwargs):
        today = date.today()

        properties = self.list_all_properties()
        self.stdout.write(f"Found {len(properties)} GA4 properties")

        for prop in properties:
            daily_users = self.fetch_active_users(prop["id"], "yesterday", "yesterday")

            monthly_users = self.fetch_active_users(prop["id"], "30daysAgo", "today")

            earliest_date_str = self.fetch_earliest_data_date(prop["id"])
            earliest_date = (
                datetime.strptime(earliest_date_str, "%Y%m%d").date()
                if earliest_date_str
                else None
            )

            GoogleAnalyticsStats.objects.update_or_create(
                property_id=prop["id"],
                date=today,
                defaults={
                    "property_name": prop["name"],
                    "daily_users": daily_users,
                    "monthly_users": monthly_users,
                    "earliest_data_date": earliest_date,
                },
            )

            self.stdout.write(
                self.style.SUCCESS(f"✔ Synced {prop['name']} ({prop['id']})")
            )