
from django.urls import path
from apps.employees.views.profile_views import (
    MyProfileView,
    ProfileUpdateView,
    ProfileStatsView
)
app_name = 'profiles'

urlpatterns = [
    # Rutas de perfil personal
    path('my-profile/', MyProfileView.as_view(), name='my-profile'),
    path('profile/update/', ProfileUpdateView.as_view(), name='update'),
    path('profile/stats/', ProfileStatsView.as_view(), name='stats'),
]