from typing import List, Dict, OrderedDict, Any
from schemas import MeetingUser, MeetingRoomState, UserRole
from user_model import UserModel
from utils import current_timestamp_s

# 房间模型
class RoomModel:
    # 构造函数
    def __init__(self,
                 app_id: str,
                 room_id: str,
                 host_user: UserModel,
                 ):
        self._room = MeetingRoomState(
            app_id = app_id,
            room_id = room_id,
            room_name = f"meet_{room_id}",
            host_user_id = host_user.id,
            host_user_name = host_user.name,
            start_time = current_timestamp_s(),
            base_time= current_timestamp_s(),
            )
        self._users = OrderedDict()
        self.add_user(host_user, UserRole.HOST)

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
    def add_user(self, user: UserModel, role: UserRole = UserRole.VISITOR) -> None:
        user.join_room(self._room.room_id, role)
        self._users[user.id] = user

    # 用户退出房间
    def remove_user(self, user_id: str) -> None:
        if user_id in self._users:
            del self._users[user_id]
            # 如果删除的是主持人，将下一个用户设为主持人
            if self._room.host_user_id == user_id:
                self._room.host_user_id = next(iter(self._users), None)
                if self._room.host_user_id:
                    self._room.host_user_name = self._users[self._room.host_user_id].name
                    self._users[self._room.host_user_id].set_user_role(UserRole.HOST)

    # 检查用户是否在房间中
    def user_in_room(self, user_id: str) -> bool:
        return user_id in self._users
    
    # 获取用户
    def get_user(self, user_id: str) -> UserModel:
        return self._users.get(user_id)

    # 转换成字典对象
    def to_dict(self) -> Dict[str, Any]:
        return self._room.model_dump()

    # 从字典对象创建房间实例（不包含用户，用户需要单独加载）
    @staticmethod
    def from_dict(room_data: Dict[str, Any], users_data: Dict[str, Dict[str, Any]] = None) -> 'RoomModel':
        """
        从字典创建RoomModel实例

        Args:
            room_data: 房间数据字典
            users_data: 用户数据字典，格式为 {user_id: user_dict}

        Returns:
            RoomModel实例
        """
        # 首先需要找到主持人用户创建房间
        host_user_id = room_data["host_user_id"]

        # 如果没有提供用户数据，创建一个临时主持人用户
        if not users_data or host_user_id not in users_data:
            from schemas import DeviceState, SilenceState
            host_user = UserModel(
                user_id=host_user_id,
                user_name=room_data.get("host_user_name", ""),
                device_id="",
                camera=DeviceState.OPEN,
                mic=DeviceState.OPEN,
                is_silence=SilenceState.NOT_SILENT,
            )
        else:
            host_user = UserModel.from_dict(users_data[host_user_id])

        # 创建房间实例
        room = RoomModel(
            app_id=room_data["app_id"],
            room_id=room_data["room_id"],
            host_user=host_user,
        )

        # 恢复房间状态
        room._room.room_name = room_data.get("room_name", f"meet_{room_data['room_id']}")
        room._room.room_mic_status = room_data.get("room_mic_status", 1)
        room._room.operate_self_mic_permission = room_data.get("operate_self_mic_permission", 1)
        room._room.share_status = room_data.get("share_status", 0)
        room._room.share_type = room_data.get("share_type", 0)
        room._room.share_user_id = room_data.get("share_user_id", "")
        room._room.share_user_name = room_data.get("share_user_name", "")
        room._room.start_time = room_data.get("start_time", 0)
        room._room.base_time = room_data.get("base_time", 0)
        room._room.record_status = room_data.get("record_status", 0)
        room._room.record_start_time = room_data.get("record_start_time", 0)
        room._room.status = room_data.get("status", 1)

        # 添加其他用户（除了主持人，因为主持人已经在构造函数中添加了）
        if users_data:
            for user_id, user_dict in users_data.items():
                if user_id != host_user_id:
                    user = UserModel.from_dict(user_dict)
                    room._users[user_id] = user

        return room

    # 获取用户字典（用于序列化到Redis）
    @property
    def users(self) -> OrderedDict:
        return self._users

    # 获取用户列表
    def get_user_list(self) -> List[Dict[str, Any]]:
        return [u.to_dict() for u in self._users.values()]
