'''
veRTC房间事件回调处理程序
回调设置：https://console.volcengine.com/rtc/cloudRTC?appId=693b6cadaecbdd017582aa25&tab=callback
'''
import logging
from fastapi import (
    APIRouter,
    Request,
    Response,
    )
import json
from typing import Dict
from schemas import *
from meeting_member import MeetingMember
from meeting_room import MeetingRoom
from utils import generate_token
from rts_service import rtsService
from vertc_service import rtc_service
from mysql_client import mysql_client


logger = logging.getLogger(__name__)

callback_router = APIRouter()


@callback_router.post("/rts/callback", response_model=ResponseMessageBase)
async def handle_rts_callback(request: Request):
    # 手动获取请求体
    body = await request.body()
    
    # 手动解析JSON，不管Content-Type头是什么
    request_data = json.loads(body.decode("utf-8"))

    notify_msg = RtsCallback(**request_data)
    event_data = json.loads(notify_msg.EventData)

    # TODO: 验证签名

    # 根据不同的事件名称处理不同的消息
    handler = EVENT_HANDLERS.get(notify_msg.EventType)
    if handler:
        await handler(notify_msg, event_data)
    else:
        logger.warning(f"收到未知事件消息: {notify_msg}")
    
    return Response(
        status_code=200,
        content="ok",
    )


# 处理用户加入房间通知
async def handle_user_join_room(notify_msg: RtsCallback, event_data: Dict):
    #  rts_event = UserJoinRoomEvent(**event_data)
    pass


# 处理用户离开房间通知
async def handle_user_leave_room(notify_msg: RtsCallback, event_data: Dict):
    # rts_event = UserLeaveRoomEvent(**event_data)
    pass


# 处理房间销毁通知
async def handle_room_destroy(notify_msg: RtsCallback, event_data: Dict):
    # rts_event = RoomDestroyEvent(**event_data)
    pass


# 处理程序映射
EVENT_HANDLERS = {
    "UserJoinRoom": handle_user_join_room,
    "UserLeaveRoom": handle_user_leave_room,
    "RoomDestroy": handle_room_destroy,
}
