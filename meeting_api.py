"""
会议管理API
提供会议预定、取消、查询等功能

注意：此文件已被移动到 jusi_meet_server 项目中
当前保留在此处作为 RTS 服务的直接接口实现
如需使用会议管理功能，请通过 jusi_meet_server 项目的接口访问
"""
import logging
import random
from fastapi import APIRouter
from schemas import *
from rts_service import rtsService
from drift_api import drift_join_room, drift_leave_room


logger = logging.getLogger(__name__)

meeting_router = APIRouter()

# 取消会议
@meeting_router.post("/meeting/cancel", response_model=CancelMeetingResponse)
async def cancel_meeting(request: CancelMeetingRequest):
    """
    取消会议（只有主持人可以取消，且房间内没有人时才能取消）

    Args:
        request: 取消会议请求

    Returns:
        取消结果
    """
    try:
        code, message = await rtsService.cancel_meeting(
            room_id=request.room_id,
            user_id=request.user_id,
        )

        return CancelMeetingResponse(
            code=code,
            room_id=request.room_id,
            message=message
        )
    except Exception as e:
        logger.error(f"取消会议失败: {e}")
        return CancelMeetingResponse(
            code=500,
            room_id=request.room_id,
            message=f"服务器错误: {str(e)}"
        )


# 查询我的会议
@meeting_router.post("/meeting/get-my", response_model=GetMyMeetingsResponse)
async def get_my_meetings(request: GetMyMeetingsRequest):
    """
    查询用户作为主持人的所有会议

    Args:
        request: 查询会议请求

    Returns:
        会议列表
    """
    try:
        meetings_data = await rtsService.get_user_meetings(user_id=request.user_id)

        # 转换为MeetingInfo对象
        meetings = [MeetingInfo(**meeting) for meeting in meetings_data]

        return GetMyMeetingsResponse(
            code=200,
            meetings=meetings,
            total=len(meetings),
            message="查询成功"
        )
    except Exception as e:
        logger.error(f"查询会议失败: {e}")
        return GetMyMeetingsResponse(
            code=500,
            meetings=[],
            total=0,
            message=f"服务器错误: {str(e)}"
        )


# 检查房间是否存在
@meeting_router.post("/meeting/check-room", response_model=CheckRoomResponse)
async def check_room(request: CheckRoomRequest):
    """
    检查房间号是否存在

    Args:
        request: 检查房间请求

    Returns:
        房间是否存在
    """
    try:
        exists = await rtsService.check_room_exists(room_id=request.room_id)

        return CheckRoomResponse(
            code=200,
            room_id=request.room_id,
            exists=exists,
            message="查询成功"
        )
    except Exception as e:
        logger.error(f"检查房间失败: {e}")
        return CheckRoomResponse(
            code=500,
            room_id=request.room_id,
            exists=False,
            message=f"服务器错误: {str(e)}"
        )


# 检查用户是否在房间中
@meeting_router.post("/meeting/check-user-in-room", response_model=CheckUserInRoomResponse)
async def check_user_in_room(request: CheckUserInRoomRequest):
    """
    检查用户是否在某个会议中

    Args:
        request: 检查用户在房间请求

    Returns:
        用户是否在房间中
    """
    try:
        result = await rtsService.check_user_in_room(
            room_id=request.room_id,
            user_id=request.user_id
        )

        if result == -1:
            return CheckUserInRoomResponse(
                code=404,
                room_id=request.room_id,
                user_id=request.user_id,
                in_room=False,
                message="房间不存在"
            )

        return CheckUserInRoomResponse(
            code=200,
            room_id=request.room_id,
            user_id=request.user_id,
            in_room=(result == 1),
            message="查询成功"
        )
    except Exception as e:
        logger.error(f"检查用户是否在房间失败: {e}")
        return CheckUserInRoomResponse(
            code=500,
            room_id=request.room_id,
            user_id=request.user_id,
            in_room=False,
            message=f"服务器错误: {str(e)}"
        )


