from datetime import datetime
from django.db.models import Q
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import *
from .filters import WebsiteFilter, VmFilter, shortwebsiteFilter, shortvmFilter
from .models import *
from datetime import *
from django.db.models import Max, Min
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from io import BytesIO
import base64
from datetime import date, timedelta, datetime
from datetime import date, timedelta, datetime
import calendar
from django.core.cache import cache
from django.utils import timezone  # ✅  correct import
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.management import call_command

from django.shortcuts import render
from django.http import JsonResponse
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, RunRealtimeReportRequest, DateRange, Metric
from google.oauth2 import service_account
import os
from google.analytics.data_v1beta import (
    BetaAnalyticsDataClient,
    RunReportRequest,
    RunRealtimeReportRequest,
    DateRange,
    Metric,
    Dimension,  # ✅  ADDED
)

import logging
logger = logging.getLogger(__name__)

@login_required
#######################################################################################################################
# ---------------------------------------------------------------------------------------------------------------------
#                                                    HOME
# ---------------------------------------------------------------------------------------------------------------------
#######################################################################################################################
def home(request):
    # --------------websites
    websites = Website.objects.filter(
        Q(type__name__exact="SITE") & ~Q(activity__name__exact="DECOMMISSIONED")
    ).order_by('ssl_expiry_date')
    count_all_sites = Website.objects.filter(
        Q(type__name__exact="SITE")
    ).count
    count_all_active = Website.objects.filter(
        Q(type__name__exact="SITE") & Q(activity__name__exact="ACTIVE")
    ).count
    count_sites_workingon = Website.objects.filter(
        Q(type__name__exact="SITE") & Q(tech_status__name__exact="WORKING ON")
    ).count
    count_sites_cert_sent = Website.objects.filter(
        Q(type__name__exact="SITE") & Q(tech_status__name__exact="CERT SENT")
    ).count

    count_sites_issue = Website.objects.filter(
        Q(type__name__exact="SITE") & Q(tech_status__name__exact="ISSUE")
    ).count
    # -----------------subsites
    count_all_subsites = Website.objects.filter(Q(type__name__exact="SUB-SITE")).count
    count_all_active_subsites = Website.objects.filter(
        Q(type__name__exact="SUB-SITE") & Q(activity__name__exact="ACTIVE")
    ).count
    count_subsites_workingon = Website.objects.filter(
        Q(type__name__exact="SUB-SITE") & Q(tech_status__name__exact="WORKING ON")
    ).count
    count_subsites_issue = Website.objects.filter(
        Q(type__name__exact="SUB-SITE") & Q(tech_status__name__exact="ISSUE")
    ).count
    # -----------------vm's
    table_item_count_vms = Vm.objects.all().count
    vms_working_on_status_count = Vm.objects.filter(
        Q(vm_type__name__exact="VM") & Q(vm_status__name__exact="Working On")
    ).count

    current_datetime_now = datetime.now()
    current_datetime_now_tostring = current_datetime_now

    return render(request, 'index.html', {
        'count_all_sites': count_all_sites,
        'count_all_active': count_all_active,
        'count_sites_workingon': count_sites_workingon,
        'count_sites_issue': count_sites_issue,
        'websites': websites,
        # subsites
        'count_all_subsites': count_all_subsites,
        'count_all_active_subsites': count_all_active_subsites,
        'count_subsites_workingon': count_subsites_workingon,
        'count_subsites_issue': count_subsites_issue,
        'current_datetime_now_tostring': current_datetime_now_tostring,
        # vm's
        'table_item_count_vms': table_item_count_vms,
        'count_sites_cert_sent': count_sites_cert_sent,
        'vms_working_on_status_count': vms_working_on_status_count,

    })

#######################################################################################################################
# ---------------------------------------------------------------------------------------------------------------------
#                                                    WEBSITES
# ---------------------------------------------------------------------------------------------------------------------
#######################################################################################################################

