# apps/users/urls/auth_urls.py (o crear apps/auth/)
from django.urls import path
from django.contrib.auth import views as auth_views

app_name = 'auth'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='auth/login.html'
    ), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(
        template_name='auth/logout.html'
    ), name='logout'),
    
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='auth/password_reset.html'
    ), name='password_reset'),
]