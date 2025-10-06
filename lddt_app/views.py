from datetime import datetime
from django.db.models import Q
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import *
from .filters import WebsiteFilter, VmFilter, shortwebsiteFilter, shortvmFilter
from .models import *
from datetime import *


from django.http import JsonResponse
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric, Dimension
from google.oauth2 import service_account
import os


# Create your views here.
@login_required
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

def websites_home(request):
    # ----------------------------------
    websites = Website.objects.filter(
        Q(type__name__exact="SITE") & ~Q(activity__name__exact="DECOMMISSIONED")
    ).order_by('ssl_expiry_date')
    # ----------------------------------
    table_item_count_sites = Website.objects.filter(
        Q(type__name__exact="SITE") & ~Q(activity__name__exact="DECOMMISSIONED")
    ).count
    # ----------------------------------
    myFilter = WebsiteFilter(request.GET, queryset=websites)
    shortFilter = shortwebsiteFilter(request.GET, queryset=websites)
    websites = myFilter.qs
    # ----------------------------------
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
    # ----------------------------------
    websites = Website.objects.filter(
        Q(type__name__exact="SITE")
    ).order_by('ssl_expiry_date')
    # ----------------------------------
    table_item_count_sites = Website.objects.filter(
        Q(type__name__exact="SITE")
    ).count
    # ----------------------------------
    myFilter = WebsiteFilter(request.GET, queryset=websites)
    shortFilter = shortwebsiteFilter(request.GET, queryset=websites)
    websites = myFilter.qs
    # ----------------------------------
    current_datetime_now = datetime.now()
    current_datetime_now_tostring = current_datetime_now.strftime("%Y/%B")


    return render(request, 'website/websites_expiry_this_month.html', {
        'websites' : websites,
        'myFilter': myFilter,
        'shortFilter': shortFilter,
        'table_item_count_sites': table_item_count_sites,
        'current_datetime_now_tostring': current_datetime_now_tostring,


    })

def websites_investigate_decommissioned(request):
    # ----------------------------------
    websites = Website.objects.filter(
        Q(type__name__exact="SITE") & Q(activity__name__exact="INVESTIGATE") | Q(activity__name__exact="DECOMMISSIONED")
    ).order_by('ssl_expiry_date')
    # ----------------------------------
    table_item_count_sites = Website.objects.filter(
        Q(type__name__exact="SITE")
    ).count
    # ----------------------------------
    myFilter = WebsiteFilter(request.GET, queryset=websites)
    shortFilter = shortwebsiteFilter(request.GET, queryset=websites)
    websites = myFilter.qs
    # ----------------------------------
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

    # ----------------------------------
    websites = Website.objects.filter(
        ~Q(activity__name__exact="DECOMMISSIONED") & Q(ga4_required__name__exact="Yes")
    ).order_by('ssl_expiry_date')
    # ----------------------------------
    table_item_count = Website.objects.filter(
        ~Q(activity__name__exact="DECOMMISSIONED") & Q(ga4_required__name__exact="Yes")
    ).count
    # ----------------------------------
    myFilter = WebsiteFilter(request.GET, queryset=websites)
    shortFilter = shortwebsiteFilter(request.GET, queryset=websites)
    websites = myFilter.qs
    # ----------------------------------
    current_datetime_now = datetime.now()
    current_datetime_now_tostring = current_datetime_now.strftime("%Y/%B")
    return render(request, 'website/websites_google_analytics.html', {
        'websites' : websites,
        'myFilter': myFilter,
        'shortFilter': shortFilter,
        'table_item_count': table_item_count,
        'current_datetime_now_tostring': current_datetime_now_tostring,
    })

def websites_process_2(request):
    return render(request, 'website/websites_process_2.html')

