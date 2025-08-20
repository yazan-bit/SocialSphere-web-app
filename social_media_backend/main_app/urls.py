from django.urls import path
from . import views

urlpatterns = [
    path('list_posts',views.PostListView.as_view())
]