def websites_home(request):
    websites = Website.objects.filter(
        Q(type__name__exact="SITE") & ~Q(activity__name__exact="DECOMMISSIONED")
    ).order_by('ssl_expiry_date')
    table_item_count_sites = Website.objects.filter(
        Q(type__name__exact="SITE") & ~Q(activity__name__exact="DECOMMISSIONED")
    ).count
    myFilter = WebsiteFilter(request.GET, queryset=websites)
    shortFilter = shortwebsiteFilter(request.GET, queryset=websites)
    websites = myFilter.qs
    current_datetime_now = datetime.now()
    current_datetime_now_tostring = current_datetime_now.strftime("%Y/%B")

    return render(request, 'website/websites_home.html', {
        'websites': websites,
        'myFilter': myFilter,
        'shortFilter': shortFilter,
        'table_item_count_sites': table_item_count_sites,
        'current_datetime_now_tostring': current_datetime_now_tostring,
    })


def websites_ssl_exp_this_month(request):
    websites = Website.objects.filter(
        Q(type__name__exact="SITE")
    ).order_by('ssl_expiry_date')
    table_item_count_sites = Website.objects.filter(
        Q(type__name__exact="SITE")
    ).count
    myFilter = WebsiteFilter(request.GET, queryset=websites)
    shortFilter = shortwebsiteFilter(request.GET, queryset=websites)
    websites = myFilter.qs
    current_datetime_now = datetime.now()
    current_datetime_now_tostring = current_datetime_now.strftime("%Y/%B")

    return render(request, 'website/websites_expiry_this_month.html', {
        'websites': websites,
        'myFilter': myFilter,
        'shortFilter': shortFilter,
        'table_item_count_sites': table_item_count_sites,
        'current_datetime_now_tostring': current_datetime_now_tostring,
    })


def websites_investigate_decommissioned(request):
    websites = Website.objects.filter(
        Q(type__name__exact="SITE") & Q(activity__name__exact="INVESTIGATE") | Q(activity__name__exact="DECOMMISSIONED")
    ).order_by('ssl_expiry_date')
    table_item_count_sites = Website.objects.filter(
        Q(type__name__exact="SITE")
    ).count
    myFilter = WebsiteFilter(request.GET, queryset=websites)
    shortFilter = shortwebsiteFilter(request.GET, queryset=websites)
    websites = myFilter.qs
    current_datetime_now = datetime.now()
    current_datetime_now_tostring = current_datetime_now.strftime("%Y/%B")
    return render(request, 'website/websites_investigate_decommissioned.html', {
        'websites': websites,
        'myFilter': myFilter,
        'shortFilter': shortFilter,
        'table_item_count_sites': table_item_count_sites,
        'current_datetime_now_tostring': current_datetime_now_tostring,
    })


def websites_google_analytics(request):
    websites = Website.objects.filter(
        ~Q(activity__name__exact="DECOMMISSIONED") & Q(ga4_required__name__exact="Yes")
    ).order_by('ssl_expiry_date')
    table_item_count = Website.objects.filter(
        ~Q(activity__name__exact="DECOMMISSIONED") & Q(ga4_required__name__exact="Yes")
    ).count
    myFilter = WebsiteFilter(request.GET, queryset=websites)
    shortFilter = shortwebsiteFilter(request.GET, queryset=websites)
    websites = myFilter.qs
    current_datetime_now = datetime.now()
    current_datetime_now_tostring = current_datetime_now.strftime("%Y/%B")
    return render(request, 'website/websites_google_analytics.html', {
        'websites': websites,
        'myFilter': myFilter,
        'shortFilter': shortFilter,
        'table_item_count': table_item_count,
        'current_datetime_now_tostring': current_datetime_now_tostring,
    })


def websites_full_table(request):
    websites = Website.objects.all()
    vms = Vm.objects.all()
    table_item_count_sites = Website.objects.all().count
    table_item_count_vms = Vm.objects.all().count
    myFilter = WebsiteFilter(request.GET, queryset=websites)
    shortFilter = shortwebsiteFilter(request.GET, queryset=websites)
    websites = myFilter.qs

    # ssl_date = Website.ssl_date

    return render(request, 'website/website_full_table.html', {
        'websites': websites,
        'vms': vms,
        'myFilter': myFilter,
        'shortFilter': shortFilter,
        'table_item_count_sites': table_item_count_sites,
        'table_item_count_vms': table_item_count_vms,
    })


