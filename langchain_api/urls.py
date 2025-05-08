from django.urls import path
from .views import (
    ChatView,
    UserLoginView,
    UserRegisterView,
    ChatListView,
    ChatController,
    ChatHistoryView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Основные API эндпоинты
    path("chat/", ChatView.as_view(), name="create_response"),
    path("chat/sessions/", ChatListView.as_view(), name="session_list"),
    path("chat/<uuid:session_id>/", ChatView.as_view(), name="chat_history"),

    # Унифицированный эндпоинт для управления историей чатов
    path("chat-history/<uuid:chat_id>/", ChatHistoryView.as_view(), name="chat-history-manage"),

    # Аутентификация
    path("register/", UserRegisterView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Дополнительные эндпоинты (можно оставить для обратной совместимости)
    path('chats/', ChatController.as_view(), name='chat-controller'),

    # Устаревшие эндпоинты (можно удалить после перехода на chat-history/)
    # path('get-chat-history/<uuid:chat_id>/', ChatHistoryView.as_view(), name='chat-history'),
    # path('delete-chat/<uuid:chat_id>/', ChatHistoryView.as_view(), name='delete-chat'),
    # path('edit-chat-title/<uuid:chat_id>/', ChatHistoryView.as_view(), name='edit-chat-title'),
]