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

API_THROTTLE_SECONDS = 0.05


class Command(BaseCommand):
    help = "Sync GA4 stats with minimal API calls (only missing months/current month)"

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
        msg = str(exc).lower()
        return isinstance(exc, gexc.ResourceExhausted) and "server errors quota" in msg

    def run_report_with_retry(self, client, request, *, max_attempts=3, base_delay=1.0):
        for attempt in range(1, max_attempts + 1):
            try:
                resp = client.run_report(request)
                if API_THROTTLE_SECONDS:
                    time.sleep(API_THROTTLE_SECONDS)
                return resp

            except gexc.ResourceExhausted as e:
                if self._is_server_errors_quota_429(e):
                    raise
                if attempt == max_attempts:
                    raise
                sleep_s = min(base_delay * (2 ** (attempt - 1)) + random.random(), 10)
                self.stdout.write(
                    self.style.WARNING(
                        f"GA quota/rate transient error (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {sleep_s:.1f}s..."
                    )
                )
                time.sleep(sleep_s)

            except (
                gexc.InternalServerError,
                gexc.ServiceUnavailable,
                gexc.DeadlineExceeded,
                gexc.Aborted,
                gexc.Unknown,
            ) as e:
                if attempt == max_attempts:
                    raise
                sleep_s = min(base_delay * (2 ** (attempt - 1)) + random.random(), 20)
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

    # ---------- GA fetch helpers ----------

    def fetch_single_metric(self, property_id, metric_name, start_date, end_date) -> int:
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

    def fetch_users_and_sessions(self, property_id, start_date, end_date):
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

    # ---------- Date helpers ----------

    def month_start_end(self, d):
        start = d.replace(day=1)
        next_month = d.replace(day=28) + timedelta(days=4)
        last = next_month - timedelta(days=next_month.day)
        return start.strftime("%Y-%m-%d"), last.strftime("%Y-%m-%d")

    # ---------- Main ----------

    def handle(self, *args, **kwargs):
        today = timezone.localdate()
        current_month_key = today.strftime("%Y-%m")
        prev_month_key = (today - relativedelta(months=1)).strftime("%Y-%m")

        properties = self.list_all_properties()
        self.stdout.write(f"Found {len(properties)} GA4 properties")

        for prop in properties:
            property_id = str(prop["id"]).strip()
            property_name = prop["name"]

            try:
                # Pull last known row for this property (to reuse stored data)
                existing = (
                    GoogleAnalyticsStats.objects
                    .filter(property_id=property_id)
                    .order_by("-date")
                    .first()
                )

                monthly_users_data = dict(existing.monthly_users_data) if existing else {}
                monthly_sessions_data = dict(existing.monthly_sessions_data) if existing else {}
                earliest_date = existing.earliest_data_date if (existing and existing.earliest_data_date) else None

                # Always refresh these summary numbers
                daily_users = self.fetch_single_metric(property_id, "activeUsers", "yesterday", "yesterday")
                monthly_users = self.fetch_single_metric(property_id, "activeUsers", "30daysAgo", "today")

                # Only fetch earliest date once, ever
                if earliest_date is None:
                    try:
                        earliest_date_str = self.fetch_earliest_data_date(property_id)
                        earliest_date = (
                            datetime.strptime(earliest_date_str, "%Y%m%d").date()
                            if earliest_date_str
                            else None
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"⚠ Earliest date failed for {property_name} ({property_id}): {e}")
                        )
                        earliest_date = None

                # Only fetch the current month (and optionally previous month if missing)
                # Current month is always “in progress” so refresh it every run.
                start_month, end_month = self.month_start_end(today)
                users, sessions = self.fetch_users_and_sessions(property_id, start_month, end_month)
                monthly_users_data[current_month_key] = users
                monthly_sessions_data[current_month_key] = sessions

                # Optional: If it's early in the month, previous month numbers may still be settling
                # Also fetch previous month if we don't have it yet
                should_refresh_prev = (today.day <= 3) or (prev_month_key not in monthly_users_data)
                if should_refresh_prev:
                    prev_date = today - relativedelta(months=1)
                    prev_start, prev_end = self.month_start_end(prev_date)
                    u2, s2 = self.fetch_users_and_sessions(property_id, prev_start, prev_end)
                    monthly_users_data[prev_month_key] = u2
                    monthly_sessions_data[prev_month_key] = s2

                defaults = {
                    "property_name": property_name,
                    "daily_users": daily_users,
                    "monthly_users": monthly_users,
                    "earliest_data_date": earliest_date,
                    "monthly_users_data": monthly_users_data,
                    "monthly_sessions_data": monthly_sessions_data,
                }

                try:
                    with transaction.atomic():
                        GoogleAnalyticsStats.objects.update_or_create(
                            property_id=property_id,
                            date=today,
                            defaults=defaults,
                        )
                except IntegrityError:
                    GoogleAnalyticsStats.objects.filter(property_id=property_id, date=today).update(**defaults)

                self.stdout.write(self.style.SUCCESS(f"✔ Synced {property_name} ({property_id})"))

            except gexc.ResourceExhausted as e:
                if self._is_server_errors_quota_429(e):
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