def ga4_report(request):
    KEY_FILE = os.path.join(os.path.dirname(__file__), "../../ga4access.json")
    PROPERTY_ID = "382924447"

    credentials = service_account.Credentials.from_service_account_file(KEY_FILE)
    client = BetaAnalyticsDataClient(credentials=credentials)

    request_obj = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="city")],
        metrics=[Metric(name="activeUsers")],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
    )

    response = client.run_report(request_obj)

    # Convert GA response to a simple list of dicts
    data = [
        {"city": row.dimension_values[0].value,
         "activeUsers": row.metric_values[0].value}
        for row in response.rows
    ]

    return render(request, "ga4_reports.html", {"data": data})


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

    #ssl_date = Website.ssl_date

    return render(request, 'website/subsites_home.html', {
        'websites' : websites,
        'myFilter': myFilter,
        'shortFilter': shortFilter,
        'table_item_count_subsites': table_item_count_subsites,


    })

def tutorials_home(request):
    return render(request, 'tutorials/tutorials_home.html')

def what_ssl_certificate(request):
    return render(request, 'tutorials/what_ssl_cert.html')

def renew_existing_certificate(request):
    return render(request, 'tutorials/renew_existing_certificate.html')

def tech_docs_home(request):
    return render(request, 'tech_docs/tech_docs_home.html')



def websites_full_table(request):
    websites = Website.objects.all()
    vms = Vm.objects.all()
    table_item_count_sites = Website.objects.all().count
    table_item_count_vms = Vm.objects.all().count
    myFilter = WebsiteFilter(request.GET, queryset=websites)
    shortFilter = shortwebsiteFilter(request.GET, queryset=websites)
    websites = myFilter.qs

    #ssl_date = Website.ssl_date

    return render(request, 'website/website_full_table.html', {
        'websites' : websites,
        'vms' : vms,
        'myFilter': myFilter,
        'shortFilter': shortFilter,
        'table_item_count_sites': table_item_count_sites,
        'table_item_count_vms': table_item_count_vms,
    })

def website_details(request, id):
    website = Website.objects.get(id=id)
    return render(request, 'website/website_details.html', {'website': website})

def subsite_details(request, id):
    website = Website.objects.get(id=id)
    return render(request, 'website/subsite_details.html', {'website': website})


def create_website(request):
    website_form = WebsiteForm(request.POST or None)
    if website_form.is_valid():
        website_form.save()
        return redirect('websites_home')

    return render(request, 'website_form.html', {'website_form': website_form})


def create_subsite(request):
    website_form = WebsiteForm(request.POST or None)
    if website_form.is_valid():
        website_form.save()
        return redirect('lddt_subsites_home')

    return render(request, 'subsite_form.html', {'website_form': website_form})

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






def vm_home(request):
    vms = Vm.objects.all()
    table_item_count_vms = Vm.objects.all().count
    myFilter = VmFilter(request.GET, queryset=vms)
    shortFilter = shortvmFilter(request.GET, queryset=vms)
    vms = myFilter.qs

    return render(request, 'vm/vms_home.html', {
        'vms':vms,
        'myFilter': myFilter,
        'shortFilter': shortFilter,
        'table_item_count_vms': table_item_count_vms,
    })

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
    return render(request, 'vm/vms_investigate.html',{
        'vms_investigate_status': vms_investigate_status,
        'vms_investigate_status_count': vms_investigate_status_count,
    })




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


def access_statement_home(request):
    access_statements = AccessStatement.objects.all()
    access_statements_all_count = AccessStatement.objects.all().count
    return render(request, 'access_statement/access_statement_home.html', {
        'access_statements' : access_statements,
        'access_statements_all_count' : access_statements_all_count,
    })

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

    return render(request, 'create_access_statement_form.html', {'access_statement_form': access_statement_form, 'access_statement': access_statement})

def delete_statement(request, id):
    access_statement = AccessStatement.objects.get(id=id)

    if request.method == 'POST':
        access_statement.delete()
        return redirect('access_statement_home')

    return render(request, 'access_statement/delete_statement.html', {'access_statement': access_statement})