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
from rts_service import rtsService
from config import settings
from vertc_client import ban_room
from drift_api import drift_leave_room
from rts_inform import (
    join_room_infom,
    leave_room_infom,
    finish_room_infom,
    )


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
    rts_event = UserJoinRoomEvent(**event_data)
    if len(rts_event.UserId) == HUMAN_USER_ID_LENGTH:
        return  # 只有设备需要借助回调方式加入会议
    
    result = await rtsService.check_user_in_room(
        room_id=rts_event.RoomId,
        user_id=rts_event.UserId,
    )

    if result == -1 or result == 1:
        # 房间不存在，或用户已在房间中，不处理
        return
    
    user_model = UserModel(
        user_id=rts_event.UserId,
        user_name=rts_event.UserId,
        camera=DeviceState.OPEN,
        mic=DeviceState.OPEN,
        is_silence=SilenceState.NOT_SILENT,
    )
    user = MeetingMember(user_model)

    # 将设备加入房间中
    room: MeetingRoom = await rtsService.join_room(user, rts_event.RoomId)

    # 发送设备加入房间通知
    await join_room_infom(settings.rtc_app_id, room, user)


# 处理用户离开房间通知
async def handle_user_leave_room(notify_msg: RtsCallback, event_data: Dict):
    rts_event = UserLeaveRoomEvent(**event_data)
    if len(rts_event.UserId) == HUMAN_USER_ID_LENGTH:
        return  # 只有设备需要借助回调方式退出会议
    
    # 将设备移出房间
    await rtsService.leave_room(rts_event.UserId, rts_event.RoomId)
    # 如果设备是最后一个离开会议，房间已被销毁
    room: MeetingRoom = await rtsService.get_room(rts_event.RoomId)
    if room:
        # 发送设备离开房间通知
        await leave_room_infom(settings.rtc_app_id, room, rts_event.UserId)
    else:
        # 发送房间销毁通知
        await finish_room_infom(settings.rtc_app_id, rts_event.RoomId)
        logger.debug(f"解散房间：{rts_event.RoomId}")
        await ban_room(rts_event.RoomId)
        # 相机离开房间后，停止转推和它相关的媒体流
        await drift_leave_room(
            DriftLeaveRequest(
            room_id=rts_event.RoomId,
            device_sn=rts_event.UserId,
            )
        )


# 处理程序映射
EVENT_HANDLERS = {
    "UserJoinRoom": handle_user_join_room,
    "UserLeaveRoom": handle_user_leave_room,
}
