# -*- coding: utf-8 -*-
from django.urls import path

from apps.monitoring.views import MonitoringReportView

app_name = "monitoring"

urlpatterns = [
    path("events/", MonitoringReportView.as_view(), name="events"),
]
