from django.db import models
from datetime import *
from django.utils.dateparse import parse_date
import os
import paramiko
import subprocess
from django.conf import settings
from django.http import JsonResponse



# Create your models here.
class Group(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Type(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name

class Tech_Status(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name

class SSL_Cert_Process(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name

class Cert_Manager(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name

class Activity(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name

class access_statement_y_n(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name

class ga4_y_n(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name

class ga4_required(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name

class Website(models.Model):
    ssl_expiry_date = models.DateField(blank=True, default=None, null=True)
    ssl_expiry_date_new = models.DateField(blank=True, default=None, null=True)
    url = models.CharField('URL', blank=True, null=True, max_length=100)
    function = models.CharField('Function', blank=True, null=True, max_length=150)
    common_name = models.CharField('Common Name', blank=True, null=True, max_length=150)
    server = models.CharField('Server', blank=True, null=True, max_length=150)
    vm_ip_address = models.CharField('VM IP Address', blank=True, null=True, max_length=150)
    type = models.ForeignKey(Type, on_delete=models.CASCADE, blank=True, null=True, max_length=150)
    tech_status = models.ForeignKey(Tech_Status, on_delete=models.CASCADE, blank=True, null=True, max_length=150)
    ssl_cert_process = models.ForeignKey(SSL_Cert_Process, on_delete=models.CASCADE, blank=True, null=True, max_length=150)
    cert_manager = models.ForeignKey(Cert_Manager, on_delete=models.CASCADE, blank=True, null=True, max_length=150)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, blank=True, null=True, max_length=150)
    vulnerability_checked = models.CharField('Vulnerability', blank=True, null=True, max_length=150)
    personal_data_held = models.CharField('Personal Data', blank=True, null=True, max_length=150)
    port = models.CharField('Port', blank=True, null=True, max_length=150)
    load_balancer = models.CharField('Load Balancer', blank=True, null=True, max_length=150)
    ours = models.CharField('Ours', blank=True, null=True, max_length=150)
    environment = models.CharField('Environment', blank=True, null=True, max_length=150)
    ssl_type = models.CharField('SSL Type', blank=True, null=True, max_length=150)
    ease_expiry = models.DateField('EASE Expiry', blank=True, null=True, max_length=150)
    application = models.CharField('Application', blank=True, null=True, max_length=150)
    restore_action = models.TextField('Restore Action', blank=True, null=True)
    ssl_certificate_action = models.TextField('SSL Certificate Action', blank=True, null=True)
    user = models.CharField('User', blank=True, null=True, max_length=50)
    major_user = models.CharField('Major User', blank=True, null=True, max_length=150)
    external_support = models.CharField('External Support', blank=True, null=True, max_length=150)
    expected_response = models.CharField('Expected Response', blank=True, null=True, max_length=150)
    handle_prefix = models.CharField('Handle Prefix', blank=True, null=True, max_length=150)
    access_statement_y_n = models.ForeignKey(access_statement_y_n, on_delete=models.CASCADE, null=True, blank=True)
    accessibility_statement = models.CharField('Accessibility Statement', blank=True, null=True, max_length=150)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    notes = models.TextField('Notes', blank=True, null=True)
    calc_ping_field = models.CharField('Field for ping', blank=True, null=True, max_length=50)
    ga4_required = models.ForeignKey(ga4_required, on_delete=models.CASCADE, null=True, blank=True)
    ga4_y_n = models.ForeignKey(ga4_y_n, on_delete=models.CASCADE, null=True, blank=True)
    ga4_notes = models.TextField('GA4 Notes', blank=True, null=True)
    ga4_path = models.TextField('GA4 path', blank=True, null=True)

    def __str__(self):
        return self.url

    @property
    def ssl_expiration(self):
        type_str = getattr(self.type, 'name', None)  # adjust 'name' as needed
        if not type_str or type_str.strip().upper() != "SITE":
            return None

        cmd = (
            f'echo | openssl s_client -connect {self.common_name}:443 '
            f'-servername {self.common_name} 2>/dev/null | '
            'openssl x509 -noout -enddate'
        )

        try:
            result = subprocess.check_output(cmd, shell=True).decode().strip()
            # result = "notAfter=Jan 20 12:00:00 2026 GMT"

            if result.startswith("notAfter="):
                result = result.replace("notAfter=", "")

            # Convert to Python date
            dt = datetime.strptime(result, "%b %d %H:%M:%S %Y %Z").date()
            return dt
        except Exception:
            return None

    def get_calc_ping_field(self):
        hostname = self.url
        response = os.system('ping -c 1 ' + hostname)
        return response

    def save_calc_ping_field(self, *args, **kwargs):
        self.calc_ping_field = self.get_calc_ping_field()
        super(Website, self).save(*args, **kwargs)


    def ssl_exp_date_year_month(self):
        date_ssl= self.ssl_expiry_date.strftime("%Y/%B")
        current_datetime_now = datetime.now()
        current_datetime_now_tostring = current_datetime_now.strftime("%Y/%B")
        if date_ssl == current_datetime_now_tostring:
            return "Yes"
        else:
            return "No"

    @property
    def tech_status_light(self):
        return str(self.tech_status)

    @property
    def ga4_y_n_light(self):
        return str(self.ga4_y_n)

    @property
    def ga4_required_light(self):
        return str(self.ga4_required)

    @property
    def cert_manager_light(self):
        return str(self.cert_manager)

    @property
    def dns_ip_address(self):
        resoult = ""
        if self.load_balancer == "No":
            resoult = self.vm_ip_address
        else:
            return resoult
        return resoult

    @property
    def vm_network_status(self):
        resoult = ""
        vm_ip_address_str = str(self.vm_ip_address)
        if "129." in vm_ip_address_str:
            resoult = "PUBLIC"
        elif "192." in vm_ip_address_str:
            resoult = "PRIVATE"
        else:
            pass
        return resoult


    @property
    def dns_network_status(self):
        resoult = ""
        vm_ip_address_str = str(self.vm_ip_address)
        if "129." in vm_ip_address_str:
            resoult = "PUBLIC"
        elif "192." in vm_ip_address_str:
            resoult = "PRIVATE"
        else:
            pass
        return resoult



class vm_type(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name

class vm_status(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name

class Vm(models.Model):
    hostname = models.CharField('Hostname', blank=True, null=True, max_length=150)
    ip_address = models.CharField('IP Address', blank=True, null=True, max_length=150)
    application = models.CharField('Application', blank=True, null=True, max_length=150)
    vm_type = models.ForeignKey(vm_type, on_delete=models.CASCADE, blank=True, null=True, max_length=150)
    vm_status = models.ForeignKey(vm_status, on_delete=models.CASCADE, blank=True, null=True, max_length=150)
    ssh_in_lp = models.CharField('SSH in LP', blank=True, null=True, max_length=150)
    puppet_controlled = models.CharField('Puppet Controlled', blank=True, null=True, max_length=150)
    data_centre = models.CharField('Data Centre', blank=True, null=True, max_length=150)
    poodle_checked = models.CharField('Poodle Checked', blank=True, null=True, max_length=150)
    log4shell_risk = models.CharField('Log for shell risk', blank=True, null=True, max_length=150)
    trace_risk = models.CharField('Trace Risk', blank=True, null=True, max_length=150)
    httpd_last_patch = models.DateField('HTTPD Last patch', blank=True, null=True, max_length=150)
    os_centos_assumed = models.CharField('OS (CENTOS assumed)', blank=True, null=True, max_length=150)
    httpd = models.CharField('HTTPD', blank=True, null=True, max_length=150)
    tomcat = models.CharField('Tomcat', blank=True, null=True, max_length=150)
    nginx = models.CharField('NGINX', blank=True, null=True, max_length=150)
    ram = models.CharField('RAM', blank=True, null=True, max_length=150)
    cpu = models.CharField('CPU', blank=True, null=True, max_length=150)
    db = models.CharField('DB', blank=True, null=True, max_length=150)
    php = models.CharField('PHP', blank=True, null=True, max_length=150)
    java = models.CharField('Java', blank=True, null=True, max_length=150)
    vm_storage = models.CharField('VM Storage', blank=True, null=True, max_length=150)
    special_mounts = models.CharField('Special Mounts', blank=True, null=True, max_length=150)
    python = models.CharField('Python', blank=True, null=True, max_length=150)
    npm = models.CharField('NPM', blank=True, null=True, max_length=150)
    shibboleth = models.CharField('NPM', blank=True, null=True, max_length=150)
    ssl = models.CharField('SSL', blank=True, null=True, max_length=150)
    notes = models.TextField('Notes', blank=True, null=True)
    vmfs_root_used = models.CharField('VMFS-root used', blank=True, null=True, max_length=150)
    vmfs_apps_used = models.CharField('VMFS-apps used', blank=True, null=True, max_length=150)
    vmfs_data_used = models.CharField('VMFS-data used', blank=True, null=True, max_length=150)
    processors = models.CharField('Processors', blank=True, null=True, max_length=150)
    memory = models.CharField('Memory', blank=True, null=True, max_length=150)
    last_patch_days_ago = models.CharField('Last Patch in days ago', blank=True, null=True, max_length=150)
    @property
    def print_hostname(self):
        return self.hostname

    @property
    def ssh_db(self):
        ssh_user_name = settings.SSH_USER_NAME
        ssh_passphrase = settings.SSH_PASSPHRASE

        hostname = self.hostname
        port = 22
        username = ssh_user_name
        private_key_path = "/home/lib/lacddt/.ssh/id_rsa"
        passphrase = ssh_passphrase

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        private_key = paramiko.RSAKey.from_private_key_file(
            private_key_path,
            password=passphrase
        )

        try:
            ssh.connect(hostname, port=port, username=username, pkey=private_key)

            # Query MySQL version
            stdin, stdout, stderr = ssh.exec_command("mysql -V")
            output = stdout.read().decode().strip()

            if not output:
                return ''

            # Example output:
            # mysql  Ver 14.14 Distrib 10.6.24-MariaDB, for Linux (x86_64) using EditLine wrapper

            version = None

            # Extract version after "Distrib "
            if "Distrib" in output:
                version_part = output.split("Distrib")[1].split(",")[0].strip()
                # Remove any suffix like -MariaDB etc.
                version = version_part.split('-')[0]

            if not version:
                # fallback: try numeric extraction
                import re
                match = re.search(r"(\d+\.\d+\.\d+)", output)
                if match:
                    version = match.group(1)

            if not version:
                return 'MySQL "unknown version"'

            return f'MySQL {version}'

        except paramiko.AuthenticationException:
            return ''

        except paramiko.SSHException as sshException:
            return f''

        except Exception as e:
            return f''

        finally:
            ssh.close()

    @property
    def ssh_nginx(self):
        ssh_user_name = settings.SSH_USER_NAME
        ssh_passphrase = settings.SSH_PASSPHRASE

        hostname = self.hostname
        port = 22
        username = ssh_user_name
        private_key_path = "/home/lib/lacddt/.ssh/id_rsa"
        passphrase = ssh_passphrase

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        private_key = paramiko.RSAKey.from_private_key_file(
            private_key_path,
            password=passphrase
        )

        try:
            ssh.connect(hostname, port=port, username=username, pkey=private_key)

            # Get OS and nginx info
            # cat -t is unnecessary here; removed for clean output
            stdin, stdout, stderr = ssh.exec_command("cat /etc/centos-release; nginx -v")

            output = stdout.read().decode().strip()

            if not output:
                return 'OS "unknown"'

            # First line should contain the OS release text
            lines = output.splitlines()
            os_release = lines[0]

            # Remove parentheses content, e.g. (Green Obsidian)
            if "(" in os_release:
                os_release = os_release.split("(")[0].strip()

            return os_release

        except paramiko.AuthenticationException:
            return 'OS "authentication failed"'

        except paramiko.SSHException as sshException:
            return f'OS "SSH error: {sshException}"'

        except Exception as e:
            return f'OS "error: {e}"'

        finally:
            ssh.close()

    @property
    def ssh_puppet_controlled(self):
        ssh_user_name = settings.SSH_USER_NAME
        ssh_passphrase = settings.SSH_PASSPHRASE

        hostname = self.hostname
        port = 22  # Default SSH port
        username = ssh_user_name
        private_key_path = "/home/lib/lacddt/.ssh/id_rsa"
        passphrase = ssh_passphrase

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Load private key with passphrase
        private_key = paramiko.RSAKey.from_private_key_file(
            private_key_path,
            password=passphrase
        )

        try:
            # Connect
            ssh.connect(hostname, port=port, username=username, pkey=private_key)

            # Query only puppet-agent version
            command = "rpm -q --qf '%{VERSION}-%{RELEASE}\n' puppet-agent"
            stdin, stdout, stderr = ssh.exec_command(command)

            version = stdout.read().decode().strip()

            if not version:
                return 'Puppet "not installed"'

            return f'Puppet - {version} '

        except paramiko.AuthenticationException:
            return 'Puppet "authentication failed"'

        except paramiko.SSHException as sshException:
            return f'Puppet "SSH error: {sshException}"'

        except Exception as e:
            return f'Puppet "error: {e}"'

        finally:
            ssh.close()

    @property
    def ssh_httpd(self):
        ssh_user_name = settings.SSH_USER_NAME
        ssh_passphrase = settings.SSH_PASSPHRASE

        hostname = self.hostname
        port = 22  # Default SSH port
        username = ssh_user_name
        private_key_path = "/home/lib/lacddt/.ssh/id_rsa"  # e.g., "/home/user/.ssh/id_rsa"
        passphrase = ssh_passphrase

        # Initialize the SSH client
        ssh = paramiko.SSHClient()

        # Add the remote server's SSH key automatically to known hosts
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Load the private key
        # private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path, password=passphrase)

        try:
            # Connect to the remote server using the private key
            ssh.connect(hostname, port=port, username=username, pkey=private_key)

            # Execute a command (example: list files in home directory)
            stdin, stdout, stderr = ssh.exec_command("httpd -v;")
            # stdin, stdout, stderr = ssh.exec_command("hostname;")

            # Print the output
            output = stdout.read().decode()

            return output

        except paramiko.AuthenticationException:
            print("Authentication failed, please verify your credentials or key.")

        except paramiko.SSHException as sshException:
            print(f"Unable to establish SSH connection: {sshException}")

        except Exception as e:
            print(f"An error occurred: {e}")


        finally:
            # Close the SSH connection
            ssh.close()

    @property
    def ssh_vmfs_root_used(self):
        ssh_user_name = settings.SSH_USER_NAME
        ssh_passphrase = settings.SSH_PASSPHRASE

        hostname = self.hostname
        port = 22
        username = ssh_user_name
        private_key_path = "/home/lib/lacddt/.ssh/id_rsa"
        passphrase = ssh_passphrase

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        private_key = paramiko.RSAKey.from_private_key_file(
            private_key_path,
            password=passphrase
        )

        try:
            ssh.connect(hostname, port=port, username=username, pkey=private_key)

            stdin, stdout, stderr = ssh.exec_command('df -h /dev/mapper/VMFS-root')
            output = stdout.read().decode()

            if output:
                for line in output.splitlines():
                    if line.startswith("Filesystem"):
                        continue

                    if "/dev/mapper/VMFS-root" in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            used_str = parts[4]  # example "73%"
                            # remove "%" and convert
                            used = int(used_str.replace("%", ""))
                            free = 100 - used
                            return f"{free}%"

            return ""

        except paramiko.AuthenticationException:
            return 'VMFS "authentication failed"'

        except paramiko.SSHException as sshException:
            return f'VMFS "SSH error: {sshException}"'

        except Exception as e:
            return f'VMFS "error: {e}"'

        finally:
            ssh.close()

    @property
    def ssh_vmfs_apps_used(self):
        ssh_user_name = settings.SSH_USER_NAME
        ssh_passphrase = settings.SSH_PASSPHRASE

        hostname = self.hostname
        port = 22
        username = ssh_user_name
        private_key_path = "/home/lib/lacddt/.ssh/id_rsa"
        passphrase = ssh_passphrase

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        private_key = paramiko.RSAKey.from_private_key_file(
            private_key_path,
            password=passphrase
        )

        try:
            ssh.connect(hostname, port=port, username=username, pkey=private_key)

            stdin, stdout, stderr = ssh.exec_command('df -h /dev/mapper/VMFS-apps')
            output = stdout.read().decode()

            if output:
                for line in output.splitlines():
                    if line.startswith("Filesystem"):
                        continue

                    if "/dev/mapper/VMFS-apps" in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            used_str = parts[4]  # e.g. "67%"
                            used = int(used_str.replace("%", ""))
                            free = 100 - used
                            return f"{free}%"

            return ""

        except paramiko.AuthenticationException:
            return 'VMFS "authentication failed"'

        except paramiko.SSHException as sshException:
            return f'VMFS "SSH error: {sshException}"'

        except Exception as e:
            return f'VMFS "error: {e}"'

        finally:
            ssh.close()

    @property
    def ssh_vmfs_data_used(self):
        ssh_user_name = settings.SSH_USER_NAME
        ssh_passphrase = settings.SSH_PASSPHRASE

        hostname = self.hostname
        port = 22
        username = ssh_user_name
        private_key_path = "/home/lib/lacddt/.ssh/id_rsa"
        passphrase = ssh_passphrase

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        private_key = paramiko.RSAKey.from_private_key_file(
            private_key_path,
            password=passphrase
        )

        try:
            ssh.connect(hostname, port=port, username=username, pkey=private_key)

            stdin, stdout, stderr = ssh.exec_command('df -h /dev/mapper/VMFS-data')
            output = stdout.read().decode()

            if output:
                for line in output.splitlines():
                    if line.startswith("Filesystem"):
                        continue

                    if "/dev/mapper/VMFS-data" in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            used_str = parts[4]  # e.g. "79%"
                            used = int(used_str.replace("%", ""))
                            free = 100 - used
                            return f"{free}%"

            return ""

        except paramiko.AuthenticationException:
            return 'VMFS "authentication failed"'

        except paramiko.SSHException as sshException:
            return f'VMFS "SSH error: {sshException}"'

        except Exception as e:
            return f'VMFS "error: {e}"'

        finally:
            ssh.close()

    @property
    def ssh_ip_address(self):
        ssh_user_name = settings.SSH_USER_NAME
        ssh_passphrase = settings.SSH_PASSPHRASE

        hostname = self.hostname
        port = 22  # Default SSH port
        username = ssh_user_name
        private_key_path = "/home/lib/lacddt/.ssh/id_rsa"  # e.g., "/home/user/.ssh/id_rsa"
        passphrase = ssh_passphrase

        # Initialize the SSH client
        ssh = paramiko.SSHClient()

        # Add the remote server's SSH key automatically to known hosts
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Load the private key
        # private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path, password=passphrase)

        try:
            # Connect to the remote server using the private key
            ssh.connect(hostname, port=port, username=username, pkey=private_key)

            # Run the nslookup command
            result = subprocess.run(['nslookup', hostname], capture_output=True, text=True, check=True)

            # Print the output
            output = result.stdout

            # Extract the relevant lines
            lines = output.splitlines()
            address_count = 0  # Initialize counter for addresses
            second_address = None  # Variable to store the second address

            for line in lines:
                # Look for lines containing 'Address'
                if 'Address' in line:
                    address_count += 1
                    if address_count == 2:  # Check if it's the second address
                        second_address = line.split()[-1]
                        print(second_address)
                        break  # Exit loop after finding the second address

            if second_address:
                return (f"{second_address}")
            else:
                return ("Second address not found.")

        except paramiko.AuthenticationException:
            print("Authentication failed, please verify your credentials or key.")

        except paramiko.SSHException as sshException:
            print(f"Unable to establish SSH connection: {sshException}")

        except Exception as e:
            print(f"An error occurred: {e}")

    @property
    def ssh_processors(self):
        ssh_user_name = settings.SSH_USER_NAME
        ssh_passphrase = settings.SSH_PASSPHRASE

        hostname = self.hostname
        port = 22
        username = ssh_user_name
        private_key_path = "/home/lib/lacddt/.ssh/id_rsa"
        passphrase = ssh_passphrase

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        private_key = paramiko.RSAKey.from_private_key_file(
            private_key_path,
            password=passphrase
        )

        try:
            ssh.connect(hostname, port=port, username=username, pkey=private_key)

            # Command to count processors (CPU cores / threads)
            stdin, stdout, stderr = ssh.exec_command('grep -c ^processor /proc/cpuinfo')
            output = stdout.read().decode().strip()

            if output.isdigit():
                return int(output)

            return "Unknown"

        except paramiko.AuthenticationException:
            return 'Processors "authentication failed"'

        except paramiko.SSHException as sshException:
            return f'Processors "SSH error: {sshException}"'

        except Exception as e:
            return f'Processors "error: {e}"'

        finally:
            ssh.close()

    @property
    def ssh_mem_total_gb(self):
        ssh_user_name = settings.SSH_USER_NAME
        ssh_passphrase = settings.SSH_PASSPHRASE

        hostname = self.hostname
        port = 22
        username = ssh_user_name
        private_key_path = "/home/lib/lacddt/.ssh/id_rsa"
        passphrase = ssh_passphrase

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        private_key = paramiko.RSAKey.from_private_key_file(
            private_key_path,
            password=passphrase
        )

        try:
            ssh.connect(hostname, port=port, username=username, pkey=private_key)

            stdin, stdout, stderr = ssh.exec_command('cat /proc/meminfo | grep MemTotal')
            output = stdout.read().decode().strip()

            if output:
                parts = output.split()
                if len(parts) >= 2:
                    try:
                        mem_kb = int(parts[1])
                        mem_gb = mem_kb / (1024 ** 2)  # convert kB to GB
                        return round(mem_gb, 2)
                    except ValueError:
                        return "Unknown"

            return "Unknown"

        except paramiko.AuthenticationException:
            return 'MemTotal "authentication failed"'

        except paramiko.SSHException as sshException:
            return f'MemTotal "SSH error: {sshException}"'

        except Exception as e:
            return f'MemTotal "error: {e}"'

        finally:
            ssh.close()

    @property
    def ssh_last_patch_days_ago(self):
        ssh_user_name = settings.SSH_USER_NAME
        ssh_passphrase = settings.SSH_PASSPHRASE

        hostname = self.hostname
        port = 22
        username = ssh_user_name
        private_key_path = "/home/lib/lacddt/.ssh/id_rsa"
        passphrase = ssh_passphrase

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        private_key = paramiko.RSAKey.from_private_key_file(
            private_key_path,
            password=passphrase
        )

        try:
            ssh.connect(hostname, port=port, username=username, pkey=private_key)

            cmd = 'boot=$(uptime -s); echo $(( ( $(date +%s) - $(date -d "$boot" +%s) ) / 86400 ))'
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output = stdout.read().decode().strip()

            if output.isdigit():
                return int(output)
            else:
                return "Unknown"

        except paramiko.AuthenticationException:
            return 'Days since boot "authentication failed"'

        except paramiko.SSHException as sshException:
            return f'Days since boot "SSH error: {sshException}"'

        except Exception as e:
            return f'Days since boot "error: {e}"'

        finally:
            ssh.close()

class Testing_Status_r(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name

class Statement_Status_r(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name


class Tasked_to(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name




class AccessStatement(models.Model):
    url = models.CharField('URL', blank=True, null=True, max_length=150)
    word21 = models.CharField('WORD21', blank=True, null=True, max_length=150)
    jira_nr = models.CharField('Jira No', blank=True, null=True, max_length=100)
    wa_statement_tasked_to = models.CharField('WA Statement tasked to', blank=True, null=True, max_length=100)
    wa_statement_tasked_to_last = models.ForeignKey(Tasked_to, on_delete=models.CASCADE, blank=True, null=True, max_length=100)
    site = models.CharField('Site', blank=True, null=True, max_length=150)
    owning_team = models.CharField('Owning Team', blank=True, null=True, max_length=150)
    content_service_manager = models.CharField('Content Service Manager', blank=True, null=True, max_length=150)
    tech_contact = models.CharField('Tech Contact', blank=True, null=True, max_length=150)
    architecture = models.CharField('Tech Contact', blank=True, null=True, max_length=150)
    physical_location_server = models.CharField('Physical Location Server', blank=True, null=True, max_length=200)
    physical_location_directory_file = models.CharField('Physical Location Directory-File', blank=True, null=True, max_length=200)
    how_deploy = models.TextField('How to deploy', blank=True, null=True)
    testing_status = models.CharField('Testing Status', blank=True, null=True, max_length=100)
    testing_status_r = models.ForeignKey(Testing_Status_r, on_delete=models.CASCADE, blank=True, null=True, max_length=30)
    access_statement_status = models.CharField('Accessibility Statement Status', blank=True, null=True, max_length=100)
    access_statement_status_r = models.ForeignKey(Statement_Status_r, on_delete=models.CASCADE, blank=True, null=True, max_length=30)
    testing_date = models.DateField(blank=True, default=None, null=True)
    expiry_date = models.DateField(blank=True, default=None, null=True)
    statement_status_date = models.DateField(blank=True, default=None, null=True)
    issues_target_date = models.DateField(blank=True, default=None, null=True)
    re_test_date = models.DateField(blank=True, default=None, null=True)
    notes = models.TextField('Notes', blank=True, null=True)
    def __str__(self):
        return self.url
