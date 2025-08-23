from rest_framework import generics,permissions,status
from .models import ChatMessage,ChatRoom
from main_app.models import Profile
from main_app.serializers import ProfileSerializer
from .serialzier import (ChatMessageSerializer,
                         ChatRoomSerializer,
                         CreatePrivateChatRoomSerializer,
                         UserChatRoomSerializer)
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication


class ProfilesFriendsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()

    def get_queryset(self):
        profile = Profile.objects.get(user = self.request.user)
        return self.queryset.friends(profile)



class ProfilesFollowersView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()

    def get_queryset(self):
        profile = Profile.objects.get(user = self.request.user)
        return self.queryset.followers(profile)


class ProfilesFollowingView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()

    def get_queryset(self):
        profile = Profile.objects.get(user = self.request.user)
        return self.queryset.following(profile)



class PrivateRoomCreateView(generics.CreateAPIView):
    serializer_class = CreatePrivateChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    

    def create(self,request,*args,**kwargs):
        user_profile = Profile.objects.get(user = request.user)
        other_user_id = request.data.get('other_user_id')
        try:
            other_user = Profile.objects.get(id = other_user_id)
            if user_profile == other_user:
                return Response(
                    {'details':'you can not create private room with yourself'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except:
            return Response(
                {'details':'user does not exists'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        #check if private room already exists
        private_rooms = ChatRoom.objects.filter(is_private = True)
        existing_room = private_rooms.filter(participants = user_profile).\
            filter(participants = other_user).first()
        
        if existing_room:
            serializer = CreatePrivateChatRoomSerializer(existing_room)
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        
        room = ChatRoom.objects.create(
            name = f'private_{user_profile.id}_{other_user.id}',
            is_private = True
        )
        room.participants.add(user_profile,other_user)

        serializer = CreatePrivateChatRoomSerializer(existing_room)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class UserChatRooms(generics.ListAPIView):
    serializer_class = UserChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    # authentication_classes = [SessionAuthentication]

    def get_queryset(self):
        user = self.request.user
        user_profile = Profile.objects.get(user = user)

        return user_profile.chat_rooms
    

class ChatRoomMessages(generics.RetrieveAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    # authentication_classes = [SessionAuthentication]
    lookup_field = 'pk'
    queryset = ChatRoom.objects.all()



class UserUnreadedMessages(generics.ListAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    # authentication_classes = [SessionAuthentication]
    lookup_field = 'pk'
    queryset = ChatMessage.objects.all()

    def get_queryset(self):
        user = self.request.user
        print(user)
        return self.queryset.get_unreaded_messages(user)
