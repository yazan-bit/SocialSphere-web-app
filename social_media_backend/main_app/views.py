from django.shortcuts import render


from rest_framework.response import Response
from rest_framework import mixins
from rest_framework.views import APIView
# Create your views here.

class PostListView(APIView):
    def get(self,request):
        return Response({
                'posts':['post1','post2']
            })
