from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path("", views.blogs_overview, name="blogs_overview"),
    path("<slug:slug>/", views.blogs_detail, name="blogs_detail"),
]