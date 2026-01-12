import logging
from fastapi import (
    APIRouter,
    Request,
    Response,
    BackgroundTasks,
    )
import json
from typing import Dict
from schemas import *
from user_model import UserModel
from room_model import RoomModel
from utils import generate_token
from rts_service import service
from vertc_service import rtc_service


logger = logging.getLogger(__name__)

callback_router = APIRouter()

@callback_router.post("/rts/callback", response_model=ResponseMessageBase)
async def handle_rts_callback(request: Request, background_tasks: BackgroundTasks):
    # 手动获取请求体
    body = await request.body()
    
    # 手动解析JSON，不管Content-Type头是什么
    request_data = json.loads(body.decode("utf-8"))
    logger.debug(f"收到回调: {json.dumps(request_data, indent=2, ensure_ascii=False)}")

    message = CallbackNotification(**request_data)
    content = json.loads(message.EventData)

    # TODO: 验证签名

    # 根据不同的事件名称处理不同的消息
    handler = EVENT_HANDLERS.get(message.EventType)
    if handler:
        await handler(message, content)
    else:
        logger.warning(f"收到未知事件消息: {message}")
    
    return Response(
        status_code=200,
        content="ok",
    )

# 处理转推流状态变更事件
async def handle_relay_stream_state_changed(message: Dict, content: Dict):
    logger.info(f"收到转推流状态变更事件: {message}")

# 处理用户加入房间事件
async def handle_user_join_room(message: Dict, content: Dict):
    logger.info(f"收到用户加入房间事件: {message}")

# 处理用户离开房间事件
async def handle_user_leave_room(message: Dict, content: Dict):
    logger.info(f"收到用户离开房间事件: {message}")

# 处理程序映射
EVENT_HANDLERS = {
    "RelayStreamStateChanged": handle_relay_stream_state_changed,
    "UserJoinRoom": handle_user_join_room,
    "UserLeaveRoom": handle_user_leave_room,
}
