import random
import time
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.utils import timezone

from google.api_core import exceptions as gexc
from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric
from google.oauth2 import service_account

from lddt_app.models import GoogleAnalyticsStats


CREDENTIALS_PATH = "credentional/google_analytics_sa.json"
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

# Gentle throttling to avoid bursty behavior (tune if needed)
API_THROTTLE_SECONDS = 0.05


class Command(BaseCommand):
    help = "Sync Google Analytics GA4 stats (users + engaged sessions) safely (retries + no duplicates)"

    # ---------- Clients ----------

    def _credentials(self):
        return service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH,
            scopes=SCOPES,
        )

    def get_admin_client(self):
        return AnalyticsAdminServiceClient(credentials=self._credentials())

    def get_data_client(self):
        return BetaAnalyticsDataClient(credentials=self._credentials())

    # ---------- Retry wrapper ----------

    def _is_server_errors_quota_429(self, exc: Exception) -> bool:
        """
        GA Data API uses a special 429 when you've exhausted the 'server errors quota'
        due to too many upstream 5xx errors. Retrying aggressively makes it worse.
        """
        msg = str(exc).lower()
        return isinstance(exc, gexc.ResourceExhausted) and "server errors quota" in msg

    def run_report_with_retry(self, client, request, *, max_attempts=4, base_delay=1.0):
        """
        Retries transient GA Data API errors (500/503/timeouts).
        Does NOT retry 'server errors quota' 429s.
        """
        for attempt in range(1, max_attempts + 1):
            try:
                resp = client.run_report(request)
                if API_THROTTLE_SECONDS:
                    time.sleep(API_THROTTLE_SECONDS)
                return resp

            except gexc.ResourceExhausted as e:
                # If it's the special "server errors quota" 429, stop immediately.
                if self._is_server_errors_quota_429(e):
                    raise
                # Other ResourceExhausted can sometimes be brief; retry a little.
                if attempt == max_attempts:
                    raise
                sleep_s = min(base_delay * (2 ** (attempt - 1)) + random.random(), 15)
                self.stdout.write(
                    self.style.WARNING(
                        f"GA quota/rate transient error (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {sleep_s:.1f}s..."
                    )
                )
                time.sleep(sleep_s)

            except (
                gexc.InternalServerError,   # 500
                gexc.ServiceUnavailable,    # 503
                gexc.DeadlineExceeded,      # timeout
                gexc.Aborted,
                gexc.Unknown,
            ) as e:
                if attempt == max_attempts:
                    raise
                sleep_s = min(base_delay * (2 ** (attempt - 1)) + random.random(), 30)
                self.stdout.write(
                    self.style.WARNING(
                        f"GA API transient error (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {sleep_s:.1f}s..."
                    )
                )
                time.sleep(sleep_s)

    # ---------- Properties ----------

    def list_all_properties(self):
        client = self.get_admin_client()
        properties = []

        for account in client.list_accounts():
            account_id = account.name.split("/")[-1]
            request = {"filter": f"parent:accounts/{account_id}"}

            for prop in client.list_properties(request=request):
                properties.append(
                    {
                        "id": prop.name.split("/")[-1],
                        "name": prop.display_name,
                    }
                )

        return properties

    # ---------- Metrics ----------

    def fetch_metric(self, property_id, metric_name, start_date, end_date):
        client = self.get_data_client()

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[Metric(name=metric_name)],
        )

        response = self.run_report_with_retry(client, request)

        if not response.rows:
            return 0

        try:
            return int(response.rows[0].metric_values[0].value)
        except (TypeError, ValueError, IndexError):
            return 0

    def fetch_active_users(self, property_id, start_date, end_date):
        return self.fetch_metric(property_id, "activeUsers", start_date, end_date)

    def fetch_engaged_sessions(self, property_id, start_date, end_date):
        return self.fetch_metric(property_id, "engagedSessions", start_date, end_date)

    def fetch_users_and_sessions(self, property_id, start_date, end_date):
        """
        Fetches activeUsers + engagedSessions in ONE call (cuts API calls ~50% for monthly loop).
        """
        client = self.get_data_client()

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[Metric(name="activeUsers"), Metric(name="engagedSessions")],
        )

        response = self.run_report_with_retry(client, request)

        if not response.rows:
            return 0, 0

        row = response.rows[0]
        try:
            users = int(row.metric_values[0].value)
        except (TypeError, ValueError, IndexError):
            users = 0
        try:
            sessions = int(row.metric_values[1].value)
        except (TypeError, ValueError, IndexError):
            sessions = 0

        return users, sessions

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

        response = self.run_report_with_retry(client, request)

        if not response.rows:
            return None

        return response.rows[0].dimension_values[0].value  # YYYYMMDD

    # ---------- Main ----------

    def handle(self, *args, **kwargs):
        today = timezone.localdate()
        properties = self.list_all_properties()

        self.stdout.write(f"Found {len(properties)} GA4 properties")

        for prop in properties:
            property_id = str(prop["id"]).strip()
            property_name = prop["name"]

            try:
                daily_users = self.fetch_active_users(property_id, "yesterday", "yesterday")
                monthly_users = self.fetch_active_users(property_id, "30daysAgo", "today")

                # Cache earliest date (don’t call GA again if we already know it)
                existing = (
                    GoogleAnalyticsStats.objects
                    .filter(property_id=property_id)
                    .exclude(earliest_data_date__isnull=True)
                    .order_by("-date")
                    .first()
                )

                if existing and existing.earliest_data_date:
                    earliest_date = existing.earliest_data_date
                else:
                    try:
                        earliest_date_str = self.fetch_earliest_data_date(property_id)
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠ Earliest date failed for {property_name} ({property_id}): {e}"
                            )
                        )
                        earliest_date_str = None

                    earliest_date = (
                        datetime.strptime(earliest_date_str, "%Y%m%d").date()
                        if earliest_date_str
                        else None
                    )

                monthly_users_data = {}
                monthly_sessions_data = {}

                # 12 months, but each month is ONE call for both metrics
                for i in range(12):
                    month_date = today - relativedelta(months=i)
                    start_month = month_date.replace(day=1).strftime("%Y-%m-%d")

                    next_month = month_date.replace(day=28) + timedelta(days=4)
                    last_day = (next_month - timedelta(days=next_month.day)).strftime("%Y-%m-%d")

                    month_key = month_date.strftime("%Y-%m")

                    users, sessions = self.fetch_users_and_sessions(property_id, start_month, last_day)
                    monthly_users_data[month_key] = users
                    monthly_sessions_data[month_key] = sessions

                defaults = {
                    "property_name": property_name,
                    "daily_users": daily_users,
                    "monthly_users": monthly_users,
                    "earliest_data_date": earliest_date,
                    "monthly_users_data": monthly_users_data,
                    "monthly_sessions_data": monthly_sessions_data,
                }

                # race-safe upsert
                try:
                    with transaction.atomic():
                        GoogleAnalyticsStats.objects.update_or_create(
                            property_id=property_id,
                            date=today,
                            defaults=defaults,
                        )
                except IntegrityError:
                    GoogleAnalyticsStats.objects.filter(
                        property_id=property_id,
                        date=today,
                    ).update(**defaults)

                self.stdout.write(self.style.SUCCESS(f"✔ Synced {property_name} ({property_id})"))

            except gexc.ResourceExhausted as e:
                if self._is_server_errors_quota_429(e):
                    # Don’t keep hammering Google; skip and continue.
                    self.stdout.write(
                        self.style.ERROR(
                            f"✖ Skipping {property_name} ({property_id}) due to GA 'server errors quota' 429. "
                            f"Try again later (tokens refill in under an hour)."
                        )
                    )
                    continue
                self.stdout.write(self.style.ERROR(f"✖ Failed {property_name} ({property_id}): {e}"))
                continue

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✖ Failed {property_name} ({property_id}): {e}"))
                continue