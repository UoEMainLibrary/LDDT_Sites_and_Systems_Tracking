#!/bin/bash

# Send the email with the CSV attached
mail -s "Tracking Morning Report" -a "/apps/www/tracking/reports/tracking_morning_report.txt" patryk.smacki@ed.ac.uk <<EOF

Hello,

Attached is the folder size report generated today.

Regards,

Patryk Smacki

EOF
