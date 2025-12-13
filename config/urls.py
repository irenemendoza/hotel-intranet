# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('apps.dashboard.urls', "dashboard"), namespace="dashboard")),
    path('users/', include(('apps.users.urls', "users"), namespace="users")),
    path('rooms/', include(('apps.rooms.urls', "rooms"), namespace="rooms")),
    path('/rooms/maintenance/', include(('apps.rooms.urls', "maintenance"), namespace="maintenance")),
    path('rooms/cleaning/', include(('apps.rooms.urls', "cleaning"), namespace="cleaning")),
    path('tasks/', include(('apps.tasks.urls', "tasks"), namespace="tasks")),
    path('departments/', include(('apps.users.urls.departments_urls', "department"), namespace="departments")),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)