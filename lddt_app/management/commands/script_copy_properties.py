from django.core.management.base import BaseCommand
from lddt_app.models import Vm
from django.utils import timezone

class Command(BaseCommand):
    help = 'Copies the value from the property field to the standard field'

    def handle(self, *args, **kwargs):
        total = Vm.objects.count()
        current = 0

        for obj in Vm.objects.all():
            current += 1

            print(
                f'Updating {obj.hostname} '
                f'({current} of {total})'
            )

            obj.db = obj.ssh_db
            obj.nginx = obj.ssh_nginx
            obj.puppet_controlled = obj.ssh_puppet_controlled
            obj.httpd = obj.ssh_httpd
            obj.vmfs_root_used = obj.ssh_vmfs_root_used
            obj.vmfs_apps_used = obj.ssh_vmfs_apps_used
            obj.vmfs_data_used = obj.ssh_vmfs_data_used
            obj.ip_address = obj.ssh_ip_address
            obj.processors = obj.ssh_processors
            obj.memory = obj.ssh_mem_total_gb
            obj.last_patch_days_ago = obj.ssh_last_patch_days_ago
            obj.system_check = obj.ssh_healthy_check
            obj.last_health_check = timezone.now()

            obj.save()

            print(f'Updated {obj.hostname}')
            print('***********************************\n')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {total} servers.'
            )
        )