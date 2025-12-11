from django.core.management.base import BaseCommand
from lddt_app.models import Vm

class Command(BaseCommand):
    help = 'Copies the value from the property field to the standard field'
    def handle(self, *args, **kwargs):
        # Fetch all objects of MyModel
        for obj in Vm.objects.all():
            # Copy the value from the property field to the standard field
            print('Updating ' + str(obj.hostname) + ' id number=' + str(obj.id) + ' ..... of 1055')
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
            obj.save()
            name = obj.ssh_db
            print( 'Updated ' + str(obj.hostname))
            print ('***********************************')
            print ('                                    ')

        self.stdout.write(self.style.SUCCESS('Successfully copied property values to standard fields.'))