def websites_process_2(request):
    return render(request, 'website/websites_process_2.html')


############################# WEBSITES CRUD
def create_website(request):
    website_form = WebsiteForm(request.POST or None)
    if website_form.is_valid():
        website_form.save()
        return redirect('websites_home')
    return render(request, 'website_form.html', {'website_form': website_form})


def website_details(request, id):
    website = Website.objects.get(id=id)
    return render(request, 'website/website_details.html', {'website': website})


def update_website(request, id):
    website = Website.objects.get(id=id)
    website_form = WebsiteForm(request.POST or None, instance=website)

    if website_form.is_valid():
        website_form.save()
        return redirect('websites_home')

    return render(request, 'website_form.html', {'website_form': website_form, 'website': website})


def delete_website(request, id):
    website = Website.objects.get(id=id)
    if request.method == 'POST':
        website.delete()
        return redirect('websites_home')

    return render(request, 'website/website_delete_confirmation.html', {'website': website})

#######################################################################################################################
# ---------------------------------------------------------------------------------------------------------------------
#                                                    SUBSITES
# ---------------------------------------------------------------------------------------------------------------------
#######################################################################################################################
def lddt_subsites_home(request):
    websites = Website.objects.filter(
        Q(type__name__exact="SUB-SITE")
    )
    table_item_count_subsites = Website.objects.filter(
        Q(type__name__exact="SUB-SITE")
    ).count
    myFilter = WebsiteFilter(request.GET, queryset=websites)
    shortFilter = shortwebsiteFilter(request.GET, queryset=websites)
    websites = myFilter.qs

    return render(request, 'website/subsites_home.html', {
        'websites': websites,
        'myFilter': myFilter,
        'shortFilter': shortFilter,
        'table_item_count_subsites': table_item_count_subsites,
    })

############################# SUB-SITES CRUD

def subsite_details(request, id):
    website = Website.objects.get(id=id)
    return render(request, 'website/subsite_details.html', {'website': website})


def create_subsite(request):
    website_form = WebsiteForm(request.POST or None)
    if website_form.is_valid():
        website_form.save()
        return redirect('lddt_subsites_home')

    return render(request, 'subsite_form.html', {'website_form': website_form})


#######################################################################################################################
# ---------------------------------------------------------------------------------------------------------------------
#                                                    VM's
# ---------------------------------------------------------------------------------------------------------------------
#######################################################################################################################

def vm_home(request):
    vms = Vm.objects.all()
    table_item_count_vms = Vm.objects.all().count
    myFilter = VmFilter(request.GET, queryset=vms)
    shortFilter = shortvmFilter(request.GET, queryset=vms)
    vms = myFilter.qs

    return render(request, 'vm/vms_home.html', {
        'vms': vms,
        'myFilter': myFilter,
        'shortFilter': shortFilter,
        'table_item_count_vms': table_item_count_vms,
    })

@require_POST
def run_vm_update(request):
    try:
        call_command('script_copy_properties')
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def vms_working_on(request):
    vms_working_on_status = Vm.objects.filter(
        Q(vm_type__name__exact="VM") & Q(vm_status__name__exact="Working On")
    )
    vms_working_on_status_count = Vm.objects.filter(
        Q(vm_type__name__exact="VM") & Q(vm_status__name__exact="Working On")
    ).count
    return render(request, 'vm/vms_working_on.html', {
        'vms_working_on_status': vms_working_on_status,
        'vms_working_on_status_count': vms_working_on_status_count,
    })


def vms_investigate(request):
    vms_investigate_status = Vm.objects.filter(
        Q(vm_type__name__exact="VM") & Q(vm_status__name__exact="Investigate")
    )
    vms_investigate_status_count = Vm.objects.filter(
        Q(vm_type__name__exact="VM") & Q(vm_status__name__exact="Investigate")
    ).count
    return render(request, 'vm/vms_investigate.html', {
        'vms_investigate_status': vms_investigate_status,
        'vms_investigate_status_count': vms_investigate_status_count,
    })


