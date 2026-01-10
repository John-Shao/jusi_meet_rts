from typing import Dict, OrderedDict, Any
from schemas import *
from user_model import UserModel
from utils import current_timestamp_s

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
            start_time = current_timestamp_s(),
            base_time= current_timestamp_s(),
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
            "app_id": self._room.app_id,
            "room_id": self._room.room_id,
            "room_name": self._room.room_name,
            "host_user_id": self._room.host_user_id,
            "host_user_name": self._room.host_user_name,
            "room_mic_status": int(self._room.room_mic_status),
            "operate_self_mic_permission": int(self._room.operate_self_mic_permission),
            "share_status": int(self._room.share_status),
            "share_type": int(self._room.share_type),
            "share_user_id": self._room.share_user_id,
            "share_user_name": self._room.share_user_name,
            "start_time": self._room.start_time,
            "base_time": self._room.base_time,
            "record_status": int(self._room.record_status),
            "record_start_time": self._room.record_start_time,
            "status": self._room.status,
            "experience_time_limit": 1800,  # 体验时长限制
            "ext": "",
        }
    
    # 获取用户列表
    def get_user_list(self) -> List[Dict]:
        return [u.to_dict() for u in self._users.values()]
