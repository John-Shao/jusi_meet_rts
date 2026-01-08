from enum import IntEnum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DeviceState(IntEnum):
    Closed = 0
    Open = 1


class Permission(IntEnum):
    NoPermission = 0
    HasPermission = 1


class ShareType(IntEnum):
    Screen = 0
    Board = 1


class Silence(IntEnum):
    notSilent = 0
    silence = 1


class ServerMessage(BaseModel):
    app_id: str
    room_id: Optional[str]
    device_id: Optional[str]
    user_id: str
    login_token: Optional[str]
    request_id: str
    event_name: str
    content: str  # JSON string


# Payloads for various events
class JoinRoomPayload(BaseModel):
    user_name: str
    camera: DeviceState
    mic: DeviceState
    is_silence: Optional[Silence] = None


class OperateDevicePayload(BaseModel):
    operate: DeviceState


class OperateOtherDevicePayload(BaseModel):
    operate_user_id: str
    operate: DeviceState


class OperateOtherSharePermissionPayload(BaseModel):
    operate_user_id: str
    operate: Permission


class ApplyMicPermitPayload(BaseModel):
    apply_user_id: str
    permit: DeviceState


class SharePermissionPermitPayload(BaseModel):
    apply_user_id: str
    permit: Permission


# Response wrapper to match SendServerMessageRes<T>
class SendServerMessageRes(BaseModel):
    message_type: str = Field('return', const=True)
    request_id: str
    code: int
    message: str
    timestamp: int
    response: Optional[Any]


# Specific responses
class JoinMeetingRoomRes(BaseModel):
    room: Dict[str, Any]
    user: Dict[str, Any]
    user_list: List[Dict[str, Any]]
    token: str
    wb_room_id: str
    wb_user_id: str
    wb_token: str


class ReconnectRes(BaseModel):
    room: Dict[str, Any]
    user: Dict[str, Any]
    user_list: List[Dict[str, Any]]


class GetUserListRes(BaseModel):
    user_count: int
    user_list: List[Dict[str, Any]]
