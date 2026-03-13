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
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    OrderBy,
    RunReportRequest,
)
from google.oauth2 import service_account

from lddt_app.models import GoogleAnalyticsStats


CREDENTIALS_PATH = "credentional/google_analytics_sa.json"
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
API_THROTTLE_SECONDS = 0.05


class Command(BaseCommand):
    help = "Sync Google Analytics GA4 stats safely (users + engaged sessions, retries, one row per property)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._credentials_obj = None
        self._admin_client = None
        self._data_client = None

    # ------------------------------------------------------------------
    # Clients
    # ------------------------------------------------------------------

    def _credentials(self):
        if self._credentials_obj is None:
            self._credentials_obj = service_account.Credentials.from_service_account_file(
                CREDENTIALS_PATH,
                scopes=SCOPES,
            )
        return self._credentials_obj

    def get_admin_client(self):
        if self._admin_client is None:
            self._admin_client = AnalyticsAdminServiceClient(credentials=self._credentials())
        return self._admin_client

    def get_data_client(self):
        if self._data_client is None:
            self._data_client = BetaAnalyticsDataClient(credentials=self._credentials())
        return self._data_client

    # ------------------------------------------------------------------
    # Retry helpers
    # ------------------------------------------------------------------

    def _is_server_errors_quota_429(self, exc: Exception) -> bool:
        """
        GA Data API can return a special 429 mentioning 'server errors quota'.
        That one should not be retried aggressively.
        """
        return isinstance(exc, gexc.ResourceExhausted) and "server errors quota" in str(exc).lower()

    def run_report_with_retry(self, request, *, max_attempts=4, base_delay=1.0):
        client = self.get_data_client()

        for attempt in range(1, max_attempts + 1):
            try:
                response = client.run_report(request)
                if API_THROTTLE_SECONDS:
                    time.sleep(API_THROTTLE_SECONDS)
                return response

            except gexc.ResourceExhausted as e:
                if self._is_server_errors_quota_429(e):
                    raise

                if attempt == max_attempts:
                    raise

                sleep_s = min(base_delay * (2 ** (attempt - 1)) + random.random(), 15)
                self.stdout.write(
                    self.style.WARNING(
                        f"GA quota/rate transient error "
                        f"(attempt {attempt}/{max_attempts}): {e}. "
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

                sleep_s = min(base_delay * (2 ** (attempt - 1)) + random.random(), 30)
                self.stdout.write(
                    self.style.WARNING(
                        f"GA API transient error "
                        f"(attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {sleep_s:.1f}s..."
                    )
                )
                time.sleep(sleep_s)

    # ------------------------------------------------------------------
    # Property helpers
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Metric helpers
    # ------------------------------------------------------------------

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def fetch_metric(self, property_id, metric_name, start_date, end_date):
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[Metric(name=metric_name)],
        )

        response = self.run_report_with_retry(request)

        if not response.rows:
            return 0

        try:
            return self._safe_int(response.rows[0].metric_values[0].value, default=0)
        except (IndexError, AttributeError):
            return 0

    def fetch_active_users(self, property_id, start_date, end_date):
        return self.fetch_metric(property_id, "activeUsers", start_date, end_date)

    def fetch_engaged_sessions(self, property_id, start_date, end_date):
        return self.fetch_metric(property_id, "engagedSessions", start_date, end_date)

    def fetch_users_and_sessions(self, property_id, start_date, end_date):
        """
        Fetch activeUsers and engagedSessions in one API call.
        """
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="engagedSessions"),
            ],
        )

        response = self.run_report_with_retry(request)

        if not response.rows:
            return 0, 0

        row = response.rows[0]

        try:
            users = self._safe_int(row.metric_values[0].value, default=0)
        except (IndexError, AttributeError):
            users = 0

        try:
            sessions = self._safe_int(row.metric_values[1].value, default=0)
        except (IndexError, AttributeError):
            sessions = 0

        return users, sessions

    # ------------------------------------------------------------------
    # Date helpers
    # ------------------------------------------------------------------

    def fetch_earliest_data_date(self, property_id):
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date="2016-01-01", end_date="today")],
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="activeUsers")],
            order_bys=[
                OrderBy(
                    dimension=OrderBy.DimensionOrderBy(dimension_name="date"),
                    desc=False,
                )
            ],
            limit=1,
        )

        response = self.run_report_with_retry(request)

        if not response.rows:
            return None

        try:
            return response.rows[0].dimension_values[0].value  # YYYYMMDD
        except (IndexError, AttributeError):
            return None

    def parse_ga_date(self, value):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y%m%d").date()
        except (TypeError, ValueError):
            return None

    def get_month_date_range(self, today, months_ago):
        """
        Returns:
            month_key, month_start, month_end

        Current month:
            first day of month -> today

        Previous months:
            full calendar month
        """
        month_date = today - relativedelta(months=months_ago)
        month_start = month_date.replace(day=1)

        if month_date.year == today.year and month_date.month == today.month:
            month_end = today
        else:
            next_month_start = month_start + relativedelta(months=1)
            month_end = next_month_start - timedelta(days=1)

        month_key = month_start.strftime("%Y-%m")
        return month_key, month_start, month_end

    # ------------------------------------------------------------------
    # Main
    # ------------------------------------------------------------------

    def handle(self, *args, **kwargs):
        today = timezone.localdate()
        properties = self.list_all_properties()

        self.stdout.write(f"Found {len(properties)} GA4 properties")

        for prop in properties:
            property_id = str(prop["id"]).strip()
            property_name = prop["name"]

            try:
                self.stdout.write(f"Syncing {property_name} ({property_id})...")

                # high-level aggregates
                daily_users = self.fetch_active_users(property_id, "yesterday", "yesterday")
                monthly_users = self.fetch_active_users(property_id, "30daysAgo", "today")

                # earliest date: reuse cached value if already present
                existing = GoogleAnalyticsStats.objects.filter(property_id=property_id).first()

                if existing and existing.earliest_data_date:
                    earliest_date = existing.earliest_data_date
                else:
                    try:
                        earliest_date = self.parse_ga_date(
                            self.fetch_earliest_data_date(property_id)
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Could not fetch earliest date for "
                                f"{property_name} ({property_id}): {e}"
                            )
                        )
                        earliest_date = None

                # monthly time series
                monthly_users_data = {}
                monthly_sessions_data = {}

                for i in range(12):
                    month_key, start_date, end_date = self.get_month_date_range(today, i)

                    users, sessions = self.fetch_users_and_sessions(
                        property_id=property_id,
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d"),
                    )

                    monthly_users_data[month_key] = users
                    monthly_sessions_data[month_key] = sessions

                defaults = {
                    "property_name": property_name,
                    "date": today,  # last sync date
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
                            defaults=defaults,
                        )
                except IntegrityError:
                    GoogleAnalyticsStats.objects.filter(
                        property_id=property_id
                    ).update(**defaults)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✔ Synced {property_name} ({property_id}) | "
                        f"date={today}, daily_users={daily_users}, monthly_users={monthly_users}"
                    )
                )

            except gexc.ResourceExhausted as e:
                if self._is_server_errors_quota_429(e):
                    self.stdout.write(
                        self.style.ERROR(
                            f"✖ Skipping {property_name} ({property_id}) due to "
                            f"GA 'server errors quota' 429. Try again later."
                        )
                    )
                    continue

                self.stdout.write(
                    self.style.ERROR(
                        f"✖ Failed {property_name} ({property_id}) with quota error: {e}"
                    )
                )
                continue

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✖ Failed {property_name} ({property_id}): {e}")
                )
                continue