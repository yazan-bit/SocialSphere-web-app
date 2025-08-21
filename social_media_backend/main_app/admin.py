from django.contrib import admin
from .models import User,Post,Profile,PostImage,Comment,React,Notification

admin.site.register(User)
admin.site.register(Post)
admin.site.register(Profile)
admin.site.register(PostImage)
admin.site.register(Comment)
admin.site.register(React)
admin.site.register(Notification)
