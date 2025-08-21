from django.shortcuts import render,get_object_or_404,get_list_or_404

from .serializers import (RegisterUser,
                         CustomTokenObtainPair,
                         PostSerializer,
                         PostCreateSerializer,
                         ProfileSerializer,
                         NotificationSerializer,
                         CreateCommentSerializer)

from rest_framework_simplejwt.views import TokenObtainPairView
from .models import (User,
                     Post,
                     React,
                     Notification,
                     Profile,
                     PostImage,
                     Comment)

from rest_framework.response import Response
from rest_framework import permissions,mixins,generics,status,authentication
from rest_framework.decorators import api_view, permission_classes,authentication_classes



class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class  = RegisterUser



class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPair


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile_avatar_username(request):
    user = request.user
    profile = Profile.objects.get(user = user)
    profile_serializer = ProfileSerializer(profile)
    return Response(profile_serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def toggle_post_like(request,post_pk,react_type = 'like'):
    user_profile = Profile.objects.get(user = request.user)
    post = get_object_or_404(Post,pk = post_pk)
    user_react = post.post_reacts.filter(profile = user_profile).first()

    if user_react and user_react.react_type == 'like':
        if react_type == 'dislike':
            user_react.react_type = user_react._action = react_type
            user_react.save()
        elif react_type == 'like':
            user_react.delete()
            user_react._action = 'undo like'

    elif user_react and user_react.react_type == 'dislike':
        if react_type == 'like':
            user_react.react_type = user_react._action = 'like'
            user_react.save()
        elif react_type == 'dislike':
            user_react.delete()
            user_react._action = 'undo dislike'
    
    else:
        user_react = React.objects.create(
            profile = user_profile,
            post = post,
            react_type = react_type
        )
        user_react._action = react_type
        
    return Response({
        'reacted_user':user_profile.get_username(),
        'post_title':post.title,
        'post_author':post.user.user.username,
        'action':user_react._action
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@authentication_classes([authentication.SessionAuthentication])
def following(request,profile_pk):
    user = request.user
    user_profile = Profile.objects.get(user = user)
    visited_profile = Profile.objects.get(id = profile_pk)
    if user_profile == visited_profile:
        return Response({
            'details':'you can not follow your own profile'
        })
    elif visited_profile.following.filter(id = user_profile.id).exists():
        visited_profile.following.remove(user_profile)
        visited_profile._action = "unfollow"
    else:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        visited_profile.following.add(user_profile)
        visited_profile._action = "follow"

        #create notification
        notification = Notification.objects.create(
            sender = user_profile,
            recipient = visited_profile,
            notification_type = 'follow',
            message = f'{user_profile.get_username()} start following you'
        )

        #send this notification to web socket
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
    

    return Response({
        'user_profile':user_profile.user.username,
        'visited_profile':visited_profile.user.username,
        'action':visited_profile._action
    })



class PostListView(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  generics.GenericAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = 'pk'
    
    def get(self,request,*args,**kwargs):
        pk = kwargs.get('pk')
        if pk is not None:
            return self.retrieve(request,*args,**kwargs)
        return self.list(request,*args,**kwargs)
    
class RecentPost(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    def get_queryset(self):
        return self.queryset.recent_posts()

class FollowersPosts(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        print(self.request.user)
        user_profile = Profile.objects.get(user = self.request.user)
        return self.queryset.followers_posts(user_profile)

class CreatPostView(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.SessionAuthentication]

class UnreadNotificationList(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_profile = Profile.objects.get(user = user)

        return user_profile.notifications.filter(is_read = False).order_by('-created_at')
    

class MarkNotificationDelivered(generics.UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Notification.objects.all()

    def perform_update(self, serializer):
        serializer.save(is_delevered = True)



class CreateCommentView(generics.CreateAPIView):
    serializer_class = CreateCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Comment.objects.all()

    def perform_create(self, serializer):
        print(serializer.validated_data)
        user_profile = Profile.objects.get(user = self.request.user)
        post_id = serializer.validated_data['post_id']
        post_instance = Post.objects.get(id = post_id)
        try:
            p_comment_id = serializer.validated_data.pop('parent_comment_id')
            p_comment = Comment.objects.get(id = p_comment_id)
            return serializer.save(post = post_instance,user = user_profile,replied_on=p_comment)
        except:
            return serializer.save(post = post_instance, user = user_profile)