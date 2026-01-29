'''
会议管理系统，与火山veRTC Meeting Demo配套的业务服务器
该服务的地址通过登录服务的setAppInfo接口返回给前端
'''
import logging
from fastapi import (
    APIRouter,
    Request,
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

meeting_router = APIRouter()

@meeting_router.post("/rts/message", response_model=ResponseMessageBase)
async def handle_rts_message(request: Request, background_tasks: BackgroundTasks):
    # 手动获取请求体
    body = await request.body()
    try:
        # 手动解析JSON，不管Content-Type头是什么
        request_data = json.loads(body.decode("utf-8"))
        logger.debug(f"收到通知: {json.dumps(request_data, indent=2, ensure_ascii=False)}")

        msg_str = request_data.get("message", "")
        binary = request_data.get("binary", False)
        signature = request_data.get("signature", "")

        # 不处理二进制消息
        if binary:
            logger.warning(f"收到二进制消息，丢弃: {msg_str}")
            return ResponseMessageBase(
                code=400,
                request_id=message.request_id,
                event_name=message.event_name,
                content="binary message not supported",
                )

        # 验证签名（这里简单用字符串比较，实际应进行签名验证）
        if signature != "temp_server_signature":
            logger.warning(f"收到无效签名消息: {msg_str}")
            return ResponseMessageBase(
                code=401,
                request_id=message.request_id,
                event_name=message.event_name,
                content="invalid signature",
                )

        # 解析message字段
        message = RequestMessageBase(**json.loads(msg_str))
        logger.debug(f"通知内容: {json.dumps(message.model_dump(), indent=2, ensure_ascii=False)}")
        # 规范化content字段
        if 'content' not in message.model_dump() or message.content in ("", "null"):
            message.content = "{}"
    except json.JSONDecodeError:
        logger.error(f"JSON解析错误: {msg_str}")
        return ResponseMessageBase(
            code=402,
            request_id=message.request_id,
            event_name=message.event_name,
            content="invalid message format",
            )

    # 添加后台任务处理返回消息
    background_tasks.add_task(send_return_message, message)
    
    return ResponseMessageBase(
        code=200,
        request_id=message.request_id,
        event_name=message.event_name,
        content="ok",
        )

# 异步发送return消息
async def send_return_message(message: RequestMessageBase):
    try:
        # 验证登录态（这里需要验证登录态）
        if not message.login_token:
            logger.warning(f"收到缺失登录态消息: {message}")
            return

        content = json.loads(message.content)
        logger.debug(f"事件信息: {json.dumps(content, indent=2, ensure_ascii=False)}")
            
    except json.JSONDecodeError:
        logger.error(f"JSON解析错误: {message}")
        return

    # 根据不同的事件名称处理不同的消息
    handler = EVENT_HANDLERS.get(message.event_name)
    if handler:
        await handler(message, content)
    else:
        logger.warning(f"收到未知事件消息: {message}")

# 处理加入房间事件
async def handle_join_room(message: RequestMessageBase, content: Dict):
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
        user_list = room.get_user_list(),
        token = generate_token(user.id, message.room_id),
        wb_room_id = wb_room_id,
        wb_user_id = wb_user_id,
        wb_token = generate_token(wb_user_id, wb_room_id),
    )

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=response,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")


# 处理离开房间事件
async def handle_leave_room(message: RequestMessageBase, content: Dict):
    await service.leave_room(message.user_id, message.room_id)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 处理关闭房间事件
async def handle_finish_room(message: RequestMessageBase, content: Dict):
    await service.finish_room(message.user_id, message.room_id)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 处理重连同步
async def handle_resync(message: RequestMessageBase, content: Dict):
    room: RoomModel = await service.get_room(message.room_id)
    user: UserModel = room.get_user(message.user_id)

    response = ReconnectRes(
        room = room.to_dict(),
        user= user.to_dict(),
        user_list = room.get_user_list(),
    )

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=response,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 处理获取用户列表
async def handle_get_user_list(message: RequestMessageBase, content: Dict):
    room: RoomModel = await service.get_room(message.room_id)
    user: UserModel = room.get_user(message.user_id)

    response = GetUserListRes(
        user_count = len(room.get_user_list()),
        user_list = room.get_user_list(),
    )

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=response,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 处理操纵自己的摄像头
async def handle_operate_self_camera(message: RequestMessageBase, content: Dict):
    operate: DeviceState = content.get("operate")

    await service.operate_self_camera(message.user_id, message.room_id, operate)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 处理操纵自己的麦克风
