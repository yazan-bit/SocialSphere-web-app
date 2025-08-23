from rest_framework import serializers
from main_app.serializers import ProfileSerializer
from .models import ChatMessage,ChatRoom

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.get_username',read_only=True)
    class Meta:
        model = ChatMessage
        fields = [
            'sender_username',
            'message',
            'is_read',
            'timestamp'
        ]


class ChatRoomSerializer(serializers.ModelSerializer):
    room_messages = ChatMessageSerializer(many = True , read_only = True)
    participants = ProfileSerializer(many = True)
    allias_name = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'name',
            'allias_name',
            'is_private',
            'participants',
            'created_at',
            'room_messages'
        ]

    def get_allias_name(self,object):
        request = self.context.get('request')
        user = request.user
        participants_count = object.participants.count()
        if participants_count == 2:
            allias_name = object.participants.exclude(user = user).first().get_username()
            return allias_name
        else:
            return object.name


class UserChatRoomSerializer(serializers.ModelSerializer):
    participants = ProfileSerializer(many = True)
    allias_name = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'name',
            'allias_name',
            'is_private',
            'participants',
            'created_at',
        ]

    def get_allias_name(self,object):
        request = self.context.get('request')
        user = request.user
        participants_count = object.participants.count()
        if participants_count == 2:
            allias_name = object.participants.exclude(user = user).first().get_username()
            return allias_name
        else:
            return object.name




class CreatePrivateChatRoomSerializer(serializers.ModelSerializer):
    participants = ProfileSerializer(read_only=True,many = True)
    other_user_id = serializers.CharField(write_only=True)
    name = serializers.CharField(read_only=True)
    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'name',
            'other_user_id',
            'participants'
        ]