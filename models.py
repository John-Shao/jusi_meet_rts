import time
from typing import Dict, Optional
from schemas import *


# 会议用户
class UserModel:
    def __init__(self,
            user_id: str,
            user_name: str,
            user_role: UserRole,
            camera: DeviceState,
            mic: DeviceState,
            join_time: int,
            room_id: str
            ):
        
        self.user = MeetingUser(
            user_id = user_id,
            user_name = user_name,
            user_role = user_role,
            camera = camera,
            mic = mic,
            join_time = join_time,
            room_id = room_id,
        )

    def get_user_id(self):
        return self.user.user_id
    
    def get_user_name(self):
        return self.user.user_name

    def to_dict(self):
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
                 room_id: str,
                 host: UserModel,
                 ):
        
        self.room = MeetingRoomState(
            room_id = room_id,
            host_user_id = host.get_user_id(),
            host_user_name = host.get_user_name(),
            start_time = int(time.time() * 1000),
            activeSpeakers = [host.get_user_id()],
            )
        
        self.users = {host.get_user_id(): host}



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
