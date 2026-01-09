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
            ):
        self.user = MeetingUser(
            user_id = user_id,
            user_name = user_name,
            device_id = device_id,
            camera = camera,
            mic = mic,
        )

    # 获取用户ID
    def get_user_id(self) -> str:
        return self.user.user_id
    
    # 获取用户名
    def get_user_name(self) -> str:
        return self.user.user_name
    
    # 设置用户角色
    def set_user_role(self, user_role: UserRole) -> None:
        self.user.user_role = user_role
    
    # 进入房间
    def join_room(self, room_id: str, role: UserRole) -> None:
        self.user.join_time = int(time.time() * 1000)
        self.user.room_id = room_id
        self.user.user_role = role

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


# 房间模型
class RoomModel:
    def __init__(self,
                 app_id: str,
                 room_id: str,
                 host_user: UserModel,
                 ):
        self.room = MeetingRoomState(
            app_id = app_id,
            room_id = room_id,
            room_name = f"meet_{room_id}",
            host_user_id = host_user.get_user_id(),
            host_user_name = host_user.get_user_name(),
            start_time = int(time.time() * 1000),
            base_time= int(time.time() * 1000),
            activeSpeakers = [host_user.get_user_id()],
            )
        self.users = OrderedDict()
        self.add_user(host_user, UserRole.HOST)

    # 用户进入房间
    def add_user(self, user: UserModel, role: UserRole = UserRole.VISITOR) -> None:
        user.join_room(self.room.room_id, role)
        self.users[user.get_user_id()] = user

    # 用户退出房间
    def remove_user(self, user_id: str) -> None:
        if user_id in self.users:
            del self.users[user_id]
            # 如果删除的是主持人，将下一个用户设为主持人
            if self.room.host_user_id == user_id:
                self.room.host_user_id = next(iter(self.users), None)
                if self.room.host_user_id:
                    self.room.host_user_name = self.users[self.room.host_user_id].get_user_name()
                    self.users[self.room.host_user_id].set_user_role(UserRole.HOST)

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
        return [u.user for u in self.users.values()]
    