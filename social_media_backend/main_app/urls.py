from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('get_token/',views.CustomTokenObtainPairView.as_view()),
    path('refresh_token/',TokenRefreshView.as_view()),
    path('register/',views.RegisterUserView.as_view()),
    path('profile_details/',views.profile_avatar_username),
    path('posts/',views.PostListView.as_view()),
    path('posts/recent/',views.RecentPost.as_view()),
    path('posts/followers/',views.FollowersPosts.as_view()),
    path('posts/<int:pk>/',views.PostListView.as_view()),
    path('posts/create/',views.CreatPostView.as_view()),
    path('post_react/<int:post_pk>/<str:react_type>',views.toggle_post_like,name = 'post_react'),
    path('post_comment/',views.CreateCommentView.as_view()),
    path('follow_profile/<int:profile_pk>/',views.following,name='follow_profile'),
    path('notifications/list/',views.UnreadNotificationList.as_view()),
    path('notification/read/<int:pk>',views.MarkNotificationDelivered.as_view())
    ]