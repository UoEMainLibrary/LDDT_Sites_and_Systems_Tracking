from django.contrib import admin
from .models import Website, \
    Vm, \
    AccessStatement, \
    Type, Tech_Status, \
    Group, Activity, \
    Cert_Manager, \
    SSL_Cert_Process, \
    access_statement_y_n, \
    Testing_Status_r, \
    Statement_Status_r, \
    ga4_y_n, \
    Tasked_to, \
    ga4_required, \
    vm_type, \
    vm_status


from import_export.admin import ImportExportModelAdmin

# Register your models here.

@admin.register(Website)
class WebsiteAdmin(ImportExportModelAdmin):
    list_display = [
        'ssl_expiry_date',
        'url',
        'type',
        'function',
        'activity',
        'server',
        'vm_ip_address',
        'vulnerability_checked',
        'personal_data_held',
        'port',
        'load_balancer',
        'ours',
        'environment',
        'ssl_type',
        'ease_expiry',
        'application',
        'restore_action',
        'user',
        'major_user',
        'external_support',
        'expected_response',
        'handle_prefix',
        'accessibility_statement',
        #'group',
        'notes',
        'calc_ping_field',
        'ga4_y_n',
        'ga4_required',
    ]

@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Activity)
class TypeAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Tech_Status)
class Tech_StatusAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(SSL_Cert_Process)
class Tech_StatusAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Cert_Manager)
class Tech_StatusAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name']\

@admin.register(access_statement_y_n)
class access_statement_y_nAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(ga4_y_n)
class ga4_y_nAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(ga4_required)
class ga4_requiredAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Vm)
class VmAdmin(ImportExportModelAdmin):
    list_display = [
        'ip_address',
        'application',
        'vm_type',
        'vm_status',
        'ssh_in_lp',
        'puppet_controlled',
        'data_centre',
        'poodle_checked',
        'log4shell_risk',
        'trace_risk',
        'httpd_last_patch',
        'os_centos_assumed',
        'httpd',
        'tomcat',
        'nginx',
        'ram',
        'cpu',
        'db',
        'php',
        'java',
        'vm_storage',
        'special_mounts',
        'python',
        'npm',
        'shibboleth',
        'ssl',
        'notes'
    ]

@admin.register(Testing_Status_r)
class Testing_Status_rAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(vm_type)
class vm_type_rAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(vm_status)
class vm_status_rAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Statement_Status_r)
class Statement_Status_rAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Tasked_to)
class Tasked_toAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(AccessStatement)
class AccessStatementAdmin(ImportExportModelAdmin):
    list_display = [
        'url',
        'site',
        'word21',
        'jira_nr',
        'wa_statement_tasked_to',
        'wa_statement_tasked_to_last',
        'site',
        'owning_team',
        'content_service_manager',
        'tech_contact',
        'architecture',
        'physical_location_server',
        'physical_location_directory_file',
        'how_deploy',
        'testing_status_r',
        'access_statement_status',
        'access_statement_status_r',
    ]


