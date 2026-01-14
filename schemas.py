import time
from enum import IntEnum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from utils import current_timestamp_ms, current_timestamp_s

# ================================== Meeting ==================================

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
class SilenceState(IntEnum):
    NOT_SILENT = 0
    SILENCE = 1

# 请求消息模型
class RequestMessageBase(BaseModel):
    app_id: str
    room_id: Optional[str]
    device_id: Optional[str]
    user_id: str
    login_token: Optional[str]
    request_id: str
    event_name: str
    content: str = "{}"

# 房间外点对点消息模型（https://www.volcengine.com/docs/6348/1164061?lang=zh）
class UnicastMessageBase(BaseModel):
    AppId: str
    From: str = "server"
    To: str
    Binary: bool = False
    Message: Optional[str] = "{}"

# 房间内广播消息 SendBroadcast（https://www.volcengine.com/docs/6348/1164063?lang=zh）
class BroadcastMessageBase(BaseModel):
    AppId: str
    RoomId: str
    From: str = "server"
    Binary: bool = False
    Message: Optional[str] = "{}"

# 响应消息模型（UnicastMessageBase.Message，参考 rtsTypes.ts）
class ResponseMessageBase(BaseModel):
    message_type: str = 'return'
    request_id: str
    code: int = 200
    event_name: str
    message: str = "ok"  # 详细错误信息
    timestamp: int = Field(default_factory=lambda: current_timestamp_ms())  # 时间戳ms
    response: Optional[Any] = {}

# 会议房间状态
class MeetingRoomState(BaseModel):
    app_id: str
    room_id: str
    room_name: Optional[str] = ""
    host_user_id: Optional[str] = ""
    host_user_name: Optional[str] = ""
    room_mic_status: DeviceState = RoomMicStatus.ALLOW_MIC  # 房间内是否全体静音
    operate_self_mic_permission: Permission = Permission.HAS_PERMISSION  # 操作自己麦克风权限
    share_status: ShareStatus = ShareStatus.NOT_SHARING  # 房间内是否正在共享
    share_type: Optional[ShareType] = ShareType.SCREEN
    share_user_id: Optional[str] = ""
    share_user_name: Optional[str] = ""
    start_time: int = 0  # 会议开始时间，时间戳，单位秒
    base_time: Optional[int] = 0  # 服务器时间，时间戳，单位秒
    record_status: Optional[RecordStatus] = RecordStatus.NOT_RECORDING  # 录制状态
    record_start_time: Optional[int] = 0  # 最近一次开始录制的时间
    status: Optional[int] = 1

# 会议用户信息
class MeetingUser(BaseModel):
    user_id: str
    user_name: str
    user_role: Optional[UserRole] = UserRole.VISITOR
    camera: Optional[DeviceState] = DeviceState.OPEN
    mic: Optional[DeviceState] = DeviceState.OPEN
    join_time: Optional[int] = 0  # 加入时间，时间戳，单位毫秒
    room_id: Optional[str] = ""
    share_permission: Permission = Permission.HAS_PERMISSION
    share_status: ShareStatus = ShareStatus.NOT_SHARING
    share_type: ShareType = ShareType.SCREEN
    operate_camera_permission: Optional[Permission] = Permission.HAS_PERMISSION  # 操作自己摄像头权限
    operate_mic_permission: Optional[Permission] = Permission.HAS_PERMISSION     # 操作自己麦克风权限
    # 官方demo中没有的数据 
    is_silence: Optional[SilenceState] = SilenceState.NOT_SILENT  # 是否静音
    device_id: Optional[str] = ""

# 加入房间响应
class JoinMeetingRoomRes(BaseModel):
    nts: int = Field(default_factory=lambda: current_timestamp_s())  # 时间戳ms
    room: MeetingRoomState
    user: MeetingUser
    user_list: List[MeetingUser]
    token: str
    wb_room_id: str
    wb_user_id: str
    wb_token: str

# 断线之后重连响应
class ReconnectRes(BaseModel):
    room: MeetingRoomState
    user: MeetingUser
    user_list: List[MeetingUser]

# 获取用户列表响应
class GetUserListRes(BaseModel):
    user_count: int
    user_list: List[MeetingUser]

# ================================== Callback ==================================

# RTS回调通知
class RtsCallback(BaseModel):
    EventType: str
    EventData: str
    EventTime: str
    EventId: str
    AppId: str
    BusinessId: Optional[str] = ""
    Version: str
    Signature: str
    Nonce: str

# 用户加入房间回调事件数据
class UserJoinRoomEvent(BaseModel):
    RoomId: str
    UserId: str
    DeviceType: str
    MediaProcessingType: Optional[int] = 0
    Timestamp: Optional[int] = 0
    ExtraInfo: Optional[str] = ""
    UserExtraInfo: Optional[str] = ""

# 用户离开房间回调事件数据
class UserLeaveRoomEvent(BaseModel):
    RoomId: str
    UserId: str
    DeviceType: str
    MediaProcessingType: Optional[int] = 0
    Reason: Optional[str] = ""
    Duration: Optional[int] = 0
    Timestamp: Optional[int] = 0
    ExtraInfo: Optional[str] = ""


# ================================== Inform ==================================

# RTS通知消息
class RtsInform(BaseModel):
    message_type: str = 'inform'
    event: str
    data: Optional[Any] = {}
    timestamp: int = Field(default_factory=lambda: current_timestamp_ms())  # 时间戳ms

# 用户进入房间通知（vcOnJoinRoom）
class InformVcOnJoinRoom(BaseModel):
    user: Dict[str, Any]
    user_count: int

# 用户离开房间通知（vcOnLeaveRoom）
class InformVcOnLeaveRoom(BaseModel):
    user: Dict[str, Any]
    user_count: int
