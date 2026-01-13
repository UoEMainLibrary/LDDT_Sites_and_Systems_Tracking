from .ga4 import fetch_ga4_stats
from datetime import datetime
from ..models import AnalyticsStat

def sync_analytics_data():
    response = fetch_ga4_stats()

    for row in response.rows:
        date_str = row.dimension_values[0].value
        date = datetime.strptime(date_str, "%Y%m%d").date()

        AnalyticsStat.objects.update_or_create(
            date=date,
            defaults={
                "active_users": int(row.metric_values[0].value),
                "sessions": int(row.metric_values[1].value),
                "page_views": int(row.metric_values[2].value),
            }
        )