from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

@database_sync_to_async
def get_user(validated_token):
    try:
        user = User.objects.get(id=validated_token["user_id"])
        return user
    except User.DoesNotExist:
        return AnonymousUser()

class JwtAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Extract the token from the query string
        query_string = scope.get("query_string", b"").decode()
        token_param = [param.split("=") for param in query_string.split("&")]
        token = None
        
        for param in token_param:
            if len(param) == 2 and param[0] == "token":
                token = param[1]
                break
        
        # Try to authenticate the user
        if token:
            try:
                UntypedToken(token)
            except (InvalidToken, TokenError) as e:
                scope["user"] = AnonymousUser()
            else:
                decoded_data = UntypedToken(token).payload
                scope["user"] = await get_user(validated_token=decoded_data)
        else:
            scope["user"] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)