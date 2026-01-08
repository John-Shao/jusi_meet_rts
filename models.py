from enum import IntEnum
from pydantic import BaseModel
from typing import Optional, List, Dict

# 用户角色枚举
class UserRole(IntEnum):
    VISITOR = 0
    HOST = 1

# 设备状态枚举
class DeviceState(IntEnum):
    CLOSED = 0
    OPEN = 1

# 权限枚举
class Permission(IntEnum):
    NO_PERMISSION = 0
    HAS_PERMISSION = 1

# 房间内是否全体静音
class RoomMicStatus(IntEnum):
    ALL_MUTED = 0
    ALLOW_MIC = 1

# 房间内是否正在录制
class RecordStatus(IntEnum):
    NOT_RECORDING = 0
    RECORDING = 1

# 共享类型枚举
class ShareType(IntEnum):
    SCREEN = 0
    BOARD = 1

# 房间内是否正在共享
class ShareStatus(IntEnum):
    NOT_SHARING = 0
    SHARING = 1

# 是否静默用户，云录屏用户是静默用户，其它用户不是静默用户
class Silence(IntEnum):
    NOT_SILENT = 0
    SILENCE = 1

# RTS消息基础模型
class RTSMessage(BaseModel):
    event_name: str
    content: Dict

# 响应模型
class BaseResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Dict] = None

# 会议房间状态
class MeetingRoomState(BaseModel):
    room_id: str
    room_name: Optional[str] = None
    create_time: int
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    status: int = 0  # 0: 未开始, 1: 进行中, 2: 已结束

# 会议用户信息
class MeetingUser(BaseModel):
    user_id: str
    user_name: str
    user_role: UserRole
    camera: DeviceState
    mic: DeviceState
    join_time: int
    share_permission: Permission
    share_status: int = 0  # 0: 未共享, 1: 共享中
    share_type: Optional[ShareType] = None
    is_silence: Optional[Silence] = None
    isLocal: Optional[bool] = False

# 加入房间响应
class JoinMeetingRoomRes(BaseModel):
    room: MeetingRoomState
    user: MeetingUser
    user_list: List[MeetingUser]
    token: str
    wb_room_id: str
    wb_user_id: str
    wb_token: str

# 重连响应
class ReconnectRes(BaseModel):
    room: MeetingRoomState
    user: MeetingUser
    user_list: List[MeetingUser]

# 获取用户列表响应
class GetUserListRes(BaseModel):
    user_count: int
    user_list: List[MeetingUser]
