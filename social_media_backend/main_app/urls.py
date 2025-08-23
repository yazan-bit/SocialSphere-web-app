from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('token/get_token/',views.CustomTokenObtainPairView.as_view()),
    path('token/refresh_token/',TokenRefreshView.as_view()),
    path('register/',views.RegisterUserView.as_view()),
    path('posts/get/',views.PostListView.as_view()),
    path('posts/get/<int:pk>/',views.PostListView.as_view()),
    path('posts/recent/',views.RecentPost.as_view()),
    path('posts/following/',views.FollowingPosts.as_view()),
    path('posts/create/',views.CreatePostView.as_view()),
    path('posts/post_react/<int:post_pk>/<str:react_type>',views.toggle_post_like,name = 'post_react'),
    path('posts/post_comment/',views.CreateCommentView.as_view()),
    path('profiles/profile_details/',views.profile_avatar_username),
    path('profiles/follow_unfollow/<int:profile_pk>/',views.following,name='follow_profile'),
    path('notifications/list/',views.UnreadNotificationList.as_view()),
    path('notifications/read/<int:pk>',views.notification_mark_read),
    ]