"""
会议管理API
提供会议预定、取消、查询等功能

注意：此文件已被移动到 jusi_meet_server 项目中
当前保留在此处作为 RTS 服务的直接接口实现
如需使用会议管理功能，请通过 jusi_meet_server 项目的接口访问
"""
import logging
from fastapi import APIRouter
from schemas import *
from rts_service import rtsService

logger = logging.getLogger(__name__)

meeting_router = APIRouter()


# 预定会议
@meeting_router.post("/meeting/book", response_model=BookMeetingResponse)
async def book_meeting(request: BookMeetingRequest):
    """
    预定会议

    Args:
        request: 预定会议请求

    Returns:
        预定结果
    """
    try:
        success = await rtsService.create_room(
            room_id=request.room_id,
            host_user_id=request.host_user_id,
            host_user_name=request.host_user_name,
            room_name=request.room_name,
            host_device_sn=request.host_device_sn,
        )

        if success:
            return BookMeetingResponse(
                code=200,
                room_id=request.room_id,
                room_name=request.room_name or request.room_id,
                message="会议预定成功"
            )
        else:
            return BookMeetingResponse(
                code=400,
                room_id=request.room_id,
                room_name=request.room_name or request.room_id,
                message="会议已存在，预定失败"
            )
    except Exception as e:
        logger.error(f"预定会议失败: {e}")
        return BookMeetingResponse(
            code=500,
            room_id=request.room_id,
            room_name=request.room_name or request.room_id,
            message=f"服务器错误: {str(e)}"
        )


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
