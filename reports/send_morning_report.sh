#!/bin/bash

REPORT="/apps/www/tracking/reports/tracking_morning_report.txt"

mail -s "Tracking Morning Report" \
-a "$REPORT" \
patryk.smacki@ed.ac.uk \
lac-servers@mlist.is.ed.ac.uk <<EOF

Good morning,

Tracking report from this morning :)

$(cat "$REPORT")

Regards,

Pat

EOF
