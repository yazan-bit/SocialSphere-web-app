"""
ASGI config for social_media_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter,URLRouter
from channels.auth import AuthMiddlewareStack
from .jwt_authentication import JwtAuthMiddleware
from .routing import websocket_urlpatterns

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'social_media_backend.settings')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webChannels.settings')

application = ProtocolTypeRouter({
    'http':get_asgi_application(),
    'websocket':JwtAuthMiddleware(
        URLRouter(
            websocket_urlpatterns
        )
    )
})
