import logging
import json
from schemas import *
from vertc_service import rtc_service
from mysql_client import mysql_client
from rts_service import rtsService
from meeting_room import MeetingRoom
from meeting_member import MeetingMember


logger = logging.getLogger(__name__)


# 结束会议通知
async def finish_room_infom(app_id: str, room_id: str):
    # 通知房间内的用户
    event = InformVcOnRoomDestroy()

    inform = RtsInform(
        event="vcOnFinishRoom",
        data=event.model_dump(),
    )
    
    body = BroadcastMessageBase(
        AppId=app_id,
        RoomId=room_id,
        Message=inform.model_dump_json(),
    )
    logger.debug(f"发送房间外广播消息: {json.dumps(body.model_dump(), indent=2, ensure_ascii=False)}")
    response = await rtc_service.send_broadcast(body.model_dump_json())
    logger.debug(f"房间外广播消息发送结果: {json.dumps(response, indent=2, ensure_ascii=False)}")


# 用户加入房间通知
async def join_room_infom(app_id: str, room: MeetingRoom, user: MeetingMember):

    # 从数据库查询用户名
    if len(user.id) == HUMAN_USER_ID_LENGTH:
        user_name = await mysql_client.get_user_name(user.id)
    else:
        user_name = user.id
    
    user_model = UserModel(
        user_id=user.id,
        user_name=user_name,
        camera=DeviceState.OPEN,
        mic=DeviceState.OPEN,
        is_silence=SilenceState.NOT_SILENT,
    )

    # 通知房间内的用户
    event = InformVcOnJoinRoom(
        user=user_model.model_dump(),
        user_count=room.user_count,
    )

    inform = RtsInform(
        event="vcOnJoinRoom",
        data=event.model_dump(),
    )

    room_users = room.get_all_users()
    for room_user in room_users:
        if room_user.id == user.id or len(room_user.id) != HUMAN_USER_ID_LENGTH:
            continue
        body = UnicastMessageBase(
            AppId=app_id,
            To=room_user.id,
            Message=inform.model_dump_json(),
        )
        logger.debug(f"发送房间外点对点消息: {json.dumps(body.model_dump(), indent=2, ensure_ascii=False)}")
        response = await rtc_service.send_unicast(body.model_dump_json())
        logger.debug(f"房间外点对点消息发送结果: {json.dumps(response, indent=2, ensure_ascii=False)}")


# 用户离开房间通知
async def leave_room_infom(app_id: str, room: MeetingRoom, user_id: str):
    if len(user_id) == HUMAN_USER_ID_LENGTH:
        user_name = await mysql_client.get_user_name(user_id)
    else:
        user_name = user_id
    
    user_model = UserModel(
        user_id=user_id,
        user_name=user_name,
        camera=DeviceState.OPEN,
        mic=DeviceState.OPEN,
        is_silence=SilenceState.NOT_SILENT,
    )

    # 通知房间内的用户
    event = InformVcOnLeaveRoom(
        user=user_model.model_dump(),
        user_count=room.user_count,
    )

    inform = RtsInform(
        event="vcOnLeaveRoom",
        data=event.model_dump(),
    )
    
    room_users = room.get_all_users()
    for room_user in room_users:
        if room_user.id == user_id or len(room_user.id) != HUMAN_USER_ID_LENGTH:
            continue
        body = UnicastMessageBase(
            AppId=app_id,
            To=room_user.id,
            Message=inform.model_dump_json(),
        )
        logger.debug(f"发送房间外点对点消息: {json.dumps(body.model_dump(), indent=2, ensure_ascii=False)}")
        response = await rtc_service.send_unicast(body.model_dump_json())
        logger.debug(f"房间外点对点消息发送结果: {json.dumps(response, indent=2, ensure_ascii=False)}")
