# app/routers/chat.py (完整修复版)

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app import database, crud
from app.auth import security
from app.dependencies import get_current_user # 导入我们统一的依赖

# 【【【 核心修改 1: 移除 prefix 】】】
router = APIRouter(tags=["Chat"])

class ConnectionManager:
    def __init__(self):
        # The type hint Dict[int, WebSocket] was removed in your original file,
        # but it's good practice to keep it. I'll add it back.
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"用户 {user_id} 已连接到聊天服务器。")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"用户 {user_id} 已断开连接。")

    async def send_personal_message(self, message: str, recipient_id: int, sender_id: int):
        if recipient_id in self.active_connections:
            websocket = self.active_connections[recipient_id]
            payload = {"sender_id": sender_id, "content": message}
            await websocket.send_text(json.dumps(payload))
            print(f"实时消息已发送给用户 {recipient_id}")
            return True
        print(f"发送失败：用户 {recipient_id} 不在线。")
        return False

manager = ConnectionManager()

# 【【【 核心修改 2: 使用完整路径 /chat/ws 】】】
@router.websocket("/chat/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...), 
    db: Session = Depends(database.get_db)
):
    try:
        email = security.verify_token(token, credentials_exception=WebSocketDisconnect())
        user = crud.get_user_by_email(db, email=email)
        if not user: raise WebSocketDisconnect()
    except Exception:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user.id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            recipient_id = message_data.get("recipient_id")
            content = message_data.get("content")

            if recipient_id and content:
                await manager.send_personal_message(content, recipient_id, user.id)
                crud.create_chat_message(db, sender_id=user.id, recipient_id=recipient_id, content=content)
    
    except WebSocketDisconnect:
        manager.disconnect(user.id)

# --- Pydantic 模型，用于返回聊天记录 ---
class ChatMessageOut(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True # Replaces orm_mode = True in Pydantic v2

# 【【【 核心修改 3: 使用完整路径 /chat/history/{target_user_id} 】】】
@router.get("/chat/history/{target_user_id}", response_model=List[ChatMessageOut])
def get_user_chat_history(
    target_user_id: int,
    db: Session = Depends(database.get_db),
    current_user: database.User = Depends(get_current_user)
):
    """获取当前登录用户与目标用户之间的聊天历史记录"""
    # Verifying current_user exists is already handled by get_current_user dependency.
    # This check is redundant but harmless.
    if not crud.get_user_by_email(db, email=current_user.email):
        raise HTTPException(status_code=401, detail="Invalid user")
    
    return crud.get_chat_history(db, current_user.id, target_user_id)