# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include(('apps.dashboard.urls', "dashboard"), namespace="dashboard")),

    path('accounts/', include('django.contrib.auth.urls')),
    path('employees/', include(('apps.users.urls.employees_urls', "employees"), namespace="employees")),
    path('attendance/', include(('apps.users.urls.attendance_urls', "attendance"), namespace="attendance")),
    path('rooms/', include(('apps.rooms.urls', "rooms"), namespace="rooms")),
    path('leave/', include(('apps.users.urls.leave_urls', "leave"), namespace="leave")),
    path('tasks/', include(('apps.tasks.urls', "tasks"), namespace="tasks")),
    path('cleaning/', include(('apps.rooms.urls.rooms_cleaning_urls', "cleaning"), namespace="cleaning")),
    path('maintenance/', include(('apps.rooms.urls.rooms_maintenance_urls', "maintenance"), namespace="maintenance")),
    path('departments/', include(('apps.users.urls.departments_urls', "department"), namespace="departments")),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)