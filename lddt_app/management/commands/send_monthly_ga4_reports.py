import os
import re
import tempfile
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from lddt_app.models import GoogleAnalyticsStats


REPORT_DIR = os.path.join(settings.BASE_DIR, "reports")

REPORT_FILENAME = "TrackingGA4_MONTHLY_SUMMARY.pdf"

EMAIL_TO = [
    "patryk.smacki@ed.ac.uk",
]

EMAIL_FROM = getattr(settings, "DEFAULT_FROM_EMAIL", "lacddt@ed.ac.uk")

CORPORATE = "#690051"
DARK = "#323c4e"


class Command(BaseCommand):
    help = "Send monthly GA4 summary report"

    # ------------------------------------------------------------
    # Data analysis
    # ------------------------------------------------------------

    def get_months(self):
        month_keys = set()

        for stat in GoogleAnalyticsStats.objects.all():
            month_keys.update((stat.monthly_views_data or {}).keys())
            month_keys.update((stat.monthly_sessions_data or {}).keys())
            month_keys.update((stat.monthly_users_data or {}).keys())

        return sorted(month_keys)

    def month_is_after_tracking_started(self, stat, month):
        if not stat.earliest_data_date:
            return False

        month_start = datetime.strptime(month + "-01", "%Y-%m-%d").date()
        tracking_month = stat.earliest_data_date.replace(day=1)

        return month_start >= tracking_month

    def analyse_service(self, stat, months):
        if not stat.earliest_data_date:
            return None

        monthly_rows = []

        total_views = 0
        total_sessions = 0
        total_users = 0
        tracked_months = 0

        for month in months:
            if not self.month_is_after_tracking_started(stat, month):
                continue

            views = int((stat.monthly_views_data or {}).get(month, 0) or 0)
            sessions = int((stat.monthly_sessions_data or {}).get(month, 0) or 0)
            users = int((stat.monthly_users_data or {}).get(month, 0) or 0)

            activity = views + sessions + users

            monthly_rows.append({
                "month": month,
                "views": views,
                "sessions": sessions,
                "users": users,
                "activity": activity,
            })

            total_views += views
            total_sessions += sessions
            total_users += users
            tracked_months += 1

        if tracked_months == 0:
            return None

        total_activity = total_views + total_sessions + total_users
        avg_activity = total_activity / tracked_months

        first_activity = monthly_rows[0]["activity"] if monthly_rows else 0
        last_activity = monthly_rows[-1]["activity"] if monthly_rows else 0

        if first_activity > 0:
            growth_percent = ((last_activity - first_activity) / first_activity) * 100
        else:
            growth_percent = 0

        highest_month = max(monthly_rows, key=lambda row: row["activity"])
        lowest_month = min(monthly_rows, key=lambda row: row["activity"])

        return {
            "stat": stat,
            "property_name": stat.property_name,
            "since": stat.earliest_data_date,
            "months_tracked": tracked_months,
            "monthly_rows": monthly_rows,
            "total_views": total_views,
            "total_sessions": total_sessions,
            "total_users": total_users,
            "total_activity": total_activity,
            "avg_activity": avg_activity,
            "growth_percent": growth_percent,
            "highest_month": highest_month,
            "lowest_month": lowest_month,
        }

    def build_analysis(self):
        months = self.get_months()

        stats = GoogleAnalyticsStats.objects.all().order_by("property_name")

        analysed = []
        excluded = []

        for stat in stats:
            result = self.analyse_service(stat, months)

            if result:
                analysed.append(result)
            else:
                excluded.append(stat)

        busiest = sorted(
            analysed,
            key=lambda item: item["avg_activity"],
            reverse=True,
        )[:5]

        least_busy = sorted(
            analysed,
            key=lambda item: item["avg_activity"],
        )[:5]

        biggest_growth = sorted(
            analysed,
            key=lambda item: item["growth_percent"],
            reverse=True,
        )[:5]

        biggest_decline = sorted(
            analysed,
            key=lambda item: item["growth_percent"],
        )[:5]

        return {
            "months": months,
            "analysed": analysed,
            "excluded": excluded,
            "busiest": busiest,
            "least_busy": least_busy,
            "biggest_growth": biggest_growth,
            "biggest_decline": biggest_decline,
        }

    # ------------------------------------------------------------
    # Chart helpers
    # ------------------------------------------------------------

    def safe_filename(self, value):
        value = value.strip().replace(" ", "_")
        value = re.sub(r"[^A-Za-z0-9_\-]", "", value)
        return value[:40] or "service"

    def make_bar_chart(self, title, rows, value_key, filename, xlabel="Activity"):
        labels = [row["property_name"][:36] for row in rows]
        values = [row[value_key] for row in rows]

        path = os.path.join(tempfile.gettempdir(), filename)

        plt.figure(figsize=(9, 4))
        plt.barh(labels, values)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(path, dpi=160)
        plt.close()

        return path

    def make_service_trend_chart(self, service, filename):
        path = os.path.join(tempfile.gettempdir(), filename)

        months = [row["month"] for row in service["monthly_rows"]]
        views = [row["views"] for row in service["monthly_rows"]]
        sessions = [row["sessions"] for row in service["monthly_rows"]]
        users = [row["users"] for row in service["monthly_rows"]]

        plt.figure(figsize=(9, 3.5))
        plt.plot(months, views, marker="o", label="Views")
        plt.plot(months, sessions, marker="o", label="Sessions")
        plt.plot(months, users, marker="o", label="Active users")
        plt.title(service["property_name"][:80])
        plt.xticks(rotation=45, ha="right")
        plt.legend()
        plt.tight_layout()
        plt.savefig(path, dpi=160)
        plt.close()

        return path

    # ------------------------------------------------------------
    # PDF helpers
    # ------------------------------------------------------------

    def table_style(self):
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),

            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                colors.HexColor("#f8f8f8"),
            ]),

            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#323c4e")),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ])

    def ranking_table(self, title, rows, styles):
        story = [
            Paragraph(title, styles["Heading2"]),
            Spacer(1, 8),
        ]

        data = [[
            "Rank",
            "Service",
            "Since",
            "Months",
            "Avg Activity",
            "Views",
            "Sessions",
            "Users",
            "Growth",
        ]]

        for index, row in enumerate(rows, start=1):
            data.append([
                index,
                Paragraph(row["property_name"], styles["Normal"]),
                row["since"].strftime("%Y-%m-%d"),
                row["months_tracked"],
                f"{row['avg_activity']:,.0f}",
                f"{row['total_views']:,}",
                f"{row['total_sessions']:,}",
                f"{row['total_users']:,}",
                f"{row['growth_percent']:.1f}%",
            ])

        table = Table(
            data,
            colWidths=[35, 230, 75, 50, 75, 75, 75, 75, 60],
            repeatRows=1,
        )

        table.setStyle(self.table_style())

        story.append(table)
        story.append(Spacer(1, 16))

        return story

    def monthly_detail_table(self, service, styles):
        story = [
            Paragraph(service["property_name"], styles["Heading2"]),
            Paragraph(f"Since: {service['since'].strftime('%Y-%m-%d')}", styles["Normal"]),
            Paragraph(f"Months tracked: {service['months_tracked']}", styles["Normal"]),
            Paragraph(f"Average monthly activity: {service['avg_activity']:,.0f}", styles["Normal"]),
            Paragraph(f"Total views: {service['total_views']:,}", styles["Normal"]),
            Paragraph(f"Total sessions: {service['total_sessions']:,}", styles["Normal"]),
            Paragraph(f"Total active users: {service['total_users']:,}", styles["Normal"]),
            Paragraph(f"Growth over reporting period: {service['growth_percent']:.1f}%", styles["Normal"]),
            Paragraph(
                f"Highest month: {service['highest_month']['month']} "
                f"({service['highest_month']['activity']:,})",
                styles["Normal"],
            ),
            Paragraph(
                f"Lowest month: {service['lowest_month']['month']} "
                f"({service['lowest_month']['activity']:,})",
                styles["Normal"],
            ),
            Spacer(1, 8),
        ]

        data = [[
            "Month",
            "Views",
            "Sessions",
            "Active Users",
            "Total Activity",
        ]]

        for row in service["monthly_rows"]:
            data.append([
                row["month"],
                f"{row['views']:,}",
                f"{row['sessions']:,}",
                f"{row['users']:,}",
                f"{row['activity']:,}",
            ])

        table = Table(
            data,
            colWidths=[90, 90, 90, 90, 110],
            repeatRows=1,
        )

        table.setStyle(self.table_style())

        story.append(table)
        story.append(Spacer(1, 10))

        safe_name = self.safe_filename(service["property_name"])

        chart_path = self.make_service_trend_chart(
            service,
            f"ga4_trend_{safe_name}.png",
        )

        story.append(Image(chart_path, width=500, height=190))
        story.append(PageBreak())

        return story

    # ------------------------------------------------------------
    # PDF generation
    # ------------------------------------------------------------

    def build_summary_pdf(self, analysis):
        os.makedirs(REPORT_DIR, exist_ok=True)

        path = os.path.join(
            REPORT_DIR,
            REPORT_FILENAME,
        )

        doc = SimpleDocTemplate(
            path,
            pagesize=landscape(A4),
            rightMargin=20,
            leftMargin=20,
            topMargin=20,
            bottomMargin=20,
        )

        styles = getSampleStyleSheet()
        story = []

        months = analysis["months"]
        period = f"{months[0]} to {months[-1]}" if months else "No data"

        story.append(Paragraph("Tracking GA4 Monthly Summary", styles["Title"]))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            f"Generated: {timezone.localtime().strftime('%Y-%b-%d at %H:%M')}",
            styles["Normal"],
        ))
        story.append(Paragraph(f"Reporting period: {period}", styles["Normal"]))
        story.append(Paragraph(f"Total services: {GoogleAnalyticsStats.objects.count()}", styles["Normal"]))
        story.append(Paragraph(f"Services analysed: {len(analysis['analysed'])}", styles["Normal"]))
        story.append(Paragraph(f"Excluded, no Since date: {len(analysis['excluded'])}", styles["Normal"]))
        story.append(Spacer(1, 14))

        story += self.ranking_table(
            "Top 5 Busiest Services",
            analysis["busiest"],
            styles,
        )

        story += self.ranking_table(
            "Bottom 5 Least Busy Services",
            analysis["least_busy"],
            styles,
        )

        story += self.ranking_table(
            "Biggest Growth",
            analysis["biggest_growth"],
            styles,
        )

        story += self.ranking_table(
            "Biggest Decline",
            analysis["biggest_decline"],
            styles,
        )

        chart1 = self.make_bar_chart(
            "Top 5 busiest services",
            analysis["busiest"],
            "avg_activity",
            "ga4_top5_summary.png",
            xlabel="Average monthly activity",
        )

        chart2 = self.make_bar_chart(
            "Bottom 5 least busy services",
            analysis["least_busy"],
            "avg_activity",
            "ga4_bottom5_summary.png",
            xlabel="Average monthly activity",
        )

        chart3 = self.make_bar_chart(
            "Biggest growth",
            analysis["biggest_growth"],
            "growth_percent",
            "ga4_growth_summary.png",
            xlabel="Growth %",
        )

        chart4 = self.make_bar_chart(
            "Biggest decline",
            analysis["biggest_decline"],
            "growth_percent",
            "ga4_decline_summary.png",
            xlabel="Growth %",
        )

        story.append(PageBreak())
        story.append(Paragraph("Summary Charts", styles["Title"]))
        story.append(Spacer(1, 10))
        story.append(Image(chart1, width=520, height=230))
        story.append(Spacer(1, 18))
        story.append(Image(chart2, width=520, height=230))

        story.append(PageBreak())
        story.append(Paragraph("Growth and Decline Charts", styles["Title"]))
        story.append(Spacer(1, 10))
        story.append(Image(chart3, width=520, height=230))
        story.append(Spacer(1, 18))
        story.append(Image(chart4, width=520, height=230))

        story.append(PageBreak())
        story.append(Paragraph("Top 5 Busiest Service Details", styles["Title"]))
        story.append(Spacer(1, 10))

        for service in analysis["busiest"]:
            story += self.monthly_detail_table(service, styles)

        story.append(Paragraph("Bottom 5 Least Busy Service Details", styles["Title"]))
        story.append(Spacer(1, 10))

        for service in analysis["least_busy"]:
            story += self.monthly_detail_table(service, styles)

        story.append(Paragraph("Notes and Recommendations", styles["Title"]))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            "• Review services in the Bottom 5 list for tracking accuracy, visibility, and ongoing business need.",
            styles["Normal"],
        ))
        story.append(Paragraph(
            "• Check services with sudden decline for possible GA4 tag, DNS, access, redirect, or service availability issues.",
            styles["Normal"],
        ))
        story.append(Paragraph(
            "• Services without a Since date are excluded from rankings to avoid misleading results.",
            styles["Normal"],
        ))
        story.append(Paragraph(
            "• Activity = Views + Sessions + Active Users.",
            styles["Normal"],
        ))
        story.append(Paragraph(
            "• Average monthly activity is calculated only from months after tracking started.",
            styles["Normal"],
        ))

        doc.build(story)

        return path

    # ------------------------------------------------------------
    # Email
    # ------------------------------------------------------------

    def send_email(self, summary_pdf, analysis):
        today = timezone.localdate().strftime("%Y-%m")

        top_service = (
            analysis["busiest"][0]["property_name"]
            if analysis["busiest"]
            else "N/A"
        )

        bottom_service = (
            analysis["least_busy"][0]["property_name"]
            if analysis["least_busy"]
            else "N/A"
        )

        body = (
            "Hello,\n\n"
            "Attached is the monthly GA4 summary report generated by the "
            "Digital Library Tracking App.\n\n"
            f"Reporting month: {today}\n"
            f"Services analysed: {len(analysis['analysed'])}\n"
            f"Services excluded because they have no Since date: {len(analysis['excluded'])}\n\n"
            f"Top service: {top_service}\n"
            f"Lowest activity service: {bottom_service}\n\n"
            "The PDF includes:\n"
            "- Executive summary\n"
            "- Top 5 busiest services\n"
            "- Bottom 5 least busy services\n"
            "- Biggest growth services\n"
            "- Biggest decline services\n"
            "- Summary charts\n"
            "- Monthly breakdowns for top and bottom services\n"
            "- Notes and recommendations\n\n"
            "Regards,\n"
            "Digital Library Tracking App\n"
        )

        email = EmailMessage(
            subject=f"Monthly GA4 Summary Report - {today}",
            body=body,
            from_email=EMAIL_FROM,
            to=EMAIL_TO,
        )

        email.attach_file(summary_pdf)
        email.send()

    # ------------------------------------------------------------
    # Command entry point
    # ------------------------------------------------------------

    def handle(self, *args, **options):
        analysis = self.build_analysis()

        summary_pdf = self.build_summary_pdf(analysis)

        self.send_email(summary_pdf, analysis)

        self.stdout.write(
            self.style.SUCCESS(
                f"Monthly GA4 summary PDF report sent successfully: {summary_pdf}"
            )
        )