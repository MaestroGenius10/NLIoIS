from django.contrib import admin
from django.urls import path
from search_system_app import views  # импортируем view из приложения

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('crawl/auto/', views.auto_crawl, name='auto_crawl'),  # автоматический краулинг
    path('crawl/manual/', views.manual_crawl, name='manual_crawl'),  # краулинг по ссылке
    path('documents/', views.document_list, name='document_list'),  # список документов
    path('documents/<int:doc_id>/', views.document_detail, name='document_detail'),
    path('search/', views.search_results, name='search_results'),
    path('search-history/', views.search_history, name='search_history'),
    path('search-history/<int:query_id>/', views.search_history_results, name='search_history_results'),
    path('help/', views.help_view, name='help'),
    path('metrics/', views.evaluate_metrics_view, name='metrics_view'),
]
