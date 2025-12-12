from django.urls import include, path

urlpatterns = [
    path("departments/", include("apps.users.urls.departments_urls")),
]