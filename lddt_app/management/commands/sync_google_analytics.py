from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.core.management.base import BaseCommand

from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric
from google.oauth2 import service_account

from lddt_app.models import GoogleAnalyticsStats


CREDENTIALS_PATH = "credentional/google_analytics_sa.json"
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


class Command(BaseCommand):
    help = "Sync Google Analytics stats for all GA4 properties"

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

    def list_all_properties(self):
        client = self.get_admin_client()
        properties = []

        accounts = client.list_accounts()

        for account in accounts:
            account_id = account.name.split('/')[-1]
            request = {"filter": f"parent:accounts/{account_id}"}
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
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[Metric(name="activeUsers")],
        )
        response = client.run_report(request)

        if not response.rows:
            return 0

        return sum(int(row.metric_values[0].value) for row in response.rows)

    def fetch_earliest_data_date(self, property_id):
        client = self.get_data_client()

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date="2016-01-01", end_date="today")],
            dimensions=[{"name": "date"}],
            metrics=[{"name": "activeUsers"}],
            order_bys=[{"dimension": {"dimension_name": "date"}, "desc": False}],
            limit=1,
        )

        response = client.run_report(request)

        if not response.rows:
            return None

        earliest_date_str = response.rows[0].dimension_values[0].value  # e.g., '20220115'
        return earliest_date_str

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

            monthly_data = {}
            for i in range(12):
                month_date = today - relativedelta(months=i)
                start_month = month_date.replace(day=1).strftime("%Y-%m-%d")
                next_month = month_date.replace(day=28) + timedelta(days=4)
                last_day = (next_month - timedelta(days=next_month.day)).strftime("%Y-%m-%d")

                users_count = self.fetch_active_users(prop["id"], start_month, last_day)
                month_key = month_date.strftime("%Y-%m")
                monthly_data[month_key] = users_count

            GoogleAnalyticsStats.objects.update_or_create(
                property_id=prop["id"],
                date=today,
                defaults={
                    "property_name": prop["name"],
                    "daily_users": daily_users,
                    "monthly_users": monthly_users,
                    "earliest_data_date": earliest_date,
                    "monthly_data": monthly_data,
                },
            )

            self.stdout.write(
                self.style.SUCCESS(f"✔ Synced {prop['name']} ({prop['id']})")
            )
