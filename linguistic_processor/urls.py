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
]
