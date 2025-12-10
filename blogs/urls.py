from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path("", views.blogs_overview, name="blogs_overview"),

    path("<slug:slug>/", views.blogs_detail, name="blogs_detail"),

    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]

urlpatterns += [
   path(
       "robots.txt",
       TemplateView.as_view(template_name="robots.txt", content_type="text/plain")
   ),
]