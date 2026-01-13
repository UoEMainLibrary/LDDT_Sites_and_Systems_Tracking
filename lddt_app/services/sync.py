from .ga_admin import get_all_ga4_properties
from django.db import models

class AnalyticsStat(models.Model):
    property_id = models.CharField(max_length=50)
    property_name = models.CharField(max_length=255)
    date = models.DateField()
    active_users = models.IntegerField()
    sessions = models.IntegerField()
    page_views = models.IntegerField()

    class Meta:
        unique_together = ('property_id', 'date')

    def __str__(self):
        return f"{self.property_name} - {self.date}"