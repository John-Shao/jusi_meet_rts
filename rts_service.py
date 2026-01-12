from typing import Dict
from user_model import UserModel
from room_model import RoomModel
from schemas import *


class RtsService:
    def __init__(self):
        self._rooms: Dict[str, RoomModel] = {}  # 简单内存存储，实际项目中使用数据库

    # 获取房间
    async def get_room(self, room_id: str) -> RoomModel:
        return self._rooms.get(room_id, None)

    # 用户进入房间
    async def join_room(self, app_id: str, user: UserModel, room_id: str) -> RoomModel:
        if room_id not in self._rooms:
            room = RoomModel(app_id=app_id, room_id=room_id, host_user=user)
            self._rooms[room_id] = room
        else:
            self._rooms[room_id].add_user(user)

        return self._rooms[room_id]

    # 用户离开房间
    async def leave_room(self, user_id: str, room_id: str) -> None:
        if room_id in self._rooms:
            room = self._rooms[room_id]
            room.remove_user(user_id)
            if room.user_count == 0:
                self._rooms.pop(room_id)

    # 用户关闭房间
    async def finish_room(self, user_id: str, room_id: str) -> None:
        assert self._rooms[room_id].host_uid == user_id, "只允许主持人关闭房间"
        if room_id in self._rooms:
            self._rooms.pop(room_id)

    # 操作自己的摄像头
    async def operate_self_camera(self, user_id: str, room_id: str, operate: DeviceState) -> None:
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        user.operate_camera(operate)

    # 操作自己的麦克风
    async def operate_self_mic(self, user_id: str, room_id: str, operate: DeviceState) -> None:
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        user.operate_mic(operate)

    # 操作其他用户的摄像头
    async def operate_other_camera(self, user_id: str, room_id: str, operate_user_id: str, operate: DeviceState) -> None:
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "操作用户不在房间内"
        user = room.get_user(user_id)
        assert user.role == UserRole.HOST, "只有主持人才能操作其他用户的摄像头"
        assert room.user_in_room(operate_user_id), "被操作用户不在房间内"
        operate_user = room.get_user(operate_user_id)
        operate_user.operate_camera(operate)

    # 操作其他用户的麦克风
    async def operate_other_mic(self, user_id: str, room_id: str, operate_user_id: str, operate: DeviceState) -> None:
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "操作用户不在房间内"
        user = room.get_user(user_id)
        assert user.role == UserRole.HOST, "只有主持人才能操作其他用户的麦克风"
        assert room.user_in_room(operate_user_id), "被操作用户不在房间内"
        operate_user = room.get_user(operate_user_id)
        operate_user.operate_mic(operate)

    # 操作其他用户的屏幕共享权限
    async def operate_other_share_permission(self, user_id: str, room_id: str, operate_user_id: str, operate: Permission) -> None:
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "操作用户不在房间内"
        user = room.get_user(user_id)
        assert user.role == UserRole.HOST, "只有主持人才能操作其他用户的屏幕共享权限"
        assert room.user_in_room(operate_user_id), "被操作用户不在房间内"
        operate_user = room.get_user(operate_user_id)
        operate_user.update_share_permission(operate)

    # 操作自己的麦克风权限申请
    async def operate_self_mic_apply(self, user_id: str, room_id: str, operate: Permission) -> None:
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        user.update_mic_permission(operate)
    
    # 开始共享
    async def start_share(self, user_id: str, room_id: str, share_type: ShareType) -> None:
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        user.start_share(share_type)

    # 结束共享
    async def finish_share(self, user_id: str, room_id: str) -> None:
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        user.finish_share()

    # 申请共享权限
    async def share_permission_apply(self, user_id: str, room_id: str) -> None:
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        user.update_share_permission(Permission.HAS_PERMISSION)

    # 操作所有用户的麦克风
    async def operate_all_mic(self, user_id: str, room_id: str, operate_self_mic_permission: Permission, operate: DeviceState) -> None:
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        assert user.role == UserRole.HOST, "只有主持人才能操作所有用户的麦克风"
        for other_user in room.users.values():
            if other_user.id != user_id:
                other_user.operate_mic(operate)
                other_user.update_mic_permission(operate_self_mic_permission)

    # 观众请求麦克风使用权限后, 主持人答复
    async def operate_self_mic_permit(self, user_id: str, room_id: str, apply_user_id: str, permit: Permission) -> None:
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        assert user.role == UserRole.HOST, "只有主持人才能审批其他用户的麦克风权限申请"
        assert room.user_in_room(apply_user_id), "申请用户不在房间内"
        apply_user = room.get_user(apply_user_id)
        apply_user.update_mic_permission(permit)
    
    # 操作自己的屏幕共享权限申请
    async def operate_self_share_permission_permit(self, user_id: str, room_id: str, apply_user_id: str, permit: Permission) -> None:
        assert room_id in self._rooms, "房间不存在"
        room = self._rooms[room_id]
        assert room.user_in_room(user_id), "用户不在房间内"
        user = room.get_user(user_id)
        assert user.role == UserRole.HOST, "只有主持人才能审批其他用户的屏幕共享权限申请"
        assert room.user_in_room(apply_user_id), "申请用户不在房间内"
        apply_user = room.get_user(apply_user_id)
        apply_user.update_share_permission(permit)

# 创建服务实例
service = RtsService()
