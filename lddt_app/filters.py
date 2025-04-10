import django_filters

from .models import *
from datetime import timedelta
from django.db.models import F, Case, When, BooleanField
from django_filters import rest_framework as filters




class WebsiteFilter(django_filters.FilterSet):
    class Meta:
        model = Website
        fields = '__all__'


class VmFilter(django_filters.FilterSet):
    class Meta:
        model = Vm
        fields = '__all__'



class shortwebsiteFilter(django_filters.FilterSet):
    class Meta:
        model = Website
        fields = [
            'calc_ping_field',
            'type',
            'tech_status',
            'ssl_expiry_date',
            'vm_ip_address',
            'url',
            'server',
            'port',
            'environment',
            'ours',
            'activity',
            'common_name',
        ]
class shortvmFilter(django_filters.FilterSet):
    class Meta:
        model = Vm
        fields = [
            'hostname',
            'ip_address',
            'application',
            'httpd_last_patch',
            'data_centre',
            'puppet_controlled',
            'httpd',
        ]