############################# VM's CRUD

def vm_details(request, id):
    vm = Vm.objects.get(id=id)
    return render(request, 'vm/vm_details.html', {'vm': vm})


def create_vm(request):
    vm_form = VmForm(request.POST or None)
    if vm_form.is_valid():
        vm_form.save()
        return redirect('vms_home')
    return render(request, 'vm_form.html', {'vm_form': vm_form})


def update_vm(request, id):
    vm = Vm.objects.get(id=id)
    vm_form = VmForm(request.POST or None, instance=vm)

    if vm_form.is_valid():
        vm_form.save()
        return redirect('vms_home')

    return render(request, 'vm_form.html', {'vm_form': vm_form, 'vm': vm})


def delete_vm(request, id):
    vm = Vm.objects.get(id=id)

    if request.method == 'POST':
        vm.delete()
        return redirect('vms_home')

    return render(request, 'vm/vm_delete_confirmation.html', {'vm': vm})


#######################################################################################################################
# ---------------------------------------------------------------------------------------------------------------------
#                                                    TUTORIALS
# ---------------------------------------------------------------------------------------------------------------------
#######################################################################################################################

def tutorials_home(request):
    return render(request, 'tutorials/tutorials_home.html')


#######################################################################################################################
# ---------------------------------------------------------------------------------------------------------------------
#                                                    WHAT CERTIFICATE
# ---------------------------------------------------------------------------------------------------------------------
#######################################################################################################################

def what_ssl_certificate(request):
    return render(request, 'tutorials/what_ssl_cert.html')


#######################################################################################################################
# ---------------------------------------------------------------------------------------------------------------------
#                                                    RENEW
# ---------------------------------------------------------------------------------------------------------------------
#######################################################################################################################

def renew_existing_certificate(request):
    return render(request, 'tutorials/renew_existing_certificate.html')


#######################################################################################################################
# ---------------------------------------------------------------------------------------------------------------------
#                                                    TECHNICAL DOCUMENTATION
# ---------------------------------------------------------------------------------------------------------------------
#######################################################################################################################

def tech_docs_home(request):
    return render(request, 'tech_docs/tech_docs_home.html')


#######################################################################################################################
# ---------------------------------------------------------------------------------------------------------------------
#                                                    ACCESSIBILITY STATEMENT
# ---------------------------------------------------------------------------------------------------------------------
#######################################################################################################################

def access_statement_home(request):
    access_statements = AccessStatement.objects.all()
    access_statements_all_count = AccessStatement.objects.all().count
    return render(request, 'access_statement/access_statement_home.html', {
        'access_statements': access_statements,
        'access_statements_all_count': access_statements_all_count,
    })


############################# ACCESSIBILITY STATEMENT CRUD

def create_access_statement(request):
    access_statement_form = AccessStatementForm(request.POST or None)
    if access_statement_form.is_valid():
        access_statement_form.save()
        return redirect('access_statement_home')
    return render(request, 'create_access_statement_form.html', {
        'access_statement_form': access_statement_form,
    })


def access_statement_details(request, id):
    access_statement = AccessStatement.objects.get(id=id)
    return render(request, 'access_statement/access_statement_details.html', {'access_statement': access_statement})


def update_access_statement(request, id):
    access_statement = AccessStatement.objects.get(id=id)
    access_statement_form = AccessStatementForm(request.POST or None, instance=access_statement)

    if access_statement_form.is_valid():
        access_statement_form.save()
        return redirect('access_statement_home')

    return render(request, 'create_access_statement_form.html',
                  {'access_statement_form': access_statement_form, 'access_statement': access_statement})


def delete_statement(request, id):
    access_statement = AccessStatement.objects.get(id=id)

    if request.method == 'POST':
        access_statement.delete()
        return redirect('access_statement_home')

    return render(request, 'access_statement/delete_statement.html', {'access_statement': access_statement})

#######################################################################################################################
# ---------------------------------------------------------------------------------------------------------------------
#                                                    GOOGLE ANALYTICS GA4
# ---------------------------------------------------------------------------------------------------------------------
#######################################################################################################################

