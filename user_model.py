from typing import Dict, Optional, Any
from schemas import *
from utils import current_timestamp


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
    def user_id(self) -> str:
        return self._user.user_id
    
    @property
    def user_name(self) -> str:
        return self._user.user_name
    
    # 设置用户角色
    def set_user_role(self, user_role: UserRole) -> None:
        self._user.user_role = user_role
    
    # 进入房间
    def join_room(self, room_id: str, role: UserRole) -> None:
        self._user.join_time = current_timestamp()
        self._user.room_id = room_id
        self._user.user_role = role

    # 转换成字典对象
    def to_dict(self) -> Dict[str, Any]:
        user_dict = {
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
    
        if self._user.is_silence is not None:
            user_dict["is_silence"] = int(self._user.is_silence)

        return user_dict
