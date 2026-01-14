from email import message
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
    '''
    if not ujr_event.UserId.startswith("jusi_"):
        return  # 非jusi设备，不处理
    '''    
    user = UserModel(
        user_id=rts_event.UserId,
        device_id=rts_event.UserId[5:] if rts_event.UserId.startswith("jusi_") else rts_event.UserId,
        user_name=rts_event.UserId,
        camera=DeviceState.OPEN,
        mic=DeviceState.OPEN,
        is_silence=SilenceState.NOT_SILENT,
    )

    # 将用户加入房间
    room: RoomModel = await service.join_room(notify_msg.AppId, user, rts_event.RoomId)
    if room.user_count == 1:
        return  # 如果是第一个用户加入房间，则不需要广播通知

    # 广播通知房间内的用户
    event = InformVcOnJoinRoom(
        user=user.model.model_dump(),
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

    try:
        response = rtc_service.send_broadcast(body.model_dump_json())
        logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"发送广播消息失败: {e}")

# 处理用户离开房间事件
async def handle_user_leave_room(notify_msg: RtsCallback, event_data: Dict):
    rts_event = UserLeaveRoomEvent(**event_data)
    '''
    if not ujr_event.UserId.startswith("jusi_"):
        return  # 非jusi设备，不处理
    '''    
    user = UserModel(
        user_id=rts_event.UserId,
        device_id=rts_event.UserId[5:] if rts_event.UserId.startswith("jusi_") else rts_event.UserId,
        user_name=rts_event.UserId,
        camera=DeviceState.OPEN,
        mic=DeviceState.OPEN,
        is_silence=SilenceState.NOT_SILENT,
    )

    room: RoomModel = await service.get_room(rts_event.RoomId)
    if not room:
        return  # 房间不存在，不处理

    # 将用户移出房间
    await service.leave_room(rts_event.UserId, rts_event.RoomId)

    if room.user_count == 0:
        return  # 如果房间内没有用户了，则不需要广播通知

    # 广播通知房间内的用户
    event = InformVcOnLeaveRoom(
        user=user.model.model_dump(),
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

    try:
        response = rtc_service.send_broadcast(body.model_dump_json())
        logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"发送广播消息失败: {e}")


# 处理程序映射
EVENT_HANDLERS = {
    "UserJoinRoom": handle_user_join_room,
    "UserLeaveRoom": handle_user_leave_room,
}
