from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from typing import List, Optional
from models.message import Message
from services.message_store import MessageStore
from datetime import datetime, timedelta
from utils.num_generator import generate_message_id
import base64
import traceback
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
message_store = MessageStore()

class TokenRequest(BaseModel):
    token: str = ''

@router.post("/create", response_model=dict)
async def create_message(
    message: str = Form(""),
    images: List[UploadFile] = File(default=[]),
    expiry: int = Form(...),
    burn_time: str = Form(...),
    token: Optional[str] = Form(None),
    token_hint: Optional[str] = Form(None)
):
    try:
        # Validate images
        if images:
            if len(images) > 1:
                raise HTTPException(status_code=400, detail="Maximum 1 image allowed")
            
            for img in images:
                if not img.content_type.startswith('image/'):
                    raise HTTPException(status_code=400, detail=f"File type {img.content_type} not allowed")
                
                content = await img.read()
                if len(content) > 3 * 1024 * 1024:  # 3MB
                    raise HTTPException(status_code=400, detail="Image size exceeds 3MB limit")
                await img.seek(0)

        # Generate message ID with collision checking
        message_id = generate_message_id(
            exists_check=lambda id: id in message_store.messages
        )
        
        # Process images
        image_data = []
        if images:
            for img in images:
                content = await img.read()
                image_data.append({
                    'content': base64.b64encode(content).decode('utf-8'),
                    'type': img.content_type
                })

        # Create message object using our Message model
        message_obj = Message(
            id=message_id,
            text=message,
            images=image_data,
            burn_time=burn_time,
            expires_at=datetime.now() + timedelta(minutes=expiry),
            token=token.strip() if token else "",
            token_hint=token_hint.strip() if token_hint else None
        )

        # Store message
        await message_store.store_message(message_obj)

        # Return response
        return message_obj.to_response()

    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        raise

@router.post("/{message_id}")
async def get_message(message_id: str, request: TokenRequest, client: Request):
    try:
        # Check rate limiting first
        check_result = await message_store.check_token_attempts(message_id, client.client.host)
        if not check_result["allowed"]:
            raise HTTPException(
                status_code=429, 
                detail={
                    "message": "Too many failed attempts",
                    "wait_time": check_result["wait_time"]
                }
            )
        
        # First check if message exists
        message = await message_store.check_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
            
        # Then try to get with token
        message = await message_store.get_message(message_id, request.token)
        if not message:
            await message_store.record_failed_attempt(message_id, client.client.host)
            raise HTTPException(status_code=401, detail="Invalid token")
        
        response_data = message.to_content()
        await message_store.delete_message(message_id)
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving message: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")

@router.post("/{message_id}/meta")
async def get_message_meta(message_id: str, request: TokenRequest):
    try:
        message = await message_store.get_message(message_id, request.token)
        if not message:
            raise HTTPException(
                status_code=404, 
                detail="Message not found or invalid token"
            )
        return message.to_response()

    except Exception as e:
        print(f"Error getting message metadata: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to get message metadata"}
        )

@router.get("/{message_id}/check")
async def check_message(message_id: str):
    """Check if message exists and if it needs a token"""
    try:
        # Just check if message exists and get token info
        message_info = await message_store.check_message(message_id)
        if not message_info:
            raise HTTPException(status_code=404, detail="Message not found")
            
        return {
            "needs_token": message_info.get("needs_token", False),
            "token_hint": message_info.get("token_hint")
        }
    except HTTPException as he:
        # Re-raise HTTP exceptions (like 404)
        raise he
    except Exception as e:
        print(f"Error checking message {message_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="Message not found")
