from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
]