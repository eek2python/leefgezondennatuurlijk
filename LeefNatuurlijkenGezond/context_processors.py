import os


def ga_measurement_id(request):
    return {"GA_MEASUREMENT_ID": os.environ.get("GA_MEASUREMENT_ID", "")}
