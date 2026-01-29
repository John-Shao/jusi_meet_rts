from typing import Dict
from user_model import UserModel
from room_model import RoomModel
from schemas import *
from redis_client import redis_client


class RtsService:
    def __init__(self):
        self._rooms: Dict[str, RoomModel] = {}  # 内存缓存，配合Redis持久化存储

    # 同步房间到Redis
    def _sync_room_to_redis(self, room_id: str) -> None:
        """将房间数据同步到Redis"""
        if room_id in self._rooms:
            room = self._rooms[room_id]
            # 保存房间信息
            redis_client.set_room(room_id, room.to_dict())
            # 保存用户信息
            users_data = {user_id: user.to_dict() for user_id, user in room.users.items()}
            redis_client.set_room_users(room_id, users_data)

    # 从Redis加载房间
    def _load_room_from_redis(self, room_id: str) -> RoomModel:
        """从Redis加载房间数据到内存"""
        room_data = redis_client.get_room(room_id)
        if room_data:
            users_data = redis_client.get_room_users(room_id)
            room = RoomModel.from_dict(room_data, users_data)
            self._rooms[room_id] = room
            return room
        return None

    # 获取房间
    async def get_room(self, room_id: str) -> RoomModel:
        # 先从内存获取
        if room_id in self._rooms:
            return self._rooms[room_id]
        # 内存中没有，尝试从Redis加载
        return self._load_room_from_redis(room_id)

    # 获取房间内的用户列表
    async def get_room_users(self, room_id: str) -> List[UserModel]:
        # 先从内存获取
        if room_id in self._rooms:
            room = self._rooms[room_id]
        else:
            # 尝试从Redis加载
            room = self._load_room_from_redis(room_id)
        return room.get_user_list() if room else []

    # 用户进入房间
    async def join_room(self, app_id: str, user: UserModel, room_id: str) -> RoomModel:
        # 先尝试从内存获取
        if room_id not in self._rooms:
            # 尝试从Redis加载
            room = self._load_room_from_redis(room_id)
            if not room:
                # Redis中也没有，创建新房间
                room = RoomModel(app_id=app_id, room_id=room_id, host_user=user)
                self._rooms[room_id] = room
            else:
                # 从Redis加载成功，添加用户
                room.add_user(user)
        else:
            self._rooms[room_id].add_user(user)

        # 同步到Redis
        self._sync_room_to_redis(room_id)
        return self._rooms[room_id]

    # 用户离开房间
    async def leave_room(self, user_id: str, room_id: str) -> None:
        # 先确保房间在内存中
        if room_id not in self._rooms:
            self._load_room_from_redis(room_id)

        if room_id in self._rooms:
            room = self._rooms[room_id]
            room.remove_user(user_id)
            if room.user_count == 0:
                # 房间没有用户了，从内存和Redis中删除
                self._rooms.pop(room_id)
                redis_client.delete_room(room_id)
            else:
                # 同步到Redis
                self._sync_room_to_redis(room_id)

    # 用户关闭房间
    async def finish_room(self, user_id: str, room_id: str) -> None:
        # 先确保房间在内存中
        if room_id not in self._rooms:
            self._load_room_from_redis(room_id)

        assert room_id in self._rooms, "房间不存在"
        assert self._rooms[room_id].host_uid == user_id, "只允许主持人关闭房间"

        # 从内存和Redis中删除
        self._rooms.pop(room_id)
        redis_client.delete_room(room_id)

    # 操作自己的摄像头
    async def operate_self_camera(self, user_id: str, room_id: str, operate: DeviceState) -> None:
        # 先确保房间在内存中
        if room_id not in self._rooms:
            self._load_room_from_redis(room_id)
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        user.operate_camera(operate)
        # 同步到Redis
        self._sync_room_to_redis(room_id)

    # 操作自己的麦克风
    async def operate_self_mic(self, user_id: str, room_id: str, operate: DeviceState) -> None:
        # 先确保房间在内存中
        if room_id not in self._rooms:
            self._load_room_from_redis(room_id)
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        user.operate_mic(operate)
        # 同步到Redis
        self._sync_room_to_redis(room_id)

    # 操作其他用户的摄像头
    async def operate_other_camera(self, user_id: str, room_id: str, operate_user_id: str, operate: DeviceState) -> None:
        if room_id not in self._rooms:
            self._load_room_from_redis(room_id)
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "操作用户不在房间内"
        user = room.get_user(user_id)
        assert user.role == UserRole.HOST, "只有主持人才能操作其他用户的摄像头"
        assert room.user_in_room(operate_user_id), "被操作用户不在房间内"
        operate_user = room.get_user(operate_user_id)
        operate_user.operate_camera(operate)
        self._sync_room_to_redis(room_id)

    # 操作其他用户的麦克风
    async def operate_other_mic(self, user_id: str, room_id: str, operate_user_id: str, operate: DeviceState) -> None:
        if room_id not in self._rooms:
            self._load_room_from_redis(room_id)
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "操作用户不在房间内"
        user = room.get_user(user_id)
        assert user.role == UserRole.HOST, "只有主持人才能操作其他用户的麦克风"
        assert room.user_in_room(operate_user_id), "被操作用户不在房间内"
        operate_user = room.get_user(operate_user_id)
        operate_user.operate_mic(operate)
        self._sync_room_to_redis(room_id)

    # 操作其他用户的屏幕共享权限
    async def operate_other_share_permission(self, user_id: str, room_id: str, operate_user_id: str, operate: Permission) -> None:
        if room_id not in self._rooms:
            self._load_room_from_redis(room_id)
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "操作用户不在房间内"
        user = room.get_user(user_id)
        assert user.role == UserRole.HOST, "只有主持人才能操作其他用户的屏幕共享权限"
        assert room.user_in_room(operate_user_id), "被操作用户不在房间内"
        operate_user = room.get_user(operate_user_id)
        operate_user.update_share_permission(operate)
        self._sync_room_to_redis(room_id)

    # 操作自己的麦克风权限申请
    async def operate_self_mic_apply(self, user_id: str, room_id: str, operate: Permission) -> None:
        if room_id not in self._rooms:
            self._load_room_from_redis(room_id)
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        user.update_mic_permission(operate)
        self._sync_room_to_redis(room_id)
    
    # 开始共享
    async def start_share(self, user_id: str, room_id: str, share_type: ShareType) -> None:
        if room_id not in self._rooms:
            self._load_room_from_redis(room_id)
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        user.start_share(share_type)
        self._sync_room_to_redis(room_id)

    # 结束共享
    async def finish_share(self, user_id: str, room_id: str) -> None:
        if room_id not in self._rooms:
            self._load_room_from_redis(room_id)
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        user.finish_share()
        self._sync_room_to_redis(room_id)

    # 申请共享权限
    async def share_permission_apply(self, user_id: str, room_id: str) -> None:
        if room_id not in self._rooms:
            self._load_room_from_redis(room_id)
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        user.update_share_permission(Permission.HAS_PERMISSION)
        self._sync_room_to_redis(room_id)

    # 操作所有用户的麦克风
    async def operate_all_mic(self, user_id: str, room_id: str, operate_self_mic_permission: Permission, operate: DeviceState) -> None:
        if room_id not in self._rooms:
            self._load_room_from_redis(room_id)
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        assert user.role == UserRole.HOST, "只有主持人才能操作所有用户的麦克风"
        for other_user in room.users.values():
            if other_user.id != user_id:
                other_user.operate_mic(operate)
                other_user.update_mic_permission(operate_self_mic_permission)
        self._sync_room_to_redis(room_id)

    # 观众请求麦克风使用权限后, 主持人答复
    async def operate_self_mic_permit(self, user_id: str, room_id: str, apply_user_id: str, permit: Permission) -> None:
        if room_id not in self._rooms:
            self._load_room_from_redis(room_id)
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        assert user.role == UserRole.HOST, "只有主持人才能审批其他用户的麦克风权限申请"
        assert room.user_in_room(apply_user_id), "申请用户不在房间内"
        apply_user = room.get_user(apply_user_id)
        apply_user.update_mic_permission(permit)
        self._sync_room_to_redis(room_id)

    # 操作自己的屏幕共享权限申请
    async def operate_self_share_permission_permit(self, user_id: str, room_id: str, apply_user_id: str, permit: Permission) -> None:
        if room_id not in self._rooms:
            self._load_room_from_redis(room_id)
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        assert user.role == UserRole.HOST, "只有主持人才能审批其他用户的屏幕共享权限申请"
        assert room.user_in_room(apply_user_id), "申请用户不在房间内"
        apply_user = room.get_user(apply_user_id)
        apply_user.update_share_permission(permit)
        self._sync_room_to_redis(room_id)

# 创建服务实例
service = RtsService()
