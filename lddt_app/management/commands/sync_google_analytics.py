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
    help = (
        "Sync Google Analytics GA4 statistics, monthly data "
        "and GA4 web-stream Measurement IDs."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._credentials_obj = None
        self._admin_client = None
        self._data_client = None

    # ------------------------------------------------------------------
    # Clients
    # ------------------------------------------------------------------

    def _credentials(self):
        """
        Load and cache Google service-account credentials.
        """
        if self._credentials_obj is None:
            self._credentials_obj = (
                service_account.Credentials.from_service_account_file(
                    CREDENTIALS_PATH,
                    scopes=SCOPES,
                )
            )

        return self._credentials_obj

    def get_admin_client(self):
        """
        Return a cached Google Analytics Admin API client.
        """
        if self._admin_client is None:
            self._admin_client = AnalyticsAdminServiceClient(
                credentials=self._credentials()
            )

        return self._admin_client

    def get_data_client(self):
        """
        Return a cached Google Analytics Data API client.
        """
        if self._data_client is None:
            self._data_client = BetaAnalyticsDataClient(
                credentials=self._credentials()
            )

        return self._data_client

    # ------------------------------------------------------------------
    # Retry helpers
    # ------------------------------------------------------------------

    def _is_server_errors_quota_429(self, exc):
        """
        Detect the special GA Data API 429 server-errors quota response.

        This error should not be retried aggressively because repeated calls
        can make the quota problem worse.
        """
        return (
            isinstance(exc, gexc.ResourceExhausted)
            and "server errors quota" in str(exc).lower()
        )

    def run_report_with_retry(
        self,
        request,
        *,
        max_attempts=4,
        base_delay=1.0,
    ):
        """
        Run a GA Data API report with exponential backoff for transient
        API errors.
        """
        client = self.get_data_client()

        for attempt in range(1, max_attempts + 1):
            try:
                response = client.run_report(request=request)

                if API_THROTTLE_SECONDS:
                    time.sleep(API_THROTTLE_SECONDS)

                return response

            except gexc.ResourceExhausted as exc:
                if self._is_server_errors_quota_429(exc):
                    raise

                if attempt == max_attempts:
                    raise

                sleep_seconds = min(
                    base_delay * (2 ** (attempt - 1)) + random.random(),
                    15,
                )

                self.stdout.write(
                    self.style.WARNING(
                        "GA quota/rate transient error "
                        f"(attempt {attempt}/{max_attempts}): {exc}. "
                        f"Retrying in {sleep_seconds:.1f} seconds..."
                    )
                )

                time.sleep(sleep_seconds)

            except (
                gexc.InternalServerError,
                gexc.ServiceUnavailable,
                gexc.DeadlineExceeded,
                gexc.Aborted,
                gexc.Unknown,
            ) as exc:
                if attempt == max_attempts:
                    raise

                sleep_seconds = min(
                    base_delay * (2 ** (attempt - 1)) + random.random(),
                    30,
                )

                self.stdout.write(
                    self.style.WARNING(
                        "GA API transient error "
                        f"(attempt {attempt}/{max_attempts}): {exc}. "
                        f"Retrying in {sleep_seconds:.1f} seconds..."
                    )
                )

                time.sleep(sleep_seconds)

        raise RuntimeError("GA report failed without returning a response.")

    # ------------------------------------------------------------------
    # Property and data-stream helpers
    # ------------------------------------------------------------------

    def list_all_properties(self):
        """
        Return all GA4 properties available to the service account.
        """
        client = self.get_admin_client()
        properties = []

        for account in client.list_accounts():
            account_id = account.name.split("/")[-1]

            request = {
                "filter": f"parent:accounts/{account_id}",
            }

            for prop in client.list_properties(request=request):
                properties.append(
                    {
                        "id": prop.name.split("/")[-1],
                        "name": prop.display_name,
                    }
                )

        return properties

    def fetch_measurement_ids(self, property_id):
        """
        Return all unique GA4 web-stream Measurement IDs for a property.

        Example return value:

            [
                "G-ABC1234567",
                "G-XYZ9876543",
            ]

        Android and iOS streams are ignored because they do not use the
        standard web Measurement ID format.
        """
        client = self.get_admin_client()
        measurement_ids = []

        try:
            streams = client.list_data_streams(
                request={
                    "parent": f"properties/{property_id}",
                }
            )

            for stream in streams:
                web_stream_data = getattr(
                    stream,
                    "web_stream_data",
                    None,
                )

                if not web_stream_data:
                    continue

                measurement_id = str(
                    getattr(
                        web_stream_data,
                        "measurement_id",
                        "",
                    )
                    or ""
                ).strip()

                if (
                    measurement_id
                    and measurement_id not in measurement_ids
                ):
                    measurement_ids.append(measurement_id)

        except gexc.PermissionDenied as exc:
            self.stdout.write(
                self.style.WARNING(
                    f"Permission denied when retrieving GA4 tags for "
                    f"property {property_id}: {exc}"
                )
            )

        except gexc.NotFound as exc:
            self.stdout.write(
                self.style.WARNING(
                    f"GA4 property or stream not found for "
                    f"property {property_id}: {exc}"
                )
            )

        except Exception as exc:
            self.stdout.write(
                self.style.WARNING(
                    f"Could not retrieve GA4 Measurement IDs for "
                    f"property {property_id}: {exc}"
                )
            )

        return measurement_ids

    # ------------------------------------------------------------------
    # Metric helpers
    # ------------------------------------------------------------------

    def _safe_int(self, value, default=0):
        """
        Safely convert a GA metric value to an integer.
        """
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def fetch_metric(
        self,
        property_id,
        metric_name,
        start_date,
        end_date,
    ):
        """
        Fetch one aggregate metric for a specified date range.
        """
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[
                DateRange(
                    start_date=start_date,
                    end_date=end_date,
                )
            ],
            metrics=[
                Metric(name=metric_name),
            ],
        )

        response = self.run_report_with_retry(request)

        if not response.rows:
            return 0

        try:
            value = response.rows[0].metric_values[0].value
            return self._safe_int(value, default=0)

        except (IndexError, AttributeError):
            return 0

    def fetch_active_users(
        self,
        property_id,
        start_date,
        end_date,
    ):
        """
        Fetch active users for a specified date range.
        """
        return self.fetch_metric(
            property_id=property_id,
            metric_name="activeUsers",
            start_date=start_date,
            end_date=end_date,
        )

    def fetch_engaged_sessions(
        self,
        property_id,
        start_date,
        end_date,
    ):
        """
        Fetch engaged sessions for a specified date range.
        """
        return self.fetch_metric(
            property_id=property_id,
            metric_name="engagedSessions",
            start_date=start_date,
            end_date=end_date,
        )

    def fetch_users_sessions_and_views(
        self,
        property_id,
        start_date,
        end_date,
    ):
        """
        Fetch active users, sessions and screen/page views in one request.
        """
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[
                DateRange(
                    start_date=start_date,
                    end_date=end_date,
                )
            ],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
                Metric(name="screenPageViews"),
            ],
        )

        response = self.run_report_with_retry(request)

        if not response.rows:
            return 0, 0, 0

        try:
            row = response.rows[0]

            users = self._safe_int(
                row.metric_values[0].value,
                default=0,
            )

            sessions = self._safe_int(
                row.metric_values[1].value,
                default=0,
            )

            views = self._safe_int(
                row.metric_values[2].value,
                default=0,
            )

            return users, sessions, views

        except (IndexError, AttributeError):
            return 0, 0, 0

    # ------------------------------------------------------------------
    # Date helpers
    # ------------------------------------------------------------------

    def fetch_earliest_data_date(self, property_id):
        """
        Return the first date on which the property recorded active users.

        The returned value from GA uses YYYYMMDD format.
        """
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[
                DateRange(
                    start_date="2016-01-01",
                    end_date="today",
                )
            ],
            dimensions=[
                Dimension(name="date"),
            ],
            metrics=[
                Metric(name="activeUsers"),
            ],
            order_bys=[
                OrderBy(
                    dimension=OrderBy.DimensionOrderBy(
                        dimension_name="date"
                    ),
                    desc=False,
                )
            ],
            limit=1,
        )

        response = self.run_report_with_retry(request)

        if not response.rows:
            return None

        try:
            return response.rows[0].dimension_values[0].value

        except (IndexError, AttributeError):
            return None

    def parse_ga_date(self, value):
        """
        Convert a GA date in YYYYMMDD format to a Python date object.
        """
        if not value:
            return None

        try:
            return datetime.strptime(
                value,
                "%Y%m%d",
            ).date()

        except (TypeError, ValueError):
            return None

    def get_month_date_range(self, today, months_ago):
        """
        Return:

            month_key, month_start, month_end

        For the current month, month_end is today.

        For previous months, the complete calendar month is returned.
        """
        month_date = today - relativedelta(months=months_ago)
        month_start = month_date.replace(day=1)

        if (
            month_date.year == today.year
            and month_date.month == today.month
        ):
            month_end = today

        else:
            next_month_start = (
                month_start
                + relativedelta(months=1)
            )

            month_end = (
                next_month_start
                - timedelta(days=1)
            )

        month_key = month_start.strftime("%Y-%m")

        return month_key, month_start, month_end

    # ------------------------------------------------------------------
    # Main
    # ------------------------------------------------------------------

    def handle(self, *args, **kwargs):
        """
        Synchronise all available GA4 properties.
        """
        today = timezone.localdate()

        try:
            properties = self.list_all_properties()

        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(
                    f"Could not retrieve GA4 properties: {exc}"
                )
            )
            return

        self.stdout.write(
            f"Found {len(properties)} GA4 properties"
        )

        synced_count = 0
        failed_count = 0

        for current_number, prop in enumerate(
            properties,
            start=1,
        ):
            property_id = str(prop["id"]).strip()
            property_name = str(prop["name"] or "").strip()

            try:
                self.stdout.write(
                    f"Syncing {property_name} "
                    f"({property_id}) "
                    f"[{current_number}/{len(properties)}]..."
                )

                # ------------------------------------------------------
                # GA4 Measurement IDs
                # ------------------------------------------------------

                measurement_ids = self.fetch_measurement_ids(
                    property_id
                )

                # ------------------------------------------------------
                # High-level aggregates
                # ------------------------------------------------------

                daily_users = self.fetch_active_users(
                    property_id=property_id,
                    start_date="yesterday",
                    end_date="yesterday",
                )

                monthly_users = self.fetch_active_users(
                    property_id=property_id,
                    start_date="30daysAgo",
                    end_date="today",
                )

                # ------------------------------------------------------
                # Earliest recorded GA4 date
                # ------------------------------------------------------

                existing = (
                    GoogleAnalyticsStats.objects
                    .filter(property_id=property_id)
                    .first()
                )

                if existing and existing.earliest_data_date:
                    earliest_date = existing.earliest_data_date

                else:
                    try:
                        earliest_date = self.parse_ga_date(
                            self.fetch_earliest_data_date(
                                property_id
                            )
                        )

                    except Exception as exc:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Could not fetch earliest date for "
                                f"{property_name} ({property_id}): "
                                f"{exc}"
                            )
                        )

                        earliest_date = None

                # ------------------------------------------------------
                # Monthly time series
                # ------------------------------------------------------

                monthly_users_data = {}
                monthly_sessions_data = {}
                monthly_views_data = {}

                for months_ago in range(12):
                    (
                        month_key,
                        start_date,
                        end_date,
                    ) = self.get_month_date_range(
                        today=today,
                        months_ago=months_ago,
                    )

                    (
                        users,
                        sessions,
                        views,
                    ) = self.fetch_users_sessions_and_views(
                        property_id=property_id,
                        start_date=start_date.strftime(
                            "%Y-%m-%d"
                        ),
                        end_date=end_date.strftime(
                            "%Y-%m-%d"
                        ),
                    )

                    monthly_users_data[month_key] = users
                    monthly_sessions_data[month_key] = sessions
                    monthly_views_data[month_key] = views

                # ------------------------------------------------------
                # Save or update the database record
                # ------------------------------------------------------

                defaults = {
                    "property_name": property_name,
                    "date": today,
                    "last_synced_at": timezone.now(),
                    "daily_users": daily_users,
                    "monthly_users": monthly_users,
                    "earliest_data_date": earliest_date,
                    "monthly_users_data": monthly_users_data,
                    "monthly_sessions_data": monthly_sessions_data,
                    "monthly_views_data": monthly_views_data,
                    "ga4_measurement_ids": measurement_ids,
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

                measurement_ids_text = (
                    ", ".join(measurement_ids)
                    if measurement_ids
                    else "No web-stream Measurement ID"
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✔ Synced {property_name} "
                        f"({property_id}) | "
                        f"GA4 tags: {measurement_ids_text} | "
                        f"date={today}, "
                        f"daily_users={daily_users}, "
                        f"monthly_users={monthly_users}"
                    )
                )

                synced_count += 1

            except gexc.ResourceExhausted as exc:
                failed_count += 1

                if self._is_server_errors_quota_429(exc):
                    self.stdout.write(
                        self.style.ERROR(
                            f"✖ Skipping {property_name} "
                            f"({property_id}) due to the GA "
                            f"'server errors quota' 429 response. "
                            f"Try again later."
                        )
                    )

                    continue

                self.stdout.write(
                    self.style.ERROR(
                        f"✖ Failed {property_name} "
                        f"({property_id}) with quota error: "
                        f"{exc}"
                    )
                )

            except gexc.PermissionDenied as exc:
                failed_count += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"✖ Permission denied for "
                        f"{property_name} ({property_id}): "
                        f"{exc}"
                    )
                )

            except Exception as exc:
                failed_count += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"✖ Failed {property_name} "
                        f"({property_id}): {exc}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"GA4 synchronisation finished. "
                f"Synced: {synced_count}. "
                f"Failed: {failed_count}. "
                f"Total: {len(properties)}."
            )
        )