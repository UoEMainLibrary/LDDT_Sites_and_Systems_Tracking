from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric, Dimension
from google.oauth2 import service_account

# 1️⃣ Path to your service account key file
KEY_FILE = "../../ga4access.json"

# 2️⃣ Your GA4 property ID
PROPERTY_ID = "382924447"

# 3️⃣ Authenticate
credentials = service_account.Credentials.from_service_account_file(KEY_FILE)
client = BetaAnalyticsDataClient(credentials=credentials)

# 4️⃣ Make a simple API request
request = RunReportRequest(
    property=f"properties/{PROPERTY_ID}",
    dimensions=[Dimension(name="country")],
    metrics=[Metric(name="activeUsers")],
    date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
)

response = client.run_report(request)

# 5️⃣ Print results
print("✅ Google Analytics connection successful!\n")
for row in response.rows:
    print(f"{row.dimension_values[0].value}: {row.metric_values[0].value}")