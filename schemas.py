from enum import IntEnum
from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict


# 用户角色枚举
class UserRole(IntEnum):
    VISITOR = 0  # 参会者
    HOST = 1     # 主持人

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

# 请求消息
class ServerMessage(BaseModel):
    app_id: str
    room_id: Optional[str]
    device_id: Optional[str]
    user_id: str
    login_token: Optional[str]
    request_id: str
    event_name: str
    content: str  # JSON string

# RTS消息基础模型
class RTSMessage(BaseModel):
    event_name: str
    content: Dict

# 响应模型
class BaseResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Dict] = None

# 音频属性信息
class AudioPropertiesInfo(BaseModel):
    linearVolume: int
    nonlinearVolume: int

# 会议房间状态
class MeetingRoomState(BaseModel):
    app_id: Optional[str]
    room_id: Optional[str]
    room_name: Optional[str]
    host_user_id: Optional[str]
    host_user_name: Optional[str]
    room_mic_status: DeviceState = RoomMicStatus.ALLOW_MIC               # 房间内是否全体静音
    operate_self_mic_permission: Permission = Permission.HAS_PERMISSION  # 操作自己麦克风权限
    share_status: ShareStatus = ShareStatus.NOT_SHARING                  # 房间内是否正在共享
    share_type: Optional[ShareType]
    share_user_id: Optional[str]
    share_user_name: Optional[str]
    start_time: int = 0       # 会议开始时间，时间戳，单位毫秒
    base_time: Optional[int]  # 服务器时间，时间戳，单位毫秒
    record_status: Optional[RecordStatus]   # 录制状态
    record_start_time: Optional[int]        # 可选，最近一次开始录制的时间
    activeSpeakers: List[str] = []          # 活动用户ID（user_id）列表    

# 会议用户信息
class MeetingUser(BaseModel):
    user_id: str
    user_name: str
    user_role: UserRole
    camera: DeviceState
    mic: DeviceState
    join_time: int
    room_id: str
    share_permission: Permission = Permission.HAS_PERMISSION
    share_status: ShareStatus = ShareStatus.NOT_SHARING
    share_type: ShareType = ShareType.SCREEN
    operate_camera_permission: Optional[Permission] = Permission.HAS_PERMISSION  # 操作自己摄像头权限
    operate_mic_permission: Optional[Permission] = Permission.HAS_PERMISSION     # 操作自己麦克风权限
    is_silence: Optional[Silence] = Silence.NOT_SILENT  # 是否静音
    audioPropertiesInfo: Optional[AudioPropertiesInfo]
    isLocal: Optional[bool]
    isActive: Optional[bool]

# 加入房间响应
class JoinMeetingRoomRes(BaseModel):
    room: MeetingRoomState
    user: MeetingUser
    user_list: List[MeetingUser]
    token: str
    wb_room_id: str
    wb_user_id: str
    wb_token: str
