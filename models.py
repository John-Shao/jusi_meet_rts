import time
from typing import Dict, Optional, OrderedDict
from schemas import *

# 会议用户
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
        self._user.join_time = int(time.time() * 1000)
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


# 房间模型
class RoomModel:
    def __init__(self,
                 app_id: str,
                 room_id: str,
                 host_user: UserModel,
                 ):
        self._room = MeetingRoomState(
            app_id = app_id,
            room_id = room_id,
            room_name = f"meet_{room_id}",
            host_user_id = host_user.user_id,
            host_user_name = host_user.user_name,
            start_time = int(time.time() * 1000),
            base_time= int(time.time() * 1000),
            activeSpeakers = [host_user.user_id],
            )
        self._users = OrderedDict()
        self.add_user(host_user, UserRole.HOST)

    # 用户进入房间
    def add_user(self, user: UserModel, role: UserRole = UserRole.VISITOR) -> None:
        user.join_room(self._room.room_id, role)
        self._users[user.user_id] = user

    # 用户退出房间
    def remove_user(self, user_id: str) -> None:
        if user_id in self._users:
            del self._users[user_id]
            # 如果删除的是主持人，将下一个用户设为主持人
            if self._room.host_user_id == user_id:
                self._room.host_user_id = next(iter(self._users), None)
                if self._room.host_user_id:
                    self._room.host_user_name = self._users[self._room.host_user_id].user_name
                    self._users[self._room.host_user_id].set_user_role(UserRole.HOST)

    # 检查用户是否在房间中
    def user_in_room(self, user_id: str) -> bool:
        return user_id in self._users

    # 转换成字典对象
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user.user_id,
            "user_name": self.user.user_name,
            "user_role": int(self.user.user_role),
            "camera": int(self.user.camera),
            "mic": int(self.user.mic),
            "join_time": self.user.join_time,
            "room_id": self.user.room_id,
            "share_permission": int(self.user.share_permission),
            "share_status": int(self.user.share_status),
            "share_type": int(self.user.share_type),
            "operate_camera_permission": int(self.user.operate_camera_permission),
            "operate_mic_permission": int(self.user.operate_mic_permission),
            "is_silence": int(self.user.is_silence),
        }
    
    # 获取用户列表
    def get_user_list(self) -> List[MeetingUser]:
        return [u.user for u in self._users.values()]
    