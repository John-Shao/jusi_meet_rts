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

# 处理用户加入房间事件
async def handle_user_join_room(notify_msg: RtsCallback, event_data: Dict):
    rts_event = UserJoinRoomEvent(**event_data)

    # 从数据库查询用户名
    if len(rts_event.UserId) == 32:
        user_name = await mysql_client.get_user_name(rts_event.UserId)
    else:
        user_name = rts_event.UserId

    user_model = UserModel(
        user_id=rts_event.UserId,
        user_name=user_name,
        camera=DeviceState.OPEN,
        mic=DeviceState.OPEN,
        is_silence=SilenceState.NOT_SILENT,
    )
    user = MeetingMember(user_model)

    # 将用户加入房间
    result = await rtsService.check_user_in_room(
        room_id=rts_event.RoomId,
        user_id=rts_event.UserId,
    )

    if result == -1:
        # 房间不存在，不处理
        return
    elif result == 0:
        # 用户不在房间中，加入房间
        room: MeetingRoom = await rtsService.join_room(user, rts_event.RoomId)
    else:
        # 用户已在房间中，仍可能需要发送通知
        room: MeetingRoom = await rtsService.get_room(rts_event.RoomId)

    if room.user_count == 1:
        return  # 如果是第一个用户加入房间，则不需要广播通知

    # 广播通知房间内的用户
    event = InformVcOnJoinRoom(
        user=user.to_dict(),
        user_count=room.user_count,
    )

    inform = RtsInform(
        event="vcOnJoinRoom",
        data=event.model_dump(),
    )

    body = BroadcastMessageBase(
        AppId=notify_msg.AppId,
        RoomId=rts_event.RoomId,
        Message=inform.model_dump_json(),
    )

    logger.debug(f"准备发送广播消息: {json.dumps(body.model_dump(), indent=2, ensure_ascii=False)}")

    response = rtc_service.send_broadcast(body.model_dump_json())

    # 检查API调用是否成功
    if "ResponseMetadata" in response and "Error" in response.get("ResponseMetadata", {}):
        error = response["ResponseMetadata"]["Error"]
        logger.error(f"发送广播消息失败: {error.get('Code')} - {error.get('Message')}")
    else:
        logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 处理用户离开房间事件
async def handle_user_leave_room(notify_msg: RtsCallback, event_data: Dict):
    rts_event = UserLeaveRoomEvent(**event_data)
    # 从数据库查询用户名
    if len(rts_event.UserId) == 32:
        user_name = await mysql_client.get_user_name(rts_event.UserId)
    else:
        user_name = rts_event.UserId

    user_model = UserModel(
        user_id=rts_event.UserId,
        user_name=user_name,
        camera=DeviceState.OPEN,
        mic=DeviceState.OPEN,
        is_silence=SilenceState.NOT_SILENT,
    )
    user = MeetingMember(user_model)

    room: MeetingRoom = await rtsService.get_room(rts_event.RoomId)
    if not room:
        return  # 房间不存在，不处理

    # 将用户移出房间
    await rtsService.leave_room(rts_event.UserId, rts_event.RoomId)

    if room.user_count == 0:
        rtsService.remove_room(rts_event.RoomId)
        return  # 如果房间内没有用户了，则不需要广播通知

    # 广播通知房间内的用户
    event = InformVcOnLeaveRoom(
        user=user.to_dict(),
        user_count=room.user_count,
    )

    inform = RtsInform(
        event="vcOnLeaveRoom",
        data=event.model_dump(),
    )

    body = BroadcastMessageBase(
        AppId=notify_msg.AppId,
        RoomId=rts_event.RoomId,
        Message=inform.model_dump_json(),
    )

    logger.debug(f"准备发送广播消息: {json.dumps(body.model_dump(), indent=2, ensure_ascii=False)}")

    response = rtc_service.send_broadcast(body.model_dump_json())

    # 检查API调用是否成功
    if "ResponseMetadata" in response and "Error" in response.get("ResponseMetadata", {}):
        error = response["ResponseMetadata"]["Error"]
        logger.error(f"发送广播消息失败: {error.get('Code')} - {error.get('Message')}")
    else:
        logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")


# 处理程序映射
EVENT_HANDLERS = {
    "UserJoinRoom": handle_user_join_room,
    "UserLeaveRoom": handle_user_leave_room,
}
