from django.contrib import admin
from django.urls import path
from translator_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index_view, name='index'),

    # Ручной ввод теперь ведет на страницу анализа
    path('manual/', views.manual_analysis_view, name='manual_analysis_page'),

    # Новый путь для выполнения перевода после подтверждения
    path('execute-translation/', views.execute_translation_view, name='execute_translation'),

    # Новый путь для просмотра детального результата документа
    path('document/<int:doc_id>/', views.document_result_view, name='document_result'),

# Старые пути
path('api/translate/', views.api_translate_view,
     name='api_translate'),  # Оставляем для "живого" ввода, если понадобится
path('upload/', views.file_upload_view, name='file_upload_page'),
path('results/', views.translation_results_view, name='translation_results'),
path('dictionary/', views.dictionary_list_view, name='dictionary_list'),
path('dictionary/<int:pk>/', views.dictionary_detail_view, name='dictionary_detail'),
]