# === CONFIG ===
GA_PROPERTIES = [
    {"name": "Exampapers", "id": "382924447"},
    {"name": "Archives Collections", "id": "367934488"},
    {"name": "Collections", "id": "347147610"},
    {"name": "Lyell", "id": "511195520"},
    {"name": "LHSA", "id": "511237856"},
    {"name": "Walter Scott", "id": "511168474"},
    {"name": "LUCID", "id": "511244975"},
    {"name": "IllustratingScott", "id": "511214007"},
    {"name": "Archives.lib", "id": "511778179"},
    {"name": "Arsanatomica.lib", "id": "511751914"},
    {"name": "Chartingthenation.lib", "id": "511749816"},
    {"name": "Luna", "id": "383741097"},
    {"name": "Leganto", "id": "384843296"},
    {"name": "Library Blogs", "id": "347071499"},
    {"name": "DiscoverED", "id": "370799052"},
    {"name": "Aura", "id": "382911188"},
    {"name": "Era", "id": "391408836"},
    {"name": "HWU", "id": "382928678"},
    {"name": "QMU", "id": "382912134"},
    {"name": "RSC", "id": "382918256"},
    {"name": "STA", "id": "382918682"},
    {"name": "DataShare", "id": "389022533"},
    {"name": "Exhibitions", "id": "384908156"},
    {"name": "Our History", "id": "345202489"},
    {"name": "Statacc", "id": "447420661"},
    {"name": "Ideas", "id": "451235618"},
    {"name": "Digital Colletions", "id": "507278994"},
    {"name": "Images Teaching", "id": "450459257"},
    {"name": "Pizan", "id": "455961874"},
    {"name": "Library Registration", "id": "386789431"},
    {"name": "Mantra", "id": "391409531"},
    {"name": "Pointsofarrival", "id": "350302368"},
    {"name": "Fairbairn", "id": "350314353"},
    {"name": "HIV-aids-resources", "id": "347189427"},
    {"name": "Openbooks", "id": "350304777"},
    {"name": "sjac-collection", "id": "350327347"},
    {"name": "geddes", "id": "350285942"},
    {"name": "collections.ed.ac.uk/art", "id": "518916430"},
    # add more properties here
]

KEY_FILE = os.path.join(os.path.dirname(__file__), "../../ga4access.json")


# === Helper functions ===
def _get_report(client, property_id, metric_name, start_date, end_date):
    """Run a standard GA4 report for sessions, etc."""
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            metrics=[Metric(name=metric_name)],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )
        response = client.run_report(request)
        return int(response.rows[0].metric_values[0].value) if response.rows else 0
    except Exception as e:
        print(f"⚠️ GA4 error for {property_id}: {e}")
        return 0


def _get_first_recorded_date(client, property_id):
    """Get first available date for property data."""
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="sessions")],
            date_ranges=[DateRange(start_date="2015-08-14", end_date="today")],
            order_bys=[{"dimension": {"dimension_name": "date"}, "desc": False}],
            limit=1,
        )
        response = client.run_report(request)
        if response.rows:
            first_date_str = response.rows[0].dimension_values[0].value
            return datetime.strptime(first_date_str, "%Y%m%d").strftime("%Y-%m-%d")
    except Exception as e:
        print(f"⚠️ Error getting first recorded date for {property_id}: {e}")
    return None


