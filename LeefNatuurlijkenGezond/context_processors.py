import os
from django.conf import settings


def ga_measurement_id(request):
    return {"GA_MEASUREMENT_ID": os.environ.get("GA_MEASUREMENT_ID", "")}


def site_origin(request):
    return {"SITE_URL": settings.SITE_URL.rstrip("/")}


def appliance_navigation(request):
    from products.appliance_catalogue import APPLIANCE_CATEGORIES
    return {"appliance_categories": APPLIANCE_CATEGORIES}
