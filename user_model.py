from typing import Dict, Optional, Any
from schemas import *
from utils import current_timestamp_ms


# 用户模型
class UserModel:
    def __init__(self,
            user_id: str,
            user_name: str,
            device_id: str,
            camera: DeviceState,
            mic: DeviceState,
            is_silence: Optional[SilenceState] = None,
            ):
        self._user = MeetingUser(
            user_id = user_id,
            user_name = user_name,
            device_id = device_id,
            camera = camera,
            mic = mic,
            is_silence = is_silence,
        )

    @property
    def model(self) -> MeetingUser:
        return self._user

    @property
    def id(self) -> str:
        return self._user.user_id
    
    @property
    def name(self) -> str:
        return self._user.user_name
    
    @property
    def role(self) -> UserRole:
        return self._user.user_role

    # 设置用户角色
    def set_user_role(self, user_role: UserRole) -> None:
        self._user.user_role = user_role
    
    # 进入房间
    def join_room(self, room_id: str, role: UserRole) -> None:
        self._user.join_time = current_timestamp_ms()
        self._user.room_id = room_id
        self._user.user_role = role
    
    # 操纵自己的摄像头
    def operate_camera(self, operate: DeviceState) -> None:
        self._user.camera = operate

    # 操纵自己的麦克风
    def operate_mic(self, operate: DeviceState) -> None:
        self._user.mic = operate
    
    # 更新屏幕共享权限
    def update_share_permission(self, permission: Permission) -> None:
        self._user.share_permission = permission
    
    # 更新麦克风权限
    def update_mic_permission(self, permission: Permission) -> None:
        self._user.operate_mic_permission = permission

    # 开始共享
    def start_share(self, share_type: ShareType) -> None:
        self._user.share_status = ShareStatus.SHARING
        self._user.share_type = share_type

    # 结束共享
    def finish_share(self) -> None:
        self._user.share_status = ShareStatus.NOT_SHARING
        self._user.share_type = ShareType.SCREEN


    # 转换成字典对象
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self._user.user_id,
            "user_name": self._user.user_name,
            "user_role": int(self._user.user_role),
            "camera": int(self._user.camera),
            "mic": int(self._user.mic),
            "join_time": self._user.join_time,
            "room_id": self._user.room_id,
            "share_permission": int(self._user.share_permission),
            "share_status": int(self._user.share_status),
            "share_type": int(self._user.share_type),
            "operate_camera_permission": int(self._user.operate_camera_permission),
            "operate_mic_permission": int(self._user.operate_mic_permission),
        }
