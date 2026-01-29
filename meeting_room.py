from typing import List, Dict, OrderedDict, Any
from schemas import UserModel, RoomState, UserRole
from meeting_member import MeetingMember

# 房间模型
class MeetingRoom:
    # 构造函数
    def __init__(self, room: RoomState):
        self._room = room
        self._users = OrderedDict()

    # 析构函数
    def __del__(self):
        self._users.clear()

    # 主持人ID
    @property
    def host_uid(self) -> str:
        return self._room.host_user_id
    
    # 获取用户数量
    @property
    def user_count(self) -> int:
        return len(self._users)

    # 用户进入房间
    def add_user(self, user: MeetingMember) -> None:
        # 如果用户ID与房间主持人ID匹配，则为主持人
        if self._room.host_user_id and user.id == self._room.host_user_id:
            role = UserRole.HOST
        else:
            role = UserRole.VISITOR

        user.join_room(self._room.room_id, role)
        self._users[user.id] = user

    # 用户退出房间
    def remove_user(self, user_id: str) -> None:
        if user_id in self._users:
            del self._users[user_id]

    # 检查用户是否在房间中
    def user_in_room(self, user_id: str) -> bool:
        return user_id in self._users
    
    # 获取用户
    def get_user(self, user_id: str) -> MeetingMember:
        return self._users.get(user_id)

    # 转换成字典对象
    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_data": self._room.model_dump(),
            "user_list": [u.to_dict() for u in self._users.values()]
        }

    # 从字典对象创建房间实例
    @staticmethod
    def from_dict(room_data: Dict[str, Any], user_list: List[Dict[str, Any]] = None) -> 'MeetingRoom':
        # 使用 Pydantic 的 model_validate 从字典创建 RoomState
        room_state = RoomState.model_validate(room_data)
        # 创建房间实例
        room = MeetingRoom(room_state)
        # 添加所有用户
        if user_list:
            for user_dict in user_list:
                user = MeetingMember.from_dict(user_dict)
                room._users[user.id] = user
        return room

    # 获取所有用户对象（用于遍历操作）
    def get_all_users(self) -> List[MeetingMember]:
        return list(self._users.values())