def _fetch_ga4_data():
    """Fetch GA4 analytics data for all properties and return dashboard + monthly summaries."""
    logger.info("=== Starting GA4 data fetch ===")

    credentials = service_account.Credentials.from_service_account_file(KEY_FILE)
    client = BetaAnalyticsDataClient(credentials=credentials)

    dashboard_data = []
    monthly_dashboard = []

    today = datetime.today()
    months_list = []

    # ✅ Real 12-month list, from oldest to newest
    for i in range(11, -1, -1):
        dt = (today.replace(day=1) - timedelta(days=i * 30))
        month_start = datetime(dt.year, dt.month, 1)
        months_list.append(month_start.strftime("%Y-%m"))
    logger.info("Months list prepared: %s", months_list)

    for prop in GA_PROPERTIES:
        prop_id = prop["id"]
        prop_name = prop["name"]
        logger.info("Fetching GA4 data for property: %s (%s)", prop_name, prop_id)

        # === Realtime active users ===
        try:
            realtime_request = RunRealtimeReportRequest(
                property=f"properties/{prop_id}",
                metrics=[Metric(name="activeUsers")]
            )
            realtime_response = client.run_realtime_report(realtime_request)
            active_30min = int(realtime_response.rows[0].metric_values[0].value) if realtime_response.rows else 0
            connection_status = "🟢 Connected"
        except Exception as e:
            logger.warning("Realtime report failed for %s: %s", prop_name, e)
            active_30min = 0
            connection_status = "🔴 Not Connected"

        # === Sessions over time ===
        visits_30days = _get_report(client, prop_id, "sessions", "30daysAgo", "today")
        visits_6months = _get_report(client, prop_id, "sessions", "180daysAgo", "today")
        visits_year = _get_report(client, prop_id, "sessions", "365daysAgo", "today")
        first_recorded_date = _get_first_recorded_date(client, prop_id)

        # === Receiving status ===
        if active_30min > 0:
            receiving_status = "🟢 Receiving data now"
        elif visits_30days > 0:
            receiving_status = "🟡 Received data recently"
        else:
            receiving_status = "🔴 No recent data"

        # === Trend analysis ===
        trend = "➖ Steady"
        try:
            if first_recorded_date and visits_30days > 0:
                start_date = datetime.strptime(first_recorded_date, "%Y-%m-%d")
                days_since_start = max((today - start_date).days, 1)
                historical_avg = visits_year / days_since_start
                recent_avg = visits_30days / 30
                if recent_avg > historical_avg * 1.1:
                    trend = "📈 Up"
                elif recent_avg < historical_avg * 0.9:
                    trend = "📉 Down"
        except Exception as e:
            logger.warning("Trend calc error for %s: %s", prop_name, e)

        # === Append to dashboard table ===
        row = {
            "property_name": prop_name,
            "connection_status": connection_status,
            "active_30min": active_30min,
            "visits_30days": visits_30days,
            "visits_6months": visits_6months,
            "visits_year": visits_year,
            "first_recorded_date": first_recorded_date or "N/A",
            "receiving_status": receiving_status,
            "trend": trend,
        }
        dashboard_data.append(row)
        logger.info("Added dashboard row: %s", row)

        # === Monthly visits for chart ===
        monthly_visits = []
        for month_str in months_list:
            year, month = map(int, month_str.split("-"))
            start_of_month = datetime(year, month, 1)
            end_of_month = datetime(year, month, calendar.monthrange(year, month)[1])
            visits = _get_report(
                client, prop_id, "sessions",
                start_of_month.strftime("%Y-%m-%d"),
                end_of_month.strftime("%Y-%m-%d")
            )
            monthly_visits.append(visits)
        monthly_dashboard.append({
            "property_name": prop_name,
            "monthly_visits": monthly_visits
        })
        logger.info("Added monthly data for %s: %s", prop_name, monthly_visits)

    logger.info("=== GA4 data fetch complete — %d properties ===", len(dashboard_data))
    return dashboard_data, monthly_dashboard, months_list


# === Main view ===
def ga4_report(request):
    # Get all property IDs
    property_ids = GoogleAnalyticsStats.objects.values_list('property_id', flat=True).distinct()

    latest_stats = []
    for pid in property_ids:
        latest_date = GoogleAnalyticsStats.objects.filter(property_id=pid).aggregate(Max('date'))['date__max']
        earliest_date = GoogleAnalyticsStats.objects.filter(property_id=pid).aggregate(Min('earliest_data_date'))['earliest_data_date__min']

        stat = GoogleAnalyticsStats.objects.get(property_id=pid, date=latest_date)
        stat.earliest_data_date = earliest_date  # dynamically add to object for template use
        latest_stats.append(stat)

    context = {
        'properties': latest_stats
    }
    return render(request, 'ga4_reports.html', context)
