from django.urls import path
from linguistic_processor_app import views

urlpatterns = [
    path('', views.upload_file, name='upload_file'),
    path('analyze/', views.analyze_file, name='analyze_file'),
    path('save_results/', views.save_results, name='save_results'),
    path('dictionary/', views.view_dictionary, name='view_dictionary'),
    path('syntax_tree/<int:sentence_id>/', views.view_syntax_tree, name='view_syntax_tree'),
    path('edit_sentence/<int:sentence_id>/', views.edit_sentence, name='edit_sentence'),
    path('search_sentences/', views.search_sentences, name='search_sentences'),
    path('semantic_analyze/', views.semantic_analyze_file, name='semantic_analyze_file'),
    path('save_results_semantic/', views.save_results_semantic, name='save_results_semantic'),
    path('all-analyses/', views.all_semantic_analyses, name='all_semantic_analyses'),
    path('analysis/<int:analysis_id>/', views.view_semantic_analysis, name='view_semantic_analysis'),
    path('visualize-syntax/<int:sentence_id>/', views.visualize_syntax, name='visualize_syntax'),
]