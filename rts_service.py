from typing import Dict, List, Optional
from models import Room, User
from user_service import UserService
from utils import generate_rtc_token, generate_whiteboard_token
import time

class RtsService:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}  # 简单内存存储，实际项目中使用数据库

    # 用户进入房间
    async def join_room(self, user_id: str):
        # 简化处理，实际应更新房间状态和用户列表
        pass
    
    # 用户退出房间
    async def leave_room(self, user_id: str):
        # 简化处理，实际应更新房间状态和用户列表
        pass
    
    # 结束会议
    async def finish_room(self, room_id: str):
        if room_id in self.rooms:
            self.rooms[room_id].finished_at = int(time.time() * 1000)
            self.rooms[room_id].finished = True

    # 获取房间
    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id, None)

    # 创建房间
    def create_room(self, room_id: str, host_uid: Optional[str] = None) -> Room:
        room = Room(room_id=room_id, host_uid=host_uid)
        self.rooms[room_id] = room
        return room

    # 删除房间
    def delete_room(self, room_id: str):
        self.rooms.pop(room_id, None)


# 创建服务实例
service = RtsService()
