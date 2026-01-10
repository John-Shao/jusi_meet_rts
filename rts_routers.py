import logging
from fastapi import (
    APIRouter,
    Request,
    Response,
    BackgroundTasks,
    )
import json
from typing import Dict
from schemas import (
    DeviceState,
    JoinMeetingRoomRes,
    RequestMessageBase,
    ResponseMessageBase,
    ReturnMessageBase,
)
from user_model import UserModel
from room_model import RoomModel
from utils import generate_token
from rts_service import service
from vertc_service import rtc_service


logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/rts/message", response_model=ResponseMessageBase)
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
                status_code=400,
                request_id=message.request_id,
                event_name=message.event_name,
                content="binary message not supported",
                )

        # 验证签名（这里简单用字符串比较，实际应进行签名验证）
        if signature != "temp_server_signature":
            logger.warning(f"收到无效签名消息: {msg_str}")
            return ResponseMessageBase(
                status_code=401,
                request_id=message.request_id,
                event_name=message.event_name,
                content="invalid signature",
                )

        # 解析message字段
        message = RequestMessageBase(**json.loads(msg_str))
        logger.debug(f"通知内容: {json.dumps(message.model_dump(), indent=2, ensure_ascii=False)}")
    except json.JSONDecodeError:
        logger.error(f"JSON解析错误: {msg_str}")
        return ResponseMessageBase(
            status_code=402,
            request_id=message.request_id,
            event_name=message.event_name,
            content="invalid message format",
            )

    # 添加后台任务处理返回消息
    background_tasks.add_task(send_return_message, message)
    
    return ResponseMessageBase(
        status_code=200,
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

'''
处理加入房间
请求消息实例
{
  "message": ("{\"app_id\":\"693b6cadaecbdd017582aa25\",\"room_id\":\"100\",\"device_id\":\"3f722811-2ec1-4335-ac1d-e3f7daeb3c3e\","
              + "\"user_id\":\"7fd6b7ace1194a86b4249f9e1a137194\",\"login_token\":\"25573a5fe8654450a4755b5e0bf131ab\","
              + "\"request_id\":\"vcJoinRoom:83bca91d-b75b-43be-93c6-3b130b711e42\",\"event_name\":\"vcJoinRoom\","
              + "\"content\":\"{\\\"user_name\\\":\\\"11111111111\\\",\\\"camera\\\":1,\\\"mic\\\":1}\"}"),
  "binary": false,
  "signature": "temp_server_signature"
}
'''
async def handle_join_room(message: Dict, content: Dict|str):
    """
    处理加入房间事件
    """
    user_name = content.get("user_name")
    camera = DeviceState(content.get("camera", DeviceState.CLOSED))
    mic = DeviceState(content.get("mic", DeviceState.CLOSED))
    is_silence = content.get("is_silence", None)
    
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
    '''
    response = JoinMeetingRoomRes(
        room = room.to_dict(),
        user= user.to_dict(),
        user_list = room.get_user_list(),
        token = generate_token(user._user.user_id, message.room_id),
        wb_room_id = wb_room_id,
        wb_user_id = wb_user_id,
        wb_token = generate_token(wb_user_id, wb_room_id),
    )

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=response.model_dump(),
    )
    '''
    response = {
        "room": room.to_dict(),
        "user": user.to_dict(),
        "user_list": room.get_user_list(),
        "token": generate_token(user._user.user_id, message.room_id),
        "wb_room_id": wb_room_id,
        "wb_user_id": wb_user_id,
        "wb_token": generate_token(wb_user_id, wb_room_id),
    }

    res = ResponseMessageBase(
        request_id=message.request_id,
        event_name=message.event_name,
        response=response,
    )

    body = ReturnMessageBase(
        AppId=message.app_id,
        To=message.user_id,
        Message=res.model_dump_json(),
    )

    response = rtc_service.send_unicast(body.model_dump_json())
    logger.debug(f"返回消息: {json.dumps(response, indent=2, ensure_ascii=False)}")


# 处理离开房间
async def handle_leave_room(content: Dict):
    pass

# 处理关闭房间
async def handle_finish_room(content: Dict):
    pass

'''
# 处理重连同步
async def handle_resync(content: Dict):
    meeting_service = MeetingService()
    user_id = content.get("user_id")
    room_id = content.get("room_id")
    
    reconnect_result = await meeting_service.reconnect(room_id, user_id)
    
    return BaseResponse(data=reconnect_result.dict())

# 处理获取用户列表
async def handle_get_user_list(content: Dict):
    meeting_service = MeetingService()
    room_id = content.get("room_id")
    
    user_list_result = await meeting_service.get_user_list(room_id)
    
    return BaseResponse(data=user_list_result.dict())

# 处理操作自己的摄像头
async def handle_operate_self_camera(content: Dict):
    user_service = UserService()
    user_id = content.get("user_id")
    operate = DeviceState(content.get("operate"))
    
    await user_service.update_camera_state(user_id, operate)
    
    return BaseResponse()

# 处理操作自己的麦克风
async def handle_operate_self_mic(content: Dict):
    user_service = UserService()
    user_id = content.get("user_id")
    operate = DeviceState(content.get("operate"))
    
    await user_service.update_mic_state(user_id, operate)
    
    return BaseResponse()

# 处理申请麦克风权限
async def handle_operate_self_mic_apply(content: Dict):
    meeting_service = MeetingService()
    user_id = content.get("user_id")
    
    await meeting_service.apply_mic_permission(user_id)
    
    return BaseResponse()

# 处理开始共享
async def handle_start_share(content: Dict):
    user_service = UserService()
    user_id = content.get("user_id")
    share_type = ShareType(content.get("share_type"))
    
    await user_service.start_share(user_id, share_type)
    
    return BaseResponse()

# 处理停止共享
async def handle_finish_share(content: Dict):
    user_service = UserService()
    user_id = content.get("user_id")
    
    await user_service.stop_share(user_id)
    
    return BaseResponse()

# 处理申请共享权限
async def handle_share_permission_apply(content: Dict):
    meeting_service = MeetingService()
    user_id = content.get("user_id")
    
    await meeting_service.apply_share_permission(user_id)
    
    return BaseResponse()

# 处理操作其他用户的摄像头
async def handle_operate_other_camera(content: Dict):
    user_service = UserService()
    operate_user_id = content.get("operate_user_id")
    operate = DeviceState(content.get("operate"))
    
    await user_service.update_camera_state(operate_user_id, operate)
    
    return BaseResponse()

# 处理操作其他用户的麦克风
async def handle_operate_other_mic(content: Dict):
    user_service = UserService()
    operate_user_id = content.get("operate_user_id")
    operate = DeviceState(content.get("operate"))
    
    await user_service.update_mic_state(operate_user_id, operate)
    
    return BaseResponse()

# 处理操作其他用户的共享权限
async def handle_operate_other_share_permission(content: Dict):
    user_service = UserService()
    operate_user_id = content.get("operate_user_id")
    operate = Permission(content.get("operate"))
    
    await user_service.update_share_permission(operate_user_id, operate)
    
    return BaseResponse()

# 处理全员禁言
async def handle_operate_all_mic(content: Dict):
    meeting_service = MeetingService()
    room_id = content.get("room_id")
    operate_self_mic_permission = Permission(content.get("operate_self_mic_permission"))
    operate = DeviceState.Closed
    
    await meeting_service.mute_all(room_id, operate_self_mic_permission)
    
    return BaseResponse()

# 处理主持人答复麦克风申请
async def handle_operate_self_mic_permit(content: Dict):
    meeting_service = MeetingService()
    apply_user_id = content.get("apply_user_id")
    permit = DeviceState(content.get("permit"))
    
    await meeting_service.permit_mic_apply(apply_user_id, permit)
    
    return BaseResponse()

# 处理主持人答复共享权限申请
async def handle_share_permission_permit(content: Dict):
    meeting_service = MeetingService()
    apply_user_id = content.get("apply_user_id")
    permit = Permission(content.get("permit"))
    
    await meeting_service.permit_share_apply(apply_user_id, permit)
    
    return BaseResponse()
'''

# 处理程序映射
EVENT_HANDLERS = {
    "vcJoinRoom": handle_join_room,
    "vcLeaveRoom": handle_leave_room,
    "vcFinishRoom": handle_finish_room,
    # "vcResync": handle_resync,
    # "vcGetUserList": handle_get_user_list,
    # "vcOperateSelfCamera": handle_operate_self_camera,
    # "vcOperateSelfMic": handle_operate_self_mic,
    # "vcOperateSelfMicApply": handle_operate_self_mic_apply,
    # "vcStartShare": handle_start_share,
    # "vcFinishShare": handle_finish_share,
    # "vcSharePermissionApply": handle_share_permission_apply,
    # "vcOperateOtherCamera": handle_operate_other_camera,
    # "vcOperateOtherMic": handle_operate_other_mic,
    # "vcOperateOtherSharePermission": handle_operate_other_share_permission,
    # "vcOperateAllMic": handle_operate_all_mic,
    # "vcOperateSelfMicPermit": handle_operate_self_mic_permit,
    # "vcSharePermissionPermit": handle_share_permission_permit,
}