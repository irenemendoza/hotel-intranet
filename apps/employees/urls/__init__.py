from django.urls import include, path

urlpatterns = [
    path("departments/", include("apps.employees.urls.departments_urls")),
]