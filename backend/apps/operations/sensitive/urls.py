"""敏感词 URL。"""
from django.urls import path

from . import views

app_name = "ops_sensitive"

urlpatterns = [
    path("", views.word_list, name="list"),
    path("add/", views.word_add, name="add"),
    path("<int:pk>/toggle/", views.word_toggle, name="toggle"),
    path("<int:pk>/delete/", views.word_delete, name="delete"),
    path("check/", views.word_check, name="check"),
]
