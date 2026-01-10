from typing import Dict
from user_model import UserModel
from room_model import RoomModel

class RtsService:
    def __init__(self):
        self._rooms: Dict[str, RoomModel] = {}  # 简单内存存储，实际项目中使用数据库

    # 用户进入房间
    async def join_room(self, app_id: str, user: UserModel, room_id: str) -> RoomModel:
        if room_id not in self._rooms:
            room = RoomModel(app_id=app_id, room_id=room_id, host_user=user)
            self._rooms[room_id] = room
        else:
            self._rooms[room_id].add_user(user)

        return self._rooms[room_id]


# 创建服务实例
service = RtsService()
