from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime
from django.db.models import Q


class User(AbstractUser):
    email = models.EmailField(unique=True,null=False)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    def __str__(self):
        return self.username
    

class ProfileQuerySet(models.QuerySet):
    def followers(self,profile):
        return profile.followers
    
    def following(self,profile):
        return profile.following
    
    def friends(self,profile):
        friends = self.filter(
                following = profile,
                followers = profile
            )
        return friends.exclude(id = profile.id)

class ProfileManageer(models.Manager):
    def get_queryset(self):
        return ProfileQuerySet(self.model,self._db)


def save_profile_image(instance,filename):
    today = datetime.date.today()
    return f'users/{today.year}/{today.month}/{today.day}/user_{instance.user.id}/{filename}' 

class Profile(models.Model):
    user = models.OneToOneField(User,on_delete= models.CASCADE,related_name="profile")
    profile_image = models.ImageField(default="default.jpg",upload_to=save_profile_image)
    first_name = models.CharField(max_length=100,blank=True,null=True)
    last_name = models.CharField(max_length=100,blank=True,null=True)
    following = models.ManyToManyField("self",symmetrical=False,related_name="followers",blank=True)
    is_public = models.BooleanField(default=True)

    objects = ProfileManageer()
    

    def get_username(self):
        return self.user.username


    def get_user_id(self):
        return self.user.id
    
    def __str__(self):
        return f'{self.get_username()}_{self.id}'

    def save(self, *args,**kwargs):
        if not self.first_name:
            self.first_name = self.user.first_name

        if not self.last_name:
            self.last_name = self.user.last_name
        return super().save(*args,**kwargs)



class PostQuerySet(models.QuerySet):
    def recent_posts(self):
        return self.order_by('-date_posted')[:5]

    def post_search(self,query_params):
        lookup = Q(title__icontains = query_params)|Q(content__icontains = query_params)
        return self.filter(lookup)

    def profile_search(self,query_params):
        lookup = Q(user__user__username__icontains = query_params)
        return self.filter(lookup)

    def followers_posts(self,user_profile):
        followers = user_profile.following
        print(followers)
        posts = Post.objects.none()
        for profile in followers.all():
            posts |= self.filter(user = profile)
        return posts.distinct()



class PostManageer(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model,self._db)


class Post(models.Model):
    user = models.ForeignKey('Profile',on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(null=True,blank=True)

    objects = PostManageer()

    def save(self,*args,**kwargs):
        if not self.pk:
            self.date_updated = None
        else:
            self.date_updated = timezone.now()
        return super().save(*args,**kwargs)

    def __str__(self):
        return f'{self.user.get_username()} post_id: {self.pk}'
    

def save_post_images(instance,filename):
    today = datetime.date.today()
    return f'posts/{instance.post.user.get_username()}_{instance.post.user.id}/{today.year}_{today.month}_{today.day}/{filename}'

class PostImage(models.Model):
    post = models.ForeignKey(Post,on_delete=models.CASCADE,related_name='post_images')
    image = models.ImageField(upload_to=save_post_images,null=True,blank=True)
    


class React(models.Model):
    REACT_TYPES = [
        ('like','like'),
        ('dislike','dislike')
    ]

    profile = models.ForeignKey('profile',
                                on_delete=models.CASCADE)
    
    post = models.ForeignKey('Post',
                             on_delete=models.CASCADE,
                             related_name='post_reacts')
    
    react_type = models.CharField(max_length=20,choices=REACT_TYPES)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('profile','post')




class Comment(models.Model):
    post = models.ForeignKey(Post,on_delete=models.CASCADE,related_name="post_comments")
    user = models.ForeignKey('Profile',on_delete=models.CASCADE)
    comment_text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    replied_on = models.ForeignKey("self",
                                on_delete=models.CASCADE,
                                related_name="childern_comments_replies",
                                blank=True,
                                null=True)
    def __str__(self):
        return f'{self.user} comment on {self.post}, comment_id:{self.pk}'
    


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('like','like'),
        ('comment','comment'),
        ('follow','follow')
    ]

    recipient = models.ForeignKey(Profile,on_delete=models.CASCADE,related_name='notifications')
    sender = models.ForeignKey(Profile,on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=10,choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post,on_delete=models.CASCADE,null=True,blank=True)
    message = models.CharField(max_length=255)
    is_delevered = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'notification type: {self.notification_type} ,sender: \
            {self.sender.get_username()} ,recipient: \
                {self.recipient.get_username()} '