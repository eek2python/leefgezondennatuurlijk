"""
URL configuration for LeefNatuurlijkenGezond project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from django.contrib import admin
from django.urls import path, include
from products import views
from products import admin_views
from .sitemap_views import sitemap_xml
from django.views.generic import TemplateView

urlpatterns = [
   path("admin/product-images/", admin_views.product_images_admin, name="admin_product_images"),
   path("admin/", admin.site.urls),
   path("", views.homepage, name="homepage"),
   path("snijplanken/", views.snijplanken, name="snijplanken"),
   path("koekenpannen/", views.koekenpannen, name="koekenpannen"),
   path("hapjespannen/", views.hapjespannen, name="hapjespannen"),
   path("wokpannen/", views.wokpannen, name="wokpannen"),
   path("airfryers/", views.airfryers, name="airfryers"),
   path("airfryers/<slug:fmt>/", views.airfryers, name="airfryers_format"),
   path("vershoudcontainers/", views.vershoudcontainers, name="vershoudcontainers"),
   path("rvs-koekenpannen/", views.rvs_koekenpannen, name="rvs_koekenpannen"),
   path("over-ons/", views.over_ons, name="over_ons"),
   path("hoe-wij-beoordelen/", views.hoe_wij_beoordelen, name="hoe_wij_beoordelen"),
   path("privacy/", views.privacy, name="privacy"),
   path("product/<slug:slug>/", views.product_detail, name="product_detail"),
   path("blogs/", include("blogs.urls")),
   path("sitemap.xml", sitemap_xml, name="sitemap"),
   path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]