# 相机加入会议
@meeting_router.post("/meeting/camera-join", response_model=CameraJoinResponse)
async def camera_join(request: CameraJoinRequest):
    """
    相机加入会议

    Args:
        request: 相机加入会议请求

    Returns:
        相机加入会议响应
    """
    try:
        # 如果 action_type = 0，需要先预定会议
        if request.action_type == 0:
            result = await rtsService.create_room(
                room_id=request.room_id,
                host_user_id=request.holder_user_id,
                host_user_name=request.holder_user_name,
                room_name=request.room_name,
                host_device_sn=request.device_sn,
            )

            if result == 1:
                return CameraJoinResponse(
                    code=400,
                    message="会议号已被占用"
                )
            elif result == 2:
                return CameraJoinResponse(
                    code=632,
                    message="设备已在房间中"
                )
        # 如果 action_type = 1，直接加入会议
        elif request.action_type == 1:
            # 检查房间是否存在
            room_exists = await rtsService.check_room_exists(room_id=request.room_id)
            if not room_exists:
                return CameraJoinResponse(
                    code=404,
                    message="会议不存在"
                )

        # 调用 drift_join_room 将相机加入会议
        drift_result = await drift_join_room(DriftJoinRequest(
            room_id=request.room_id,
            device_sn=request.device_sn
        ))

        if drift_result.code == 200:
            return CameraJoinResponse(
                code=200,
                rtmp_url=drift_result.data.rtmp_url,
                rtsp_url=drift_result.data.rtsp_url,
                message="相机加入会议成功"
            )
        else:
            return CameraJoinResponse(
                code=drift_result.code,
                message=drift_result.message
            )

    except Exception as e:
        logger.error(f"相机加入会议失败: {e}")
        return CameraJoinResponse(
            code=500,
            message=f"服务器错误: {str(e)}"
        )


# 相机离开会议
@meeting_router.post("/meeting/camera-leave", response_model=CameraLeaveResponse)
async def camera_leave(request: CameraLeaveRequest):
    """
    相机离开会议

    Args:
        request: 相机离开会议请求

    Returns:
        相机离开会议响应
    """
    try:
        # 调用 drift_leave_room 将相机退出会议
        drift_result = await drift_leave_room(DriftLeaveRequest(
            room_id=request.room_id,
            device_sn=request.device_sn
        ))

        if drift_result.code == 200:
            return CameraLeaveResponse(
                code=200,
                message="相机离开会议成功"
            )
        else:
            return CameraLeaveResponse(
                code=drift_result.code,
                message=drift_result.message
            )

    except Exception as e:
        logger.error(f"相机离开会议失败: {e}")
        return CameraLeaveResponse(
            code=500,
            message=f"服务器错误: {str(e)}"
        )


# 生成房间号
@meeting_router.post("/meeting/generate-room-id", response_model=GenerateRoomIdResponse)
async def generate_room_id():
    """
    生成一个不与现有会议号冲突的6位随机会议号

    Returns:
        生成的会议号
    """
    try:
        max_attempts = 100  # 最大尝试次数，避免无限循环

        for _ in range(max_attempts):
            # 生成6位随机正整数 (100000-999999)
            room_id = str(random.randint(100000, 999999))

            # 检查是否与现有会议号冲突
            exists = await rtsService.check_room_exists(room_id=room_id)

            if not exists:
                return GenerateRoomIdResponse(
                    code=200,
                    room_id=room_id,
                    message="生成会议号成功"
                )

        # 如果尝试了max_attempts次仍未找到可用的会议号
        return GenerateRoomIdResponse(
            code=500,
            message="生成会议号失败，请稍后重试"
        )

    except Exception as e:
        logger.error(f"生成会议号失败: {e}")
        return GenerateRoomIdResponse(
            code=500,
            message=f"服务器错误: {str(e)}"
        )
