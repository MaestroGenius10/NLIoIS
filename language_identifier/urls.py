from django.contrib import admin
from django.urls import path
from language_identifier_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.upload_files, name='index'),
    path('result/', views.result_view, name='result'),
    path('documents/', views.documents_list, name='documents_list'),
    path('documents/<int:doc_id>/', views.document_detail, name='document_detail'),
    path('analyze/', views.select_documents_for_analysis, name='select_documents_for_analysis'),
    path('analyze/results/', views.analyze_selected_documents, name='analyze_selected_documents'),
    path('download-results/', views.download_analysis_results, name='download_results'),
    path('history/', views.analysis_history_view, name='analysis_history'),
    path('help/', views.help_view, name='help_page'),
]
