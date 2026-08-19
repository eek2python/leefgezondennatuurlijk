from django.urls import path


def unhandled_exception(_request):
    raise RuntimeError("production logging sentinel")


urlpatterns = [
    path("_test/unhandled-exception/", unhandled_exception),
]