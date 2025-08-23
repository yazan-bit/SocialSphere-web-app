from django.shortcuts import render,get_object_or_404,get_list_or_404

from .serializers import (RegisterUser,
                         CustomTokenObtainPair,
                         PostSerializer,
                         PostImageSerializer,
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
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.parsers import MultiPartParser,FormParser

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi



class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class  = RegisterUser


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPair


@swagger_auto_schema(
    method='get',
    tags=['profiles'],
    operation_description='get athenticated user_profile details[username,profile_image]'
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile_avatar_username(request):
    user = request.user
    profile = Profile.objects.get(user = user)
    profile_serializer = ProfileSerializer(profile)
    return Response(profile_serializer.data)


@swagger_auto_schema(
    method='post',
    tags=['posts'],
    operation_description='toggle post react[like,dislike]'
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_post_like(request,post_pk,react_type = 'like'):
    if react_type not in ('like','dislike'):
        return Response({
            'details':'react_type should be \'like\' or \'dislike\' only'
        },status=status.HTTP_400_BAD_REQUEST)
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


@swagger_auto_schema(
    method='post',
    tags=['profiles'],
    operation_description='follow,un_follow profile'
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@authentication_classes([authentication.SessionAuthentication])
def following(request,profile_pk):
    user = request.user
    print(user,"######################################")
    user_profile = get_object_or_404(Profile,user = user)
    print("######################################")
    other_profile = get_object_or_404(Profile,id=profile_pk)
    if user_profile == other_profile:
        return Response({
            'details':'you can not follow your own profile'
        })
    elif other_profile.following.filter(id = user_profile.id).exists():
        other_profile.following.remove(user_profile)
        other_profile._action = "unfollow"
    else:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        other_profile.following.add(user_profile)
        other_profile._action = "follow"

        #create notification
        notification = Notification.objects.create(
            sender = user_profile,
            recipient = other_profile,
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
        'visited_profile':other_profile.user.username,
        'action':other_profile._action
    })



class PostListView(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  generics.GenericAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    @swagger_auto_schema(
        tags=['posts'],
        operation_description='get post/posts'
    )
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
    
    @swagger_auto_schema(
        tags=['posts'],
        operation_description='get recent posts'
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class FollowingPosts(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_profile = Profile.objects.get(user = self.request.user)
        return self.queryset.following_posts(user_profile)
    
    @swagger_auto_schema(
        tags=['posts'],
        operation_description='get followed users posts'
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class CreatePostView(APIView):
    # permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    MAX_FILE_COUNT = 5
    MAX_FILE_SIZE = 5 * 1024 * 1024
    ALLOWED_FILE_TYPES = ['images/jpg','images/jpeg','images/png']
    @swagger_auto_schema(
        operation_description="Create Post",
        tags=['posts'],
        manual_parameters=[
            openapi.Parameter(
                'title',
                openapi.IN_FORM,
                description="Required Post Title",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'content',
                openapi.IN_FORM,
                description="Required contnet of the post",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'images',
                openapi.IN_FORM,
                description="Post Images (Optional), should not exceed (5 images,5 mb per img)",
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_FILE),
                required=False
            ),
        ],
        responses={
            201: 'Created Post Succesfully',
            400: 'Bad Request'
        }
    )
    def post(self, request, *args, **kwargs):
        user_profile = get_object_or_404(Profile,user = request.user)
        images = request.FILES.getlist('images')
        if len(images) > self.MAX_FILE_COUNT:
            return Response({
                'details':'images should be less than 5 images'
            },
            status=status.HTTP_400_BAD_REQUEST)
        for img in images:
            if img.size > self.MAX_FILE_SIZE:
                return Response({
                'details':'image should not exceed 5 mb'
            },
            status=status.HTTP_400_BAD_REQUEST)
        post = Post.objects.create(user = user_profile ,\
                                    title = request.data.get('title') ,\
                                        content = request.data.get('content'))

        for img in images:
            PostImage.objects.create(post = post , image = img)

        post_images = post.post_images
        context = {}
        context['request'] = request
        images_serializer = PostImageSerializer(post_images,many=True,context=context)

        return Response({
            'details':'post created successfuly',
            'post_details':{
                'user_name':post.user.get_username(),
                'title':post.title,
                'content':post.content,
                'images':images_serializer.data
            }
        })


class UnreadNotificationList(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_profile = Profile.objects.get(user = user)

        return user_profile.notifications.filter(is_read = False).order_by('-created_at')
    

@swagger_auto_schema(
    method='get',
    tags=['notifications'],
    operation_description='mark a notifications as readed'
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_mark_read(request,notification_id):
    notification = get_object_or_404(Notification,id = notification_id)
    user = request.user
    user_profile = Profile.objects.get(user = user)
    if notification.recipient != user_profile:
        return Response({
            'details':'you can\t mark this notificaion as readed'
        })
    notification.is_read = True
    notification.save()

    return Response({
        'details':f'notification: {notification.message} is readed'
    })




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
            
    @swagger_auto_schema(
        tags=['posts'],
        operation_description='create comment or replay on comment'
    )    
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)