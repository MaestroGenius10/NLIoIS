"""
Основной файл URL-конфигурации проекта.
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from audiospeaker_app import views

urlpatterns = [
    # URL для админ-панели Django
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),

    path('tts/', views.text_to_speech_view, name='text_to_speech'),
    path('history/', views.speech_history_view, name='speech_history'),
    path('api/synthesize/', views.synthesize_speech_api, name='synthesize_speech_api'),
    path('help/', views.help_view, name='help_page'),
    path('recognize/', views.recognize_speech_view, name='recognize_speech'),
    path('recognize/history/', views.recognition_history_view, name='recognition_history'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)