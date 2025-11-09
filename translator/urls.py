from django.urls import path
from translator_app import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('manual/', views.manual_analysis_view, name='manual_analysis_page'),
    path('execute-translation/', views.execute_translation_view, name='execute_translation'),
    path('upload/', views.file_analysis_view, name='file_upload_page'),
    path('execute-file-translation/', views.execute_file_translation_view, name='execute_file_translation'),
    path('document/<int:doc_id>/', views.document_result_view, name='document_result'),
    path('results/', views.translation_results_view, name='translation_results'),
    path('dictionary/', views.dictionary_list_view, name='dictionary_list'),
    path('api/translate/', views.api_translate_view, name='api_translate'),
    path('dictionary/<int:pk>/', views.dictionary_detail_view, name='dictionary_detail'),
    path('document/<int:doc_id>/download/', views.download_result_view, name='download_result'),
    path('api/syntax-tree/en/<int:doc_id>/', views.generate_syntax_tree_en_view, name='generate_syntax_tree_en'),
    path('api/syntax-tree/ru/<int:doc_id>/', views.generate_syntax_tree_ru_view, name='generate_syntax_tree_ru'),
    path('help/', views.help_view, name='help_page'),
]