from lddt_app.models import AnalyticsStat
from .ga4 import fetch_ga4_stats
from .ga_admin import get_all_ga4_properties

def sync_analytics_data():
    properties = get_all_ga4_properties()

    for prop in properties:
        property_id = prop["property_id"]
        property_name = prop["display_name"]

        response = fetch_ga4_stats(property_id)

        for row in response.rows:
            AnalyticsStat.objects.update_or_create(
                property_id=property_id,
                date=row.dimension_values[0].value,
                defaults={
                    "property_name": property_name,
                    "active_users": int(row.metric_values[0].value),
                    "sessions": int(row.metric_values[1].value),
                    "page_views": int(row.metric_values[2].value),
                }
            )