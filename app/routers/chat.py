# app/routers/chat.py (完整替换)

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app import database, crud
from app.auth import security
from app.dependencies import get_current_user # 导入我们统一的依赖

router = APIRouter(prefix="/chat", tags=["Chat"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

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

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...), 
    db: Session = Depends(database.get_db)
):
    try:
        email = security.verify_token(token, credentials_exception=WebSocketDisconnect())
        user = crud.get_user_by_email(db, email=email)
        if not user: raise WebSocketDisconnect()
    except:
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
                # 1. 实时转发消息 (和以前一样)
                await manager.send_personal_message(content, recipient_id, user.id)
                # 2. 【【【核心升级】】】将消息存入数据库
                crud.create_chat_message(db, sender_id=user.id, recipient_id=recipient_id, content=content)
    
    except WebSocketDisconnect:
        manager.disconnect(user.id)

# --- (新) Pydantic 模型，用于返回聊天记录 ---
class ChatMessageOut(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

# --- (新) 获取历史记录的 HTTP 接口 ---
@router.get("/history/{target_user_id}", response_model=List[ChatMessageOut])
def get_user_chat_history(
    target_user_id: int,
    db: Session = Depends(database.get_db),
    current_user: database.User = Depends(get_current_user)
):
    """获取当前登录用户与目标用户之间的聊天历史记录"""
    if not crud.get_user_by_email(db, email=current_user.email): # 确保用户有效
        raise HTTPException(status_code=401, detail="Invalid user")
    
    return crud.get_chat_history(db, current_user.id, target_user_id)