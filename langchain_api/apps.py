from django.apps import AppConfig
from django.apps import AppConfig
import os
from .chroma import index_document_to_chroma, delete_doc_from_chroma


class LangchainApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'langchain_api'
        
    def ready(self):
        # Prevent running twice in development
        if os.environ.get('RUN_MAIN') != 'true' and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            return

        # Configure your files (path, ID)
        files_to_load = [
            ('./documents/all_articles.txt', 1),  # Update paths as needed
        ]

        for file_path, file_id in files_to_load:
            # Clean up existing entries first
            delete_doc_from_chroma(file_id)
            
            # Index new documents
            if not index_document_to_chroma(file_path, file_id):
                print(f"Failed to index {file_path}")
            else:
                print(f"Successfully indexed {file_path}")
