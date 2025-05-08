from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatExchangeSerializer, UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .models import ChatExchange, get_chat_history
from django.db.models import Subquery, OuterRef
from .langchain import get_rag_chain
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import uuid
from uuid import uuid4
import time
from uuid import UUID

class ChatView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        user = request.user
        messages = get_chat_history(session_id, user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)

    def post(self, request):
        print(request.data)
        serializer = ChatExchangeSerializer(data=request.data)
        if serializer.is_valid():
            user_query = serializer.validated_data["user_query"]
            session_id = serializer.validated_data.get("session_id")
            if not session_id:
                session_id = str(uuid.uuid4())

            chat_history = get_chat_history(session_id, user=request.user)
            rag_chain = get_rag_chain()
            model_response = rag_chain.invoke(
                {"input": user_query, "chat_history": chat_history}
            )["answer"]
            exchange = serializer.save(
                model_response=model_response, session_id=session_id, user=request.user
            )

            return Response(
                {"response": exchange.model_response, "session_id": session_id},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get distinct sessions with their first message
        first_message_subquery = ChatExchange.objects.filter(
            session_id=OuterRef('session_id')
        ).order_by('created_at')

        sessions = (
            ChatExchange.objects
            .filter(user=user)
            .values('session_id')
            .distinct()
            .annotate(
                first_message=Subquery(
                    first_message_subquery.values('user_query')[:1]
                ),
                first_time=Subquery(
                    first_message_subquery.values('created_at')[:1]
                )
            )
            .order_by('-first_time')
        )

        # Format the response
        session_data = [
            {
                "session_id": session['session_id'],
                "first_message": session['first_message']
            }
            for session in sessions
        ]

        return Response({"sessions": session_data}, status=status.HTTP_200_OK)


class UserRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User registered successfully."},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response(
                    {
                        "access_token": str(refresh.access_token),
                        "refresh_token": str(refresh),
                    }
                )
            else:
                return Response(
                    {"message": "Invalid credentials."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except User.DoesNotExist:
            return Response(
                {"message": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )


class ChatController(APIView):
    _chats = [{'id': 1,
               'title': f"Что ты умеешь?"},
              {'id': 2, 'title': f"Second chat {1}"}]
    # _chats = []
    _last_id = 2

    def get(self, request):
        return Response(sorted(self._chats, key=lambda x: x['id'], reverse=True))

    def post(self, request):
        self.__class__._last_id += 1
        new_chat = {
            'id': self.__class__._last_id,
            'title': f"Чат {self.__class__._last_id}"
        }
        self.__class__._chats.append(new_chat)
        return Response(new_chat, status=status.HTTP_201_CREATED)

    fake_chat_history = {
        1: {
            "id": 1,
            "title": "Чат о Python",
            "messages": [
                {"sender": "user", "text": "Как работает list comprehension?"},
                {"sender": "bot", "text": "List comprehension - это компактный способ создания списков..."}
            ],
        },
        2: {
            "id": 2,
            "title": "Чат о Django",
            "messages": [
                {"sender": "user", "text": "Как создать View в Django?", "timestamp": "2025-03-26T11:00:00Z"},
                {"sender": "bot", "text": "Вы можете создать View, унаследовавшись от View или APIView...",
                 "timestamp": "2025-03-26T11:02:00Z"}
            ],
            "created_at": "2025-03-26T10:45:00Z"
        },
        3: {
            "id": 3,
            "title": "Чат о REST API",
            "messages": [
                {"sender": "user", "text": "Какие методы HTTP используются в REST?",
                 "timestamp": "2025-03-27T12:00:00Z"},
                {"sender": "bot", "text": "Основные методы: GET, POST, PUT, PATCH, DELETE...",
                 "timestamp": "2025-03-27T12:01:30Z"}
            ],
            "created_at": "2025-03-27T11:50:00Z"
        }
    }


fake_chat_history = {
    uuid4(): {
        "id": 1,
        "title": "Чат о Python",
        "messages": [
            {"sender": "human", "text": "Привет! У меня вопрос по Python", "timestamp": "2025-03-25T09:55:00Z"},
            {"sender": "ai", "text": "Привет! Конечно, задавай свой вопрос.", "timestamp": "2025-03-25T09:55:30Z"},
            {"sender": "human", "text": "Как работает list comprehension?", "timestamp": "2025-03-25T10:00:00Z"},
            {"sender": "ai", "text": "List comprehension - это компактный способ создания списков...",
             "timestamp": "2025-03-25T10:01:00Z"},
            {"sender": "human", "text": "Спасибо, понятно!", "timestamp": "2025-03-25T10:02:00Z"},
            # Другие сообщения...
        ],
        "created_at": "2025-03-25T09:55:00Z"
    },
    uuid4(): {
        "id": 2,
        "title": "Чат о Django",
        "messages": [
            {"sender": "human", "text": "Здравствуйте, нужна помощь с Django", "timestamp": "2025-03-26T10:45:00Z"},
            {"sender": "ai", "text": "Здравствуйте! Чем могу помочь?", "timestamp": "2025-03-26T10:45:30Z"},
            {"sender": "human", "text": "Как создать View в Django?", "timestamp": "2025-03-26T11:00:00Z"},
            {"sender": "ai", "text": "Вы можете создать View, унаследовавшись от View или APIView...",
             "timestamp": "2025-03-26T11:02:00Z"},
            {"sender": "human", "text": "А как добавить его в urls.py?", "timestamp": "2025-03-26T11:03:00Z"},
            {"sender": "ai", "text": "Нужно добавить path() в urlpatterns...", "timestamp": "2025-03-26T11:04:00Z"},
            # Другие сообщения...
        ],
        "created_at": "2025-03-26T10:45:00Z"
    }
}

# views.py
from django.db import transaction


class ChatHistoryView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self, session_id):
        """Базовый queryset для всех операций"""
        return ChatExchange.objects.filter(
            session_id=session_id,
            user=self.request.user
        )

    def delete(self, request, chat_id):
        """Удаление всей истории чата"""
        try:
            with transaction.atomic():
                messages = self.get_queryset(chat_id)
                if not messages.exists():
                    return Response(
                        {"error": "Чат не найден"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                count = messages.count()
                messages.delete()

                return Response(
                    {
                        "message": f"Чат удален",
                        "deleted_messages": count
                    },
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def patch(self, request, chat_id):
        """Редактирование свойств чата"""
        try:
            new_title = request.data.get('title')
            if not new_title:
                return Response(
                    {"error": "Не указано новое название"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                # Находим первое сообщение в чате
                first_message = self.get_queryset(chat_id).order_by('created_at').first()

                if not first_message:
                    return Response(
                        {"error": "Чат не найден"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Обновляем "заголовок" чата (первое сообщение)
                first_message.user_query = new_title
                first_message.save()

                # Опционально: обновляем название во всех связанных чатах
                # если нужно синхронизировать данные

                return Response(
                    {"message": "Название чата обновлено"},
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request, chat_id):
        """Получение истории чата (опционально)"""
        messages = self.get_queryset(chat_id).order_by('created_at')
        serializer = ChatExchangeSerializer(messages, many=True)
        return Response(serializer.data)



