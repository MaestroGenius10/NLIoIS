from django.db import models
from django.contrib.auth.models import User
import uuid


class ChatExchange(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=255, editable=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    user_query = models.TextField()
    model_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_exchange"

    def __str__(self):
        return f"Log {id} for session {self.session_id}"


def get_chat_history(session_id: str, user):
    exchanges = ChatExchange.objects.filter(session_id=session_id, user=user).order_by(
        "created_at"
    )

    messages = []
    for exchange in exchanges:
        messages.extend(
            [
                {"role": "human", "content": exchange.user_query},
                {"role": "ai", "content": exchange.model_response},
            ]
        )

    return messages
