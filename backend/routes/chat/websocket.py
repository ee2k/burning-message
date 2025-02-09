from fastapi import WebSocket, WebSocketDisconnect
import logging
from models.chat.message import Message, ImageMessage
from fastapi import APIRouter
from services.chat.chatroom_manager import ChatroomManager
from utils.singleton import singleton
import json
import uuid
import time
import asyncio
from utils.chat_error_codes import ChatErrorCodes
from models.chat.user import User, ParticipantStatus
from pydantic import ValidationError
from models.chat.chatroom import PrivateRoom
from datetime import datetime, UTC

router = APIRouter()

logger = logging.getLogger(__name__)

chatroom_manager = ChatroomManager()

@singleton
class WebSocketManager:
    def __init__(self):
        # Removed local rooms variable; using chatroom_manager.rooms instead.
        # self.rooms: dict[str, PrivateRoom] = {}  # room_id -> PrivateRoom
        pass

    async def connect(self, websocket: WebSocket, room_id: str, user: User):
        # Set user's WebSocket connection and mark active
        user.set_websocket(websocket)
        user.update_status(ParticipantStatus.ACTIVE)

        room = await chatroom_manager.get_room(room_id)
        
        # Check if this user is already present in the room
        existing = next((p for p in room.participants if p.user_id == user.user_id), None)
        if existing:
            # Update the existing participant's connection rather than adding a duplicate
            existing.set_websocket(websocket)
            existing.update_status(ParticipantStatus.ACTIVE)
        else:
            # Add the new participant for first-time join
            room.add_participant(user)

    async def disconnect(self, user: User, room_id: str):
        if user.is_connected():
            user.clear_websocket()
            user.update_status(ParticipantStatus.OFFLINE)
        
        # Use the rooms stored in chatroom_manager instead of self.rooms.
        room = await chatroom_manager.get_room(room_id)
        if room:
            room.remove_participant(user.user_id)

    async def send_message(self, room_id: str, message: Message):
        room = await chatroom_manager.get_room(room_id)
        if not room:
            return

        # Store message in room history
        try:
            await chatroom_manager.add_message_to_room(room_id, message)
        except Exception as e:
            logger.error(f"Failed to add message to room: {str(e)}")
            return

        # Delivery logic
        first_attempt_failed = False
        delivered_count = 0
        total_recipients = len(room.participants) - 1  # Exclude sender
        
        # First delivery attempt
        for participant in room.participants:
            if participant.is_connected() and participant.user_id != message.sender_id:
                try:
                    await participant.websocket.send_text(message.model_dump_json())
                    message.mark_delivered(participant.user_id)
                    delivered_count += 1
                except Exception as e:
                    first_attempt_failed = True

        # Image-specific cleanup scheduling
        if isinstance(message, ImageMessage):
            asyncio.create_task(
                self.monitor_image_cleanup(room, message)
            )

        # Ack handling
        sender = next((p for p in room.participants if p.user_id == message.sender_id), None)
        if sender and sender.is_connected():
            if delivered_count == total_recipients:
                await self.send_full_ack(sender, message)
            else:
                if first_attempt_failed:
                    await self.send_partial_ack(sender, message)
                asyncio.create_task(
                    self.retry_failed_deliveries(room, message, max_retries=3)
                )

    async def retry_failed_deliveries(self, room: PrivateRoom, message: Message, max_retries: int):
        retry_count = 0
        total_recipients = len(room.participants) - 1
        
        while retry_count < max_retries:
            retry_count += 1
            await asyncio.sleep(2 ** retry_count)  # Exponential backoff
            
            # Get current undelivered participants
            undelivered = [p for p in room.participants 
                          if p.user_id != message.sender_id
                          and p.user_id not in message.delivered_to]
            
            # Retry delivery
            for participant in undelivered:
                if participant.is_connected():
                    await participant.websocket.send_text(message.model_dump_json())
                    message.mark_delivered(participant.user_id)

            # Check if fully delivered
            if len(message.delivered_to) == total_recipients:
                sender = next((p for p in room.participants if p.user_id == message.sender_id), None)
                if sender and sender.is_connected():
                    await self.send_full_ack(sender, message)
                    await self.cleanup_message(room, message)
                return
                
        # Max retries reached - delete message
        await self.cleanup_message(room, message)

    async def send_full_ack(self, sender: User, message: Message):
        await sender.websocket.send_json({
            "message_type": "ack",
            "message_id": message.message_id,
            "status": "delivered"
        })

    async def send_partial_ack(self, sender: User, message: Message):
        await sender.websocket.send_json({
            "message_type": "ack",
            "message_id": message.message_id,
            "status": "partial"
        })

    async def cleanup_message(self, room: PrivateRoom, message: Message):
        if message in room.messages:
            room.messages.remove(message)

    async def monitor_image_cleanup(self, room: PrivateRoom, message: ImageMessage):
        """Check image message status periodically"""
        while True:
            # Check expiration
            if datetime.now(UTC) > message.expires_at:
                await self.cleanup_message(room, message)
                return
            
            # Check if all required recipients loaded the image
            required = message.required_recipients
            loaded = message.loaded_recipients
            if loaded and required.issubset(loaded):
                await self.cleanup_message(room, message)
                return
            
            await asyncio.sleep(30)  # Check every 30 seconds

    async def check_connections(self):
        """Periodically check connection health and remove expired rooms"""
        while True:
            current_time = time.time()
            # Iterate over a list of room IDs to avoid modifying the dictionary during iteration.
            room_ids = list(chatroom_manager.rooms.keys())
            for room_id in room_ids:
                # Retrieve the room via get_room, which cleans up expired rooms.
                room = await chatroom_manager.get_room(room_id)
                if not room:
                    continue
                for participant in room.participants:
                    if participant.is_connected():
                        # Check for inactivity (e.g., via last_active timestamp)
                        if current_time - participant.last_active.timestamp() > 60:
                            await self.disconnect(participant, room.room_id)
            await asyncio.sleep(30)  # Check every 30 seconds

    async def broadcast_failed_join(self, room_id: str, username: str):
        """Broadcast failed join attempt to room participants"""
        system_message = {
            "message_type": "system",
            "username": username,
            "code": ChatErrorCodes.FAILED_JOIN_ATTEMPT,
            "timestamp": time.time()
        }
        
        # Send to all participants in the room
        if room_id in chatroom_manager.rooms:
            room = chatroom_manager.rooms[room_id]
            for participant in room.participants:
                if participant.is_connected():
                    await participant.websocket.send_json(system_message)

    async def send_participant_list(self, room_id: str):
        room = await chatroom_manager.get_room(room_id)
        if room:
            participants = [{"user_id": p.user_id, "username": p.username} for p in room.participants]
            await self.broadcast(room_id, {
                "message_type": "participant_list",
                "participants": participants
            })

    async def broadcast(self, room_id: str, message: dict):
        room = await chatroom_manager.get_room(room_id)
        if room:
            for participant in room.participants:
                if participant.is_connected():
                    await participant.websocket.send_json(message)

    async def handle_disconnect(self, room_id: str, user_id: str, username: str):
        # Implementation of handle_disconnect method
        pass

