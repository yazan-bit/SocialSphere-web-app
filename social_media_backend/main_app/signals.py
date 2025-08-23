from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User,Profile,React,Notification,Comment
from chat_app.models import ChatRoom,ChatMessage
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@receiver(post_save,sender = User)
def create_profile(sender,instance,created,**kwargs):
    if created:
        Profile.objects.create(user = instance)


@receiver(post_save,sender = User)
def save_profile(sender,instance,**kwargs):
    instance.profile.save()


@receiver(post_save,sender = React)
def create_react_notification(sender,instance,**kwargs):
    if instance.react_type == 'like':
        notification = Notification.objects.create(
            sender = instance.profile,
            post = instance.post,
            recipient = instance.post.user,
            notification_type = instance.react_type,
            message = f'{instance.profile.get_username()} liked your post: {instance.post.title}'
        )
        print('created notification successfuly')
        channel_layer = get_channel_layer()
        print(f'notification_{notification.recipient.get_user_id()}')
        try:
            print('trying to send react notification')
            async_to_sync(channel_layer.group_send)(
                f'notification_{notification.recipient.get_user_id()}',
                {
                    'type':'send_notification',
                    'notification':{
                        'id':notification.id,
                        'sender':{
                            'name':notification.sender.get_username(),
                            'avatar':notification.sender.profile_image.url
                            },
                        'post_id':notification.post.id,
                        'post_title':notification.post.title,
                        'recipient':notification.recipient.get_username(),
                        'notification_type':notification.notification_type,
                        'message':notification.message,
                        'is_read':notification.is_read,
                        'timestamp':f'{notification.created_at}'
                    }
                }
            )
        except:
            print('user is not logged in right now')


@receiver(post_save,sender = Comment)
def create_comment_notification(sender,instance,created,**kwargs):
    if created:
        notification = Notification.objects.create(
            sender = instance.user,
            post = instance.post,
            recipient = instance.post.user,
            notification_type = 'comment',
            message = f'{instance.user.get_username()} commented on your post: {instance.post.title}'
        )

        channel_layer = get_channel_layer()
        try:
            async_to_sync(channel_layer.group_send)(
                f'notification_{notification.recipient.get_user_id()}',
                {
                    'type':'send_notification',
                    'notification':{
                        'id':notification.id,
                        'sender':{
                            'name':notification.sender.get_username(),
                            'avatar':notification.sender.profile_image.url
                            },
                        'post_id':notification.post.id,
                        'post_title':notification.post.title,
                        'recipient':notification.recipient.get_username(),
                        'notification_type':notification.notification_type,
                        'message':notification.message,
                        'is_read':notification.is_read,
                        'timestamp':f'{notification.created_at}'
                    }
                }
            )
            notification.is_delivered = True
            notification.save()
        except:
            print('user is not logged in right now')

