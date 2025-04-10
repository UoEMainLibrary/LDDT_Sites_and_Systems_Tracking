from .models import Website, Vm, AccessStatement #Group
from django import forms
from crispy_forms.helper import FormHelper


class WebsiteForm(forms.ModelForm):
    class Meta:
        model = Website

        fields = [
            'ssl_expiry_date',
            'url',
            'activity',
            'common_name',
            'function',
            'server',
            'vm_ip_address',
            'type',
            'tech_status',
            'cert_manager',
            'ssl_cert_process',
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
            'ssl_certificate_action',
            'user',
            'major_user',
            'external_support',
            'expected_response',
            'handle_prefix',
            'accessibility_statement',
            'access_statement_y_n',
            #'group',
            'notes',
            'ga4_required',
            'ga4_y_n',
            'ga4_notes',
            'ga4_path',
        ]


        help_texts = {
            "ssl_expiry_date": (
                "* SSL Expiry Date exmp. 2022-04-13"
            ),
            "url": (
                "* URL"
            ),
            "function": (
                "* Function"
            ),
            "activity": (
                "* Activity"
            ),
            "ssl_cert_process": (
                "* SSL Cert Process"
            ),
            "cert_manager": (
                "* Cert-Manager"
            ),
            "common_name": (
                "* Common name examp. test.service.collections.ed.ac.uk"
            ),
            "server": (
                "lac-serv-live21.is.ed.ac.uk"
            ),
            "vm_ip_address": (
                "* VM IP Address"
            ),
            "vulnerability_checked": (
                "* Vulnerability checked"
            ),
            "personal_data_held": (
                "* Personal Data Held"
            ),
            "port": (
                "* Port"
            ),
            "load_balancer": (
                "* Load Balancer"
            ),
            "ours": (
                "* Ours"
            ),
            "environment": (
                ""
            ),
            "ssl_type": (
                ""
            ),
            "ease_expiry": (
                ""
            ),
            "application": (
                ""
            ),
            "user": (
                ""
            ),
            "major_user": (
                ""
            ),
            "restore_action": (
                "*Restore Action notes"
            ),
            "ssl_certificate_action": (
                "*SSL Certificate Action:"
            ),
            "external_support": (
                ""
            ),
            "expected_response": (
                ""
            ),
            "handle_prefix": (
                ""
            ),
            "accessibility_statement": (
                ""
            ),
            "notes": (
                ""
            ),
            "ga4_y_n": (
                "GA4 Active?"
            ),
            "ga4_required": (
                "GA4 Required?"
            ),
        }
        widgets = {
            "ssl_expiry_date": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": True,
                    "placeholder": "SSL Expiry Date",
                    "style": "text-align: center; color:black",
                },
            ),
            "url": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "URL",
                },
            ),
            "function": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Function",
                },
            ),
            "server": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Server",
                },
            ),
            "vm_ip_address": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "VM IP Address",
                },
            ),

            "vulnerability_checked": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Vulnerability Checked",
                },
            ),
            "personal_data_held": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Personal Data Held",
                },
            ),
            "port": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Port",
                },
            ),
            "load_balancer": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Load Balancer",
                },
            ),
            "ours": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Ours",
                },
            ),
            "environment": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Environment",
                },
            ),
            "ssl_type": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "SSL Type",
                },
            ),
            "ease_expiry": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Expiry Date",
                },
            ),
            "application": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Application",
                },
            ),
            "user": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "User",
                },
            ),
            "restore_action": forms.Textarea(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Restore Action",
                    "style": "width: 100%; height: 150px; padding: 12px 20px; box-sizing: border-box; border: 2px solid #ccc; border-radius: 4px; background-color: #f8f8f8; font-size: 13px; resize: none;"

                },
            ),
            "ssl_certificate_action": forms.Textarea(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "SSL Certificate Action",
                    "style": "width: 100%; height: 150px; padding: 12px 20px; box-sizing: border-box; border: 2px solid #ccc; border-radius: 4px; background-color: #f8f8f8; font-size: 13px; resize: none;"

                },
            ),
            "major_user": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Major User",
                },
            ),
            "external_support": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "External Support",
                },
            ),
            "expected_response": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Expected Response",
                },
            ),
            "handle_prefix": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Handle Prefix",
                },
            ),

            "accessibility_statement": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Accessibility Statement",
                },
            ),

            "notes": forms.Textarea(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Notes",
                    "style": "width: 100%; height: 150px; padding: 12px 20px; box-sizing: border-box; border: 2px solid #ccc; border-radius: 4px; background-color: #f8f8f8; font-size: 13px; resize: none;"
                },
            ),
            "ga4_notes": forms.Textarea(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "GA4 Notes",
                    "style": "width: 100%; height: 150px; padding: 12px 20px; box-sizing: border-box; border: 2px solid #ccc; border-radius: 4px; background-color: #f8f8f8; font-size: 13px; resize: none;"
                },
            ),
            "ga4_path": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "GA4 File Path",
                },
            ),

        }
    def __init__(self, *args, **kwargs):
        super(WebsiteForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False


class VmForm(forms.ModelForm):
    class Meta:
        model = Vm
        fields = [
            'hostname',
            'vm_type',
            'vm_status',
            'ip_address',
            'application',
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
        help_texts = {
            "hostname": (
                ""
            ),
            "ip_address": (
                ""
            ),
            "application": (
                ""
            ),
            "ssh_in_lp": (
                ""
            ),
            "puppet_controlled": (
                ""
            ),
            "data_centre": (
                ""
            ),
            "poodle_checked": (
                ""
            ),
            "log4shell_risk": (
                ""
            ),
            "trace_risk": (
                ""
            ),
            "httpd_last_patch": (
                ""
            ),
            "os_centos_assumed": (
                ""
            ),
            "httpd": (
                ""
            ),
            "tomcat": (
                ""
            ),
            "nginx": (
                ""
            ),
            "ram": (
                ""
            ),
            "cpu": (
                ""
            ),
            "db": (
                ""
            ),
            "php": (
                ""
            ),
            "java": (
                ""
            ),
            "vm_storage": (
                ""
            ),
            "special_mounts": (
                ""
            ),
            "python": (
                ""
            ),
            "npm": (
                ""
            ),
            "shibboleth": (
                ""
            ),
            "ssl": (
                ""
            ),
            "notes": (
                ""
            ),
        }
        widgets = {
            "hostname": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": True,
                },
            ),
            "ip_address": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "application": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "ssh_in_lp": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "puppet_controlled": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "data_centre": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "poodle_checked": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "log4shell_risk": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "trace_risk": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "httpd_last_patch": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "os_centos_assumed": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "httpd": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "tomcat": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "nginx": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "ram": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "cpu": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "db": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "php": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "java": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "vm_storage": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "special_mounts": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "python": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "npm": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "shibboleth": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "ssl": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                },
            ),
            "notes": forms.Textarea(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "style": "width: 100%"
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super(VmForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False


class AccessStatementForm(forms.ModelForm):
    class Meta:
        model = AccessStatement
        fields = [
            'url',
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
            'testing_status',
            'testing_status_r',
            'access_statement_status',
            'access_statement_status_r',
            'expiry_date',
            'statement_status_date',
            'issues_target_date',
            're_test_date',
            'testing_date',
            'notes',

        ]


        help_texts = {
            "url": (
                "* URL"
            ),
            "word21": (
                "* Word'21"
            ),
            "jira_nr": (
                "* Jira No"
            ),
            "wa_statement_tasked_to": (
                "* WA Statement tasked to"
            ),
            "site": (
                "* Site"
            ),
            "owning_team": (
                "* Owning Team"
            ),
            "content_service_manager": (
                "Content Service Manager"
            ),
            "tech_contact": (
                "* Tech Contact"
            ),
            "architecture": (
                "* Tech Contact"
            ),
            "physical_location_server": (
                "* Physical Location Server"
            ),
            "physical_location_directory_file": (
                "* Physical Location Directory-File"
            ),
            "how_deploy": (
                "* How to deploy"
            ),
            "testing_status": (
                "* Testing Status"
            ),
            "testing_status_r": (
                "* Testing Status R"
            ),
            "access_statement_status": (
                "* Accessibility Statement Status"
            ),
            "access_statement_status_r": (
                "* Accessibility Statement Status"
            ),
            "expiry_date": (
                "* Expiry date of Access.Statement"
            ),
            "testing_date": (
                "* Testing date of Access.Statement"
            ),
            "notes": (
                "* Notes"
            ),
        }
        widgets = {
            "url": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "",
                    "style": "width: 90%"
                },
            ),
            "word21": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "",
                    "style": "width: 15%"
                },
            ),
            "jira_nr": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "",
                },
            ),
            "wa_statement_tasked_to": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "WA Statement tasked to",
                },
            ),

            "site": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Site",
                },
            ),
            "owning_team": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Owning Team",
                },
            ),
            "content_service_manager": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Content Service Manager",
                },
            ),
            "tech_contact": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Tech Contact",
                },
            ),
            "architecture": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Tech Contact",
                },
            ),
            "physical_location_server": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Physical Location Server",
                },
            ),
            "physical_location_directory_file": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Physical Location Directory-File",
                },
            ),
            "how_deploy": forms.Textarea(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "How to deploy",
                    "style": "width: 100%; min-height: 25em; padding: 12px 20px; box-sizing: border-box; border: 2px solid #ccc; border-radius: 4px; background-color: #f8f8f8; font-size: 13px; resize: none",
                },
            ),
            "testing_status": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Testing Status",
                },
            ),
            "access_statement_status": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Accessibility Statement Status",
                },
            ),
            "testing_date": forms.DateInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Last testing date",

                },
            ),
            "statement_status_date": forms.DateInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Last testing date",

                },
            ),

            "expiry_date": forms.TextInput(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Expiry date",
                },
            ),
            "notes": forms.Textarea(
                attrs={
                    "id": "key_id",
                    "required": False,
                    "placeholder": "Notes",
                    "style": "width: 100%; min-height: 25em; height: 150px; padding: 12px 20px; box-sizing: border-box; border: 2px solid #ccc; border-radius: 4px; background-color: #f8f8f8; font-size: 13px; resize: none",
                },
            ),
        }
    def __init__(self, *args, **kwargs):
        super(AccessStatementForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False