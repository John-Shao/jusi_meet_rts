from typing import Dict, List, Optional
import time
from schemas import DeviceState, Permission, ShareType

# 用户模型
class User:
    def __init__(self, user_id: str, user_name: str, room_id: str, role: int = 0):
        self.user_id = user_id
        self.user_name = user_name
        self.room_id = room_id
        self.user_role = role
        self.camera = DeviceState.Closed
        self.mic = DeviceState.Closed
        self.share_permission = Permission.NoPermission
        self.share_status = 0
        self.share_type = ShareType.Screen
        self.join_time = int(time.time() * 1000)
        self.is_silence = 0

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "room_id": self.room_id,
            "user_role": self.user_role,
            "camera": int(self.camera),
            "mic": int(self.mic),
            "share_permission": int(self.share_permission),
            "share_status": int(self.share_status),
            "share_type": int(self.share_type),
            "join_time": self.join_time,
            "is_silence": int(self.is_silence),
        }


# 房间模型
class Room:
    def __init__(self, room_id: str, host_uid: Optional[str] = None):
        self.room_id = room_id
        self.host_user_id = host_uid
        self.users: Dict[str, User] = {}
        self.started_at = int(time.time() * 1000)
        self.finished = False
        self.finished_at = 0
        self.sharing_user_id: Optional[str] = None

    # 用户进入房间
    def add_user(self, user: User):
        self.users[user.user_id] = user

    # 用户退出房间
    def remove_user(self, user_id: str):
        if user_id in self.users:
            del self.users[user_id]
            if self.host_user_id == user_id:
                # promote another user to host (simple rule: first in list)
                self.host_user_id = next(iter(self.users), None)

    # 转为房间信息
    def to_room_info(self):
        # return a simplified room dict similar to front-end expectations
        return {
            "room_id": self.room_id,
            "host_user_id": self.host_user_id,
            "user_count": len(self.users),
            "started_at": self.started_at,
            "finished": self.finished,
            "sharing_user_id": self.sharing_user_id,
        }

    # 获取用户列表（按进入时间递增排序）
    def user_list_sorted(self):
        return sorted([u.to_dict() for u in self.users.values()], key=lambda x: x["join_time"]) 


# In-memory store (for demo only)
rooms: Dict[str, Room] = {}


def get_or_create_room(room_id: str, host_user_id: Optional[str] = None) -> Room:
    room = rooms.get(room_id)
    if not room:
        room = Room(room_id=room_id, host_user_id=host_user_id)
        rooms[room_id] = room
    return room


def delete_room(room_id: str):
    rooms.pop(room_id, None)