websocket_manager = WebSocketManager()

@router.websocket("/chatroom/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    user = None
    try:
        await websocket.accept()
        
        # Get all params from query string
        username = websocket.query_params.get("username")
        room_token = websocket.query_params.get("room_token")
        claimed_user_id = websocket.query_params.get("user_id")

        # Immediate validation
        if not username:
            await websocket.close(code=4001, reason="Username required")
            return

        # Room existence check
        room = await chatroom_manager.get_room(room_id)
        if not room:
            await websocket.close(code=4004, reason="Room not found")
            return

        # room_token validation for private rooms
        if room.requires_token():
            if not room_token or not await chatroom_manager.validate_room_token(room_id, room_token):
                await websocket.close(code=4003, reason="Invalid room_token")
                return

        # User ID handling
        user_id = claimed_user_id if await chatroom_manager.validate_reconnection(
            room_id, claimed_user_id, username
        ) else str(uuid.uuid4())

        # Create user object
        user = User(user_id=user_id, username=username)
        await websocket_manager.connect(websocket, room_id, user)
        
        # Notify client and participants
        await websocket.send_json({
            "message_type": "connection_info",
            "user_id": user_id,
            "participants": [
                {"user_id": p.user_id, "username": p.username}
                for p in room.participants
            ]
        })
        
        # Broadcast join notification
        await websocket_manager.broadcast(room_id, {
            "message_type": "participant_joined",
            "user_id": user.user_id,
            "username": user.username
        })

        # Main message loop
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Check for ping messages using the proper key
                if message.get("message_type") == "ping":
                    await websocket.send_json({"message_type": "pong"})
                    continue
                elif message.get("message_type") == "get_participants":
                    await websocket_manager.send_participant_list(room_id)
                    continue
                else:
                    try:
                        # Now validate and process messages that are not ping messages
                        validated = Message.model_validate(message)
                        if validated.message_type == "chat":
                            if validated.sender_id != user_id:
                                continue
                            # Add message to room
                            try:
                                chatroom_manager.add_message_to_room(room_id, validated)
                            except Exception as e:
                                logger.error(f"Failed to add message to room: {str(e)}")
                                continue
                            await websocket_manager.send_message(room_id, validated)
                        elif validated.message_type == "system":
                            await websocket_manager.broadcast_system_message(
                                room_id, validated.content
                            )
                    except ValidationError as e:
                        logger.error(f"Invalid message: {str(e)}")

            except json.JSONDecodeError:
                logger.error("Invalid JSON message")
            except ValidationError as e:
                logger.error(f"Invalid message format: {str(e)}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {user_id}")
    finally:
        if user:
            # Cleanup and notifications
            await websocket_manager.disconnect(user, room_id)
            await websocket_manager.broadcast(room_id, {
                "message_type": "participant_left",
                "user_id": user.user_id,
                "username": user.username
            })
            await websocket_manager.send_participant_list(room_id)

def get_websocket_manager() -> WebSocketManager:
    """Dependency to get WebSocketManager instance"""
    return websocket_manager

def get_chatroom_manager() -> ChatroomManager:
    """Dependency to get WebSocketManager instance"""
    return chatroom_manager
