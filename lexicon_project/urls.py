from django.contrib import admin
from django.urls import path
from lexicon_app import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('dictionary/', views.view_dictionary, name='view_dictionary'),
    path('save_collocations/', views.save_collocations, name='save_collocations'),
    path('edit_collocation/<int:collocation_id>/', views.edit_collocation, name='edit_collocation'),
    path('delete_collocation/<int:collocation_id>/', views.delete_collocation, name='delete_collocation'),
    path('search_collocations/', views.search_collocations, name='search_collocations'),
]
