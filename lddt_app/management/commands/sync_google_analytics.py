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
    help = "Sync Google Analytics GA4 stats (users + engaged sessions)"

    # ---------- Clients ----------

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

    # ---------- Properties ----------

    def list_all_properties(self):
        client = self.get_admin_client()
        properties = []

        for account in client.list_accounts():
            account_id = account.name.split("/")[-1]
            request = {"filter": f"parent:accounts/{account_id}"}

            for prop in client.list_properties(request=request):
                properties.append({
                    "id": prop.name.split("/")[-1],
                    "name": prop.display_name,
                })

        return properties

    # ---------- Metrics ----------

    def fetch_metric(self, property_id, metric_name, start_date, end_date):
        client = self.get_data_client()

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[Metric(name=metric_name)],
        )

        response = client.run_report(request)

        if not response.rows:
            return 0

        return sum(int(row.metric_values[0].value) for row in response.rows)

    def fetch_active_users(self, property_id, start_date, end_date):
        return self.fetch_metric(property_id, "activeUsers", start_date, end_date)

    def fetch_engaged_sessions(self, property_id, start_date, end_date):
        # ✅ Bot-resistant sessions
        return self.fetch_metric(property_id, "engagedSessions", start_date, end_date)

    # ---------- Earliest Data ----------

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

        return response.rows[0].dimension_values[0].value  # YYYYMMDD

    # ---------- Main ----------

    def handle(self, *args, **kwargs):
        today = date.today()
        properties = self.list_all_properties()

        self.stdout.write(f"Found {len(properties)} GA4 properties")

        for prop in properties:
            property_id = prop["id"]

            daily_users = self.fetch_active_users(property_id, "yesterday", "yesterday")
            monthly_users = self.fetch_active_users(property_id, "30daysAgo", "today")

            earliest_date_str = self.fetch_earliest_data_date(property_id)
            earliest_date = (
                datetime.strptime(earliest_date_str, "%Y%m%d").date()
                if earliest_date_str
                else None
            )

            monthly_users_data = {}
            monthly_sessions_data = {}

            for i in range(12):
                month_date = today - relativedelta(months=i)
                start_month = month_date.replace(day=1).strftime("%Y-%m-%d")

                next_month = month_date.replace(day=28) + timedelta(days=4)
                last_day = (next_month - timedelta(days=next_month.day)).strftime("%Y-%m-%d")

                month_key = month_date.strftime("%Y-%m")

                monthly_users_data[month_key] = self.fetch_active_users(
                    property_id, start_month, last_day
                )

                monthly_sessions_data[month_key] = self.fetch_engaged_sessions(
                    property_id, start_month, last_day
                )

            GoogleAnalyticsStats.objects.update_or_create(
                property_id=property_id,
                date=today,
                defaults={
                    "property_name": prop["name"],
                    "daily_users": daily_users,
                    "monthly_users": monthly_users,
                    "earliest_data_date": earliest_date,
                    "monthly_users_data": monthly_users_data,
                    "monthly_sessions_data": monthly_sessions_data,
                },
            )

            self.stdout.write(
                self.style.SUCCESS(f"✔ Synced {prop['name']} ({property_id})")
            )
