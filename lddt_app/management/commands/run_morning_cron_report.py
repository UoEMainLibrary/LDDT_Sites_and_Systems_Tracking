from io import StringIO

from django.conf import settings
from django.core.mail import send_mail
from django.core.management import BaseCommand, call_command
from django.utils import timezone

from lddt_app.models import Vm


class Command(BaseCommand):
    help = "Run daily scripts and send email report"

    def handle(self, *args, **kwargs):
        self.stdout.write("COMMAND STARTED")

        started_at = timezone.now()
        output = StringIO()

        commands = [
            "sync_google_analytics",
            "update_ssl_dates",
            "script_copy_properties",
        ]

        success = []
        failed = []

        for command_name in commands:
            self.stdout.write(f"Running: {command_name}")

            output.write("\n" + "=" * 70 + "\n")
            output.write(f"Running: {command_name}\n")
            output.write("=" * 70 + "\n")

            try:
                call_command(command_name, stdout=output, stderr=output)
                success.append(command_name)
                output.write(f"\nSUCCESS: {command_name}\n")
                self.stdout.write(self.style.SUCCESS(f"SUCCESS: {command_name}"))
            except Exception as e:
                failed.append((command_name, str(e)))
                output.write(f"\nFAILED: {command_name}\n")
                output.write(f"ERROR: {e}\n")
                self.stdout.write(self.style.ERROR(f"FAILED: {command_name} -> {e}"))

        finished_at = timezone.now()
        duration = finished_at - started_at
        report = output.getvalue()

        success_text = "\n".join(success) if success else "None"
        failed_text = "\n".join([f"{name}: {err}" for name, err in failed]) if failed else "None"

        subject = "Daily Django Job Report - SUCCESS"
        if failed:
            subject = f"Daily Django Job Report - FAILED ({len(failed)})"

        message = f"""
Daily automation report

Started:
{started_at.strftime("%Y-%m-%d %H:%M:%S")}

Finished:
{finished_at.strftime("%Y-%m-%d %H:%M:%S")}

Duration:
{duration}

Successful commands:
{success_text}

Failed commands:
{failed_text}

----------------------------------------------------------------------
FULL OUTPUT
----------------------------------------------------------------------

{report}
"""

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["your@email.com"],
            fail_silently=False,
        )

        Vm.objects.update(last_cron_run=finished_at)

        self.stdout.write(self.style.SUCCESS("Daily tasks completed and email sent."))
        self.stdout.write(self.style.SUCCESS(f"Last cron run saved: {finished_at}"))