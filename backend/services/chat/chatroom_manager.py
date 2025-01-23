from models.chat.chatroom import PrivateRoom
from utils.num_generator import generate_id
from datetime import datetime, UTC
from typing import Dict, Optional
import secrets
import string
from models.chat.message import Message, MessageType
from sys import getsizeof
from models.chat.user import User
from fastapi import HTTPException
from utils.chat_error_codes import ChatErrorCodes, STATUS_CODES

class RoomError(Exception):
    """Base exception for room operations"""
    pass

class RoomNotFoundError(RoomError):
    """Room does not exist"""
    pass

class RoomFullError(RoomError):
    """Room has reached capacity"""
    pass

class RoomExpiredError(RoomError):
    """Room has expired"""
    pass

class MemoryLimitError(RoomError):
    """Memory limit reached"""
    pass

class ChatroomManager:
    def __init__(self):
        self._rooms: Dict[str, PrivateRoom] = {}
        self._id_chars = string.ascii_letters + string.digits
        self._max_collision_attempts = 3
        self._max_rooms = 10000
        self._min_room_id_length = 1
        self._max_room_id_length = 70
        self._max_message_chars = 2000

    async def create_private_room(self, room_id: Optional[str] = None, room_token: Optional[str] = None, room_token_hint: Optional[str] = None) -> PrivateRoom:
        """Create a private chat room with optional custom ID"""
        if len(self._rooms) >= self._max_rooms:
            raise MemoryLimitError("Maximum room limit reached")
            
        # Create room with validation handled by PrivateRoom class
        room = PrivateRoom(
            room_id=room_id or generate_id(length=16, exists_check=lambda id: id in self._rooms),
            room_token=room_token,
            room_token_hint=room_token_hint
        )
        
        self._rooms[room.room_id] = room
        return room

    def validate_room_token(self, room_id: str, token: str) -> bool:
        """Validate room token"""
        room = self.get_private_room(room_id)
        if not room:
            return False
        return room.room_token == token

    def generate_private_room_token(self, room_id: str, expiry_minutes: int = 60) -> str:
        """Generate a one-time token for room access"""
        room = self.get_private_room(room_id)
        if not room:
            raise ValueError("Room not found")
            
        token = secrets.token_urlsafe(8)
        room.room_tokens.append(token)
        
        return token

    def validate_private_room_token(self, room_id: str, token: str) -> bool:
        """Validate a room token"""
        room = self.get_private_room(room_id)
        if not room or not room.room_token:
            return False
        return room.room_token == token

    async def add_private_room_participant(self, room_id: str, user: User) -> bool:
        """Add a participant to a room"""
        room = await self.get_private_room(room_id)
        if not room:
            return False
            
        if len(room.participants) >= 2:
            return False
            
        # Store user by their ID instead of username
        room.participants[user.user_id] = {
            'username': user.username,
            'connection_id': user.connection_id
        }
        room.last_activity = datetime.now(UTC)
        return True

    def remove_private_room_participant(self, room_id: str, username: str) -> bool:
        """Remove a participant from a room"""
        room = self.get_private_room(room_id)
        if not room or username not in room.participants:
            return False
            
        del room.participants[username]
        room.last_activity = datetime.now(UTC)
        return True

    def update_private_room_activity(self, room_id: str) -> None:
        """Update room's last activity timestamp"""
        room = self.get_private_room(room_id)
        if room:
            room.last_activity = datetime.now(UTC)

    async def get_private_room(self, room_id: str) -> PrivateRoom:
        """Get room by ID with error handling"""
        room = self._rooms.get(room_id)
        if not room:
            raise RoomNotFoundError(f"Room {room_id} not found")
        if room.is_expired():
            raise RoomExpiredError(f"Room {room_id} has expired")
        return room

    def delete_private_room(self, room_id: str) -> bool:
        """Delete a room"""
        if room_id in self._rooms:
            del self._rooms[room_id]
            return True
        return False

    def cleanup_inactive_rooms(self) -> None:
        """Remove expired rooms from memory"""
        current_time = datetime.now(UTC)
        expired_rooms = [
            room_id for room_id, room in self._rooms.items()
            if room.is_expired()
        ]
        
        for room_id in expired_rooms:
            del self._rooms[room_id]

    def get_memory_stats(self) -> dict:
        """Get current memory usage statistics"""
        return {
            "total_rooms": len(self._rooms),
            "active_rooms": sum(1 for r in self._rooms.values() if not r.is_expired()),
            "total_participants": sum(len(r.participants) for r in self._rooms.values()),
            "total_messages": sum(len(r.messages) for r in self._rooms.values())
        }

    def enforce_room_limits(self, room: PrivateRoom) -> None:
        """Enforce memory limits for a room"""
        # Remove oldest messages if limit exceeded
        if len(room.messages) > self._max_messages_per_room:
            room.messages = room.messages[-self._max_messages_per_room:]

    def add_message_to_room(self, room_id: str, message: Message) -> None:
        """Add message with size checks"""
        room = self.get_private_room(room_id)
        
        # Check message count
        if len(room.messages) >= self._max_messages_per_room:
            raise MemoryLimitError("Maximum message count reached")
            
        # Check message size based on type
        if message.type == MessageType.text.value:
            if len(message.content.encode('utf-8')) > (self._max_message_chars * 4):  # 4 bytes per char worst case
                raise MemoryLimitError("Text message too long")
        elif message.type == MessageType.image.value:
            if len(message.content) > self._max_image_size_bytes:
                raise MemoryLimitError("Image size exceeds limit")
        
        room.messages.append(message)

    async def get_room(self, room_id: str) -> Optional[PrivateRoom]:
        """Get a room by its ID"""
        room = self._rooms.get(room_id)
        if not room:
            raise HTTPException(
                status_code=STATUS_CODES[ChatErrorCodes.ROOM_NOT_FOUND],
                detail={"code": ChatErrorCodes.ROOM_NOT_FOUND.value}
            )
        return room