async def handle_operate_self_mic(message: RequestMessageBase, content: Dict):
    operate: DeviceState = content.get("operate")

    await service.operate_self_mic(message.user_id, message.room_id, operate)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 处理操纵自己麦克风权限申请
async def handle_operate_self_mic_apply(message: RequestMessageBase, content: Dict):
    operate: Permission = content.get("operate")

    await service.operate_self_mic_apply(message.user_id, message.room_id, operate)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 处理本地用户开始共享
async def handle_start_share(message: RequestMessageBase, content: Dict):
    share_type: ShareType = content.get("share_type")

    await service.start_share(message.user_id, message.room_id, share_type)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 处理本地用户停止共享
async def handle_finish_share(message: RequestMessageBase, content: Dict):
    await service.finish_share(message.user_id, message.room_id)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 处理申请共享权限
async def handle_share_permission_apply(message: RequestMessageBase, content: Dict):
    await service.share_permission_apply(message.user_id, message.room_id)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 处理操纵参会人的摄像头
async def handle_operate_other_camera(message: RequestMessageBase, content: Dict):
    operate: DeviceState = content.get("operate")
    operate_user_id = content.get("operate_user_id")

    await service.operate_other_camera(message.user_id, message.room_id, operate_user_id, operate)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 处理操纵参会人的麦克风
async def handle_operate_other_mic(message: RequestMessageBase, content: Dict):
    operate: DeviceState = content.get("operate")
    operate_user_id = content.get("operate_user_id")

    await service.operate_other_mic(message.user_id, message.room_id, operate_user_id, operate)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")


# 处理操纵参会人屏幕共享权限
async def handle_operate_other_share_permission(message: RequestMessageBase, content: Dict):
    operate = content.get("operate")
    operate_user_id = content.get("operate_user_id")

    await service.operate_other_share_permission(message.user_id, message.room_id, operate_user_id, operate)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 处理全员麦克风操作
async def handle_operate_all_mic(message: RequestMessageBase, content: Dict):
    operate_self_mic_permission: Permission = content.get("operate_self_mic_permission")  # 全员静音后，是否允许房间内观众自行开麦
    operate: DeviceState = content.get("operate")  # 全员静音或取消静音

    await service.operate_all_mic(message.user_id, message.room_id, operate_self_mic_permission, operate)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 观众请求麦克风使用权限后, 主持人答复
async def handle_operate_self_mic_permit(message: RequestMessageBase, content: Dict):
    apply_user_id: str = content.get("apply_user_id")  # 申请麦克风使用权限的用户ID
    permit: Permission = content.get("permit")  # 主持人是否同意麦克风使用权限

    await service.operate_self_mic_permit(message.user_id, message.room_id, apply_user_id, permit)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")

# 观众请求屏幕共享权限后, 主持人答复
async def handle_share_permission_permit(message: RequestMessageBase, content: Dict):
    apply_user_id: str = content.get("apply_user_id")  # 申请屏幕共享权限的用户ID
    permit: Permission = content.get("permit")  # 主持人是否同意屏幕共享权限

    await service.operate_self_share_permission_permit(message.user_id, message.room_id, apply_user_id, permit)

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=None,
    )

    body = UnicastMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")


# 处理程序映射
EVENT_HANDLERS = {
    "vcJoinRoom": handle_join_room,
    "vcLeaveRoom": handle_leave_room,
    "vcFinishRoom": handle_finish_room,
    "vcResync": handle_resync,
    "vcGetUserList": handle_get_user_list,
    "vcOperateSelfCamera": handle_operate_self_camera,
    "vcOperateSelfMic": handle_operate_self_mic,
    "vcOperateSelfMicApply": handle_operate_self_mic_apply,
    "vcStartShare": handle_start_share,
    "vcFinishShare": handle_finish_share,
    "vcSharePermissionApply": handle_share_permission_apply,
    "vcOperateOtherCamera": handle_operate_other_camera,
    "vcOperateOtherMic": handle_operate_other_mic,
    "vcOperateOtherSharePermission": handle_operate_other_share_permission,
    "vcOperateAllMic": handle_operate_all_mic,
    "vcOperateSelfMicPermit": handle_operate_self_mic_permit,
    "vcSharePermissionPermit": handle_share_permission_permit,
}
