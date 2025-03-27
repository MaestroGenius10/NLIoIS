from django.contrib import admin
from django.urls import path
from contextmanagerapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('result/', views.index, name='result'),
    path('save_analysis/', views.save_analysis, name='save_analysis'),
    path('dictionary/', views.view_dictionary, name='view_dictionary'),
    path('search/word/', views.search_word, name='search_word'),
    path('search/phrase/', views.search_phrase, name='search_phrase'),
    path('edit_word/<int:word_id>/', views.edit_word, name='edit_word'),
    path('update_word/<int:word_id>/', views.update_word, name='update_word'),
    path('articles/', views.view_articles, name='view_articles'),
    path('article/<int:article_id>/', views.view_article_text, name='view_article_text'),
    path('articles/<int:article_id>/edit/', views.edit_article, name='edit_article'),
]
