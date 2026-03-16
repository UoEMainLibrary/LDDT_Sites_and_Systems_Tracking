from io import StringIO
import traceback

from django.conf import settings
from django.core.mail import send_mail
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "Run morning report commands and email the result"

    def handle(self, *args, **options):
        commands = [
            # "sync_google_analytics",
            "update_ssl_dates",
            # "script_copy_properties",
        ]

        output = []
        success = True

        for command_name in commands:
            buffer = StringIO()
            output.append(f"=== Running: {command_name} ===")

            try:
                call_command(command_name, stdout=buffer, stderr=buffer)
                command_output = buffer.getvalue().strip() or "Completed successfully."
                output.append(command_output)
            except Exception as e:
                success = False
                output.append(f"FAILED: {e}")
                output.append(traceback.format_exc())

            output.append("")

        message = "\n".join(output)

        subject = (
            "Morning cron report: SUCCESS"
            if success
            else "Morning cron report: FAILED"
        )

        # Always print report to terminal/logs too
        self.stdout.write(message)

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["patryk.samacki@ed.ac.uk"],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS("Morning cron report sent."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Email sending failed: {e}"))