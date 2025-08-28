import datetime
from typing import Dict, List
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal
from sqlalchemy import text

import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, room_id: str, client_id: str, username:str):
        self.username = username
        async with AsyncSessionLocal() as session:
            self.user_profile = await self.get_user_profile(client_id,session)
            if self.user_profile:
                print(f"user: {self.user_profile}")
                self.room_id = room_id
                await websocket.accept()
            else:
                print("closed")
                await websocket.close()
                return
        
        async with self.lock:
            if room_id not in self.active_connections:
                self.active_connections[room_id] = {}
            self.active_connections[room_id][client_id] = websocket

    async def disconnect(self, room_id: str, client_id: str):
        async with self.lock:
            if room_id in self.active_connections and client_id in self.active_connections[room_id]:
                del self.active_connections[room_id][client_id]
                # Clean up empty rooms
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]

    async def broadcast(self, message: str, room_id: str):
        async with self.lock:
            if room_id in self.active_connections:
                for _, websocket in self.active_connections[room_id].items():
                    await websocket.send_text(message)


    async def get_user_profile(self, user_id: str , db:AsyncSession):
        print(user_id)
        async with self.lock:
            try:
                query = f'select * from users_profile where user_id = {user_id}'
                user_profile = await db.execute(text(query))
                return user_profile.scalar_one_or_none()
            except Exception as e:
                print(e)


    async def create_message(self, room_id: str, message:str, sender_id:str):
        print(type(message))
        async with self.lock:
            try:
                async with AsyncSessionLocal() as session:
                    query = f"insert into chat_app_chatmessage(message,sender_id,room_id) values('{message}',{sender_id},{room_id})"
                    await session.execute(text(query))
                    await session.commit()
                    print(self.username)
                    return {
                        'sender_id':sender_id,
                        'message':message,
                        'timestamp':str(datetime.datetime.utcnow())
                    }
            except Exception as e:
                print(e)
                return None
    
    