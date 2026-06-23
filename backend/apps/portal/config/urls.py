# -*- coding: utf-8 -*-
from django.urls import path

from .views import ThemePublicListView

app_name = "portal_skill"

urlpatterns = [
    path("themes/public/", ThemePublicListView.as_view(), name="themes-public"),
]
