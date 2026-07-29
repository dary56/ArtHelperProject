from django.urls import path
from . import views

urlpatterns = [
    path('journals/create/', views.journal_create, name='journal_create'),
    path('journals/<int:pk>/delete/', views.journal_delete, name='journal_delete'),
    path('journals/<int:pk>/', views.journal_detail, name='journal_detail'),
    path('journals/<int:journal_pk>/template/add/', views.template_add, name='template_add'),
    path('templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
]