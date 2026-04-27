#!/bin/bash

# Send the email with the CSV attached
mail -s "Tracking Morning Report" -a "/apps/www/tracking/reports/tracking_morning_report.txt" patryk.smacki@ed.ac.uk lac-servers@mlist.is.ed.ac.uk<<EOF

Hello,

Tracking report from this morning :)

Regards,

Patryk Smacki

EOF
