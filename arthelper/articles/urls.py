from django.urls import path
from . import views

urlpatterns = [
    path('articles/create/', views.article_create, name='article_create'),
    path('articles/<int:pk>/edit/', views.article_edit, name='article_edit'),
    path('articles/<int:pk>/delete/', views.article_delete, name='article_delete'),
    path('articles/<int:pk>/export/docx/', views.export_docx, name='export_docx'),
    path('articles/<int:pk>/export/pdf/', views.export_pdf, name='export_pdf'),
    path('authors/<int:pk>/delete/', views.author_delete, name='author_delete'),
    path('references/<int:pk>/delete/', views.reference_delete, name='reference_delete'),
    path('udc/search/', views.udc_search, name='udc_search'),
    path('article/<int:pk>/generate-annotation/', views.generate_annotation_ajax, name='generate_annotation'),
    path('article/<int:pk>/generate-keywords/', views.generate_keywords_ajax, name='generate_keywords'),
    path('article/<int:pk>/translate/', views.translate_metadata_ajax, name='translate_metadata'),
]