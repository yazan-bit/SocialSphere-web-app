from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import (User,
                     Post,
                     Profile,
                     PostImage,
                     Notification,
                     React,
                     Comment)

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class RegisterUser(serializers.ModelSerializer):
    password = serializers.CharField(write_only = True,required = True)
    password2 = serializers.CharField(write_only = True,required = True)

    class Meta:
        model = User
        fields = ["username","email","password","password2"]

    def validate(self, attrs):
        email = attrs['email']
        if User.objects.filter(email = email).exists():
            raise serializers.ValidationError(
                {
                    'email': 'email alreday exists try another one'
                }
            )
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {
                    'password': 'password and password2 should matched'
                }
            )
        return attrs
    

    def create(self, validated_data):
        user = User.objects.create(
            username = validated_data['username'],
            email = validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    

class CustomTokenObtainPair(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token =  super().get_token(user)
        token['user_id'] = user.id
        token['username'] = user.username
        return token


class PostImageSerializer(serializers.Serializer):
    image = serializers.ImageField()


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='get_username')
    class Meta:
        model = Profile
        fields = [
            'id',
            'profile_image',
            'username'
            ]


class InlinePostUserReacts(serializers.Serializer):
    profile_details = ProfileSerializer(source = 'profile',read_only = True)
    react_type = serializers.CharField(read_only=True)


#################################################################################
class PostCommentsSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    author = serializers.CharField(source='user.get_username',read_only=True)
    avatar = serializers.ImageField(source='user.profile_image',read_only=True)
    text = serializers.CharField(source='comment_text',read_only = True)
    date = serializers.CharField(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)

    def get_replies(self,obj):
        child_comments = obj.childern_comments_replies.all()
        child_comments_serializer = PostCommentsSerializer(child_comments,many=True,read_only=True)
        return child_comments_serializer.data
    

class CreateCommentSerializer(serializers.ModelSerializer):
    post_id = serializers.CharField(required=True,write_only=True)
    parent_comment_id = serializers.CharField(write_only=True,required=False,allow_null=True)

    class Meta:
        model = Comment
        fields = [
            'id',
            'post_id',
            'comment_text',
            'parent_comment_id'
        ]

    def validate(self, attrs):
        try:
            post = Post.objects.get(id = attrs['post_id'])
            if attrs.get('parent_comment_id'):
                try:
                    p_comment = Comment.objects.get(id = attrs['parent_comment_id'])
                except:
                    raise serializers.ValidationError({
                        'the comment you tried to replied has been deleted'
                    })
                if p_comment.post.pk != post.pk:
                    raise serializers.ValidationError({
                        'this comment and what it replied on are not related to the same post'
                    })
                return attrs
            else:
                return attrs
        except serializers.ValidationError:
            raise
        except:
            raise serializers.ValidationError({
                'the post you trying to comment on may have been deleted'
            })
    
############################################################################################

class PostSerializer(serializers.ModelSerializer):
    author = ProfileSerializer(source = 'user',read_only=True)
    images = serializers.SerializerMethodField(read_only = True)
    total_likes = serializers.SerializerMethodField()
    total_dislikes = serializers.SerializerMethodField()
    reacts_details = InlinePostUserReacts(source = 'post_reacts',many=True)
    post_comments = serializers.SerializerMethodField(read_only=True)
    follow_this_profile = serializers.SerializerMethodField(read_only=True)
    like = serializers.SerializerMethodField()
    dislike = serializers.SerializerMethodField()
    user_react_type = serializers.SerializerMethodField(read_only = True)

    class Meta:
        model = Post
        fields = ['id',
                  'title',
                  'author',
                  'follow_this_profile',
                  'content',
                  'total_likes',
                  'total_dislikes',
                  'reacts_details',
                  'date_posted',
                  'date_updated',
                  'images',
                  'like',
                  'dislike',
                  'user_react_type',
                  'post_comments']

    def get_total_likes(self,obj):
        total_likes = obj.post_reacts.filter(react_type = 'like').count()
        return int(total_likes)
    
    def get_total_dislikes(self,obj):
        total_dislikes = obj.post_reacts.filter(react_type = 'dislike').count()
        return int(total_dislikes)
    
    def get_post_comments(self,obj):
        post_comments = obj.post_comments.filter(replied_on = None)
        comments_count = obj.post_comments.count()
        all_post_comments = PostCommentsSerializer(post_comments,many=True)
        return {
            'comments_count':comments_count,
            'comments':all_post_comments.data
            }
    
    def get_follow_this_profile(self,object):
        request = self.context.get('request')
        return reverse("follow_profile",
                       kwargs={
                           'profile_pk':object.user.pk
                       },
                       request=request)
    
    def get_images(self,object):
        images = object.post_images.all()
        images_serializer = PostImageSerializer(images,many=True,read_only=True,context = self.context)
        return images_serializer.data
    

    def get_like(self,object):
        request = self.context.get('request')
        if request is None:
            return None
        
        return reverse("post_react",
                       kwargs={
                           'post_pk':object.pk,
                           'react_type':'like'
                       },
                       request=request)
    

    def get_dislike(self,object):
        request = self.context.get('request')
        if request is None:
            return None
        
        return reverse("post_react",
                       kwargs={
                           'post_pk':object.pk,
                           'react_type':'dislike'
                       },
                       request=request)
    
    def get_user_react_type(self,object):
        request = self.context.get('request')
        user = request.user
        if user.is_anonymous:
            return None
        else:
            user_profile = Profile.objects.get(user = user)
            if React.objects.filter(post = object , profile = user_profile).exists():
                return React.objects.filter(post = object , profile = user_profile).first().react_type
            else:
                return None



class PostCreateSerializer(serializers.ModelSerializer):
    ######################################
    images = serializers.ListField(
        child = serializers.ImageField(),
        required = False,
        allow_empty = True
    )
    #######################################
    class Meta:
        model = Post
        fields = [
            'title',
            'content',
            'images'
        ]

    def create(self, validated_data):
        images = validated_data.pop('images',[])
        request = self.context.get('request')
        user = request.user
        user_profile = Profile.objects.get(user = user)
        post_instance = Post.objects.create(user = user_profile,**validated_data)

        #create PostImage instance if there are images attached with the request
        for img in images:
            PostImage.objects.create(post = post_instance,image = img)

        return post_instance

    
class NotificationSerializer(serializers.ModelSerializer):
    post_id = serializers.SerializerMethodField()
    post_title = serializers.SerializerMethodField()
    class Meta:
        model = Notification
        fields = [
            'id',
            'sender',
            'post_id',
            'post_title',
            'recipient',
            'notification_type',
            'message',
            'is_read',
        ]

    def save(self, **kwargs):
        return super().save(**kwargs)
    
    def get_post_id(self,obj):
        return obj.post.id

    def get_post_title(self,obj):
        return obj.post.title