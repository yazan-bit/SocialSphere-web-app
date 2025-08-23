from django.urls import path
from . import views

urlpatterns = [
    path('friends_list/',views.ProfilesFriendsView.as_view()),
    path('followers_list/',views.ProfilesFollowersView.as_view()),
    path('following_list/',views.ProfilesFollowingView.as_view()),
    path('user_chat_rooms/',views.UserChatRooms.as_view()),
    path('chat_room/<int:pk>/',views.ChatRoomMessages.as_view()),
    path('create_private_chatroom/',views.PrivateRoomCreateView.as_view()),
]