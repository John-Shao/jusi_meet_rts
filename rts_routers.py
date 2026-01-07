import logging
from fastapi import APIRouter, Depends, Request
import json
from typing import Optional, Dict
from models import *
from meeting_service import MeetingService
from user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/rts/message", response_model=BaseResponse)
async def handle_rts_message(request: Request):
    # 手动获取请求体
    body = await request.body()
    try:
        # 手动解析JSON，不管Content-Type头是什么
        request_data = json.loads(body.decode("utf-8"))
        logger.debug(f"收到 RTS 消息: {request_data}")
        
        # 处理嵌套的JSON结构
        if "message" in request_data:
            # message字段本身是JSON字符串，需要再次解析
            message_data = json.loads(request_data["message"])
            event_name = message_data.get("event_name")
            content_str = message_data.get("content")
            
            # content字段可能也是JSON字符串，需要再次解析
            try:
                content = json.loads(content_str)
            except (json.JSONDecodeError, TypeError):
                content = content_str
        else:
            # 兼容原来的直接结构
            event_name = request_data.get("event_name")
            content = request_data.get("content", {})
            
        if not event_name:
            return BaseResponse(code=400, message="Missing event_name")
            
    except json.JSONDecodeError:
        return BaseResponse(code=400, message="Invalid JSON format")
    
    logger.debug(f"事件名称: {event_name}, 事件内容: {content}")
    
    # 根据不同的事件名称处理不同的消息
    if event_name == "vcJoinRoom":
        return await handle_join_room(content)
    elif event_name == "vcLeaveRoom":
        return await handle_leave_room(content)
    elif event_name == "vcFinishRoom":
        return await handle_finish_room(content)
    elif event_name == "vcResync":
        return await handle_resync(content)
    elif event_name == "vcGetUserList":
        return await handle_get_user_list(content)
    elif event_name == "vcOperateSelfCamera":
        return await handle_operate_self_camera(content)
    elif event_name == "vcOperateSelfMic":
        return await handle_operate_self_mic(content)
    elif event_name == "vcOperateSelfMicApply":
        return await handle_operate_self_mic_apply(content)
    elif event_name == "vcStartShare":
        return await handle_start_share(content)
    elif event_name == "vcFinishShare":
        return await handle_finish_share(content)
    elif event_name == "vcSharePermissionApply":
        return await handle_share_permission_apply(content)
    elif event_name == "vcOperateOtherCamera":
        return await handle_operate_other_camera(content)
    elif event_name == "vcOperateOtherMic":
        return await handle_operate_other_mic(content)
    elif event_name == "vcOperateOtherSharePermission":
        return await handle_operate_other_share_permission(content)
    elif event_name == "vcOperateAllMic":
        return await handle_operate_all_mic(content)
    elif event_name == "vcOperateSelfMicPermit":
        return await handle_operate_self_mic_permit(content)
    elif event_name == "vcSharePermissionPermit":
        return await handle_share_permission_permit(content)
    else:
        return BaseResponse(code=400, message=f"Unknown event: {event_name}")

# 处理加入房间
async def handle_join_room(content: Dict):
    meeting_service = MeetingService()
    user_service = UserService()
    
    # 解析参数
    user_name = content.get("user_name")
    camera = DeviceState(content.get("camera", 0))
    mic = DeviceState(content.get("mic", 0))
    is_silence = Silence(content.get("is_silence", 0)) if content.get("is_silence") else None
    
    # 创建用户
    user = await user_service.create_user(user_name, camera, mic, is_silence)
    
    # 加入房间
    join_result = await meeting_service.join_room(user)
    
    return BaseResponse(data=join_result.model_dump())

# 处理离开房间
async def handle_leave_room(content: Dict):
    meeting_service = MeetingService()
    user_id = content.get("user_id")
    
    await meeting_service.leave_room(user_id)
    
    return BaseResponse()

# 处理关闭房间
async def handle_finish_room(content: Dict):
    meeting_service = MeetingService()
    room_id = content.get("room_id")
    
    await meeting_service.finish_room(room_id)
    
    return BaseResponse()

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