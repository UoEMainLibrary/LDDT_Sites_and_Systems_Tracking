"""lddt_tracking_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from .views import *
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, re_path, include


urlpatterns = [
   path(r'^$', home, name='home'),
   re_path(r'^login/$', LoginView.as_view(template_name='login.html'), name="login"),
   re_path(r'^logout/$', LogoutView.as_view(template_name='logout.html'), name="logout"),

   re_path(r'^lddt-websites-home/', websites_home, name='websites_home'),
   re_path('create_website/', create_website, name='create_website'),
   re_path('create_subsite/', create_subsite, name='create_subsite'),
   re_path('create_access_statement/', create_access_statement, name='create_access_statement'),
   re_path(r'^website/(\d+)/', website_details, name='website_details'),
   re_path(r'^subsite/(\d+)/', subsite_details, name='subsite_details'),
   path('update_website/<int:id>/', update_website, name='update_website'),
   path('delete_website/<int:id>/', delete_website, name='delete_website'),
   path('websites_full_table/', websites_full_table, name='websites_full_table'),
   path('lddt-subsites-home/', lddt_subsites_home, name='lddt_subsites_home'),
   path('websites_ssl_exp_this_month/', websites_ssl_exp_this_month, name='websites_ssl_exp_this_month'),
   path('websites_investigate_decommissioned/', websites_investigate_decommissioned, name='websites_investigate_decommissioned'),
   path('websites_google_analytics/', websites_google_analytics, name='websites_google_analytics'),
   path('websites_process_2/', websites_process_2, name='websites_process_2'),

   re_path(r'^lddt-vms-home/', vm_home, name='vms_home'),
   re_path(r'^vms_working_on/', vms_working_on, name='vms_working_on'),
   re_path(r'^vms_investigate/', vms_investigate, name='vms_investigate'),
   re_path('create_vm/', create_vm, name='create_vm'),
   re_path(r'^vm/(\d+)/', vm_details, name='vm_details'),
   path('update_vm/<int:id>/', update_vm, name='update_vm'),
   path('delete_vm/<int:id>/', delete_vm, name='delete_vm'),

   path('tutorials_home/', tutorials_home, name='tutorials_home'),
   path('what_ssl_certificate/', what_ssl_certificate, name='what_ssl_certificate'),
   path('renew_existing_certificate/', renew_existing_certificate, name='renew_existing_certificate'),
   path('ga4_report/', ga4_report, name='ga4_report'),


   path('tech_docs_home/', tech_docs_home, name='tech_docs_home'),

   path('access_statement_home/', access_statement_home, name='access_statement_home'),
   re_path('create_access_statement/', create_access_statement, name='create_access_statement'),
   re_path(r'^access_statement/(\d+)/', access_statement_details, name='access_statement_details'),
   path('update_access_statement/<int:id>/', update_access_statement, name='update_access_statement'),
   path('delete_statement/<int:id>/', delete_statement, name='delete_statement'),
]
