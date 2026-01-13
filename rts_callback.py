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

    notify_msg = CallbackNotification(**request_data)
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
async def handle_user_join_room(notify_msg: CallbackNotification, event_data: Dict):
    ujr_event = UserJoinRoomEvent(**event_data)

    message = RequestMessageBase(
        request_id=notify_msg.EventId,
        app_id=notify_msg.AppId,
        room_id=ujr_event.RoomId,
        user_id=ujr_event.UserId,
        event_name="vcJoinRoom",
        device_id=ujr_event.UserId[5:],  # 去掉前缀 "jusi_"
        login_token="",
    )

    content = {
        "user_name": ujr_event.UserId,
        "camera": DeviceState.OPEN,
        "mic": DeviceState.OPEN,
        "is_silence": SilenceState.NOT_SILENT,
    }

    user_name = content.get("user_name")
    camera = DeviceState(content.get("camera", DeviceState.CLOSED))
    mic = DeviceState(content.get("mic", DeviceState.CLOSED))
    is_silence = SilenceState(content.get("is_silence", SilenceState.NOT_SILENT))
    
    user = UserModel(
        user_id=message.user_id,
        device_id=message.device_id,
        user_name=user_name,
        camera=camera,
        mic=mic,
        is_silence=is_silence,
    )

    room: RoomModel = await service.join_room(message.app_id, user, message.room_id)

    wb_room_id = f"whiteboard_{message.room_id}"
    wb_user_id = f"whiteboard_{message.user_id}"
    
    response = JoinMeetingRoomRes(
        room = room.model,
        user= user.model,
        user_list = room.get_user_list(),
        token = generate_token(user._user.user_id, message.room_id),
        wb_room_id = wb_room_id,
        wb_user_id = wb_user_id,
        wb_token = generate_token(wb_user_id, wb_room_id),
    )

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=response,
    )

    body = BroadcastMessageBase(
        AppId=message.app_id,
        RoomId=message.room_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_broadcast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 处理用户离开房间事件
async def handle_user_leave_room(notify_msg: CallbackNotification, event_data: Dict):
    ulr_event = UserLeaveRoomEvent(**event_data)

    message = RequestMessageBase(
        request_id=notify_msg.EventId,
        app_id=notify_msg.AppId,
        room_id=ulr_event.RoomId,
        user_id=ulr_event.UserId,
        event_name="vcLeaveRoom",
        device_id=ulr_event.UserId[5:],  # 去掉前缀 "jusi_"
        login_token="",
    )

    await service.leave_room(message.user_id, message.room_id)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = BroadcastMessageBase(
        AppId=message.app_id,
        RoomId=message.room_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_broadcast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")


# 处理程序映射
EVENT_HANDLERS = {
    "UserJoinRoom": handle_user_join_room,
    "UserLeaveRoom": handle_user_leave_room,
}
