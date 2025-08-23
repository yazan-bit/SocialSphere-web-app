from django.db import models
from main_app.models import Profile

class ChatRoom(models.Model):
    participants = models.ManyToManyField(Profile,related_name='chat_rooms')
    name = models.CharField(max_length=255,unique=True)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} id:{self.id}'


class MessageQuerySet(models.QuerySet):
    def get_unreaded_messages(self,user=None):
        if user is not None:
            user_profile = Profile.objects.get(user = user)
            return self.filter(is_read =False).exclude(sender = user_profile)


class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='room_messages')
    sender = models.ForeignKey(Profile,on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    objects = MessageQuerySet.as_manager()

    class Meta:
        ordering = ('timestamp',)

    def __str__(self):
        return f'{self.sender.get_username()}:{self.message[:20]}'