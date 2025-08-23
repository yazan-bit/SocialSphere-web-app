from django.urls import re_path
from main_app import consumers as notification_consumer
# from chat_app import consumers as chat_app_consumer


websocket_urlpatterns = [
    re_path(r'ws/notification/$',\
            notification_consumer.NotificationConsumer.as_asgi()),
#     re_path(r'ws/chat/(?P<room_id>\w+)/$',\
#             chat_app_consumer.UserChatConsumer.as_asgi())
]