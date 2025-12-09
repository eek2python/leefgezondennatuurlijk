from django.urls import path
from . import views

urlpatterns = [
   path("snijplanken/", views.snijplanken, name="snijplanken"),
   path("blog01/", views.blog01, name="blog01"),
   path("", views.product_list, name="product_list"),
   path("product/<slug:slug>/", views.product_detail, name="product_detail"),
   path("go/<slug:slug>/", views.track_and_redirect, name="track_and_redirect"),
]