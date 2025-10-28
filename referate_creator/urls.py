from django.contrib import admin
from django.urls import path
from referate_creator_app import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.index, name="index"),
    path("documents/", views.documents_list, name="documents_list"),
    path("upload/", views.upload_document, name="upload_document"),
    path('documents/<int:doc_id>/', views.document_detail, name='document_detail'),
    path("select/", views.select_documents, name="select_documents"),
    path("results/", views.referencing_results, name="referencing_results"),
    path("download/", views.download_report, name="download_report"),
    path("history/", views.history_list, name="history_list"),
    path("help/", views.help_page, name="help_page"),
]
