import os
from django.conf import settings


def ga_measurement_id(request):
    return {"GA_MEASUREMENT_ID": os.environ.get("GA_MEASUREMENT_ID", "")}


def site_origin(request):
    return {"SITE_URL": settings.SITE_URL.rstrip("/")}
