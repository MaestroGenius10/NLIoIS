from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatExchange

class ChatExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatExchange
        fields = ['session_id', 'user_query', 'model_response', 'created_at']
        read_only_fields = ['model_response', 'created_at']
        extra_kwargs = {
            'session_id': {
                'required': False,  # Make the field optional
                'allow_blank': True  # Optional: allows empty string values
            },
            'model_response': {'read_only': True},
            'created_at': {'read_only': True},
        }


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
