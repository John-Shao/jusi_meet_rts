from meeting_member import MeetingMember
from meeting_room import MeetingRoom
from schemas import *
from redis_client import redis_client
from utils import current_timestamp_s
from config import settings


class RtsService:
    def __init__(self):
        pass  # 纯Redis存储，不需要内存缓存

    # 从Redis获取房间
    def _get_room_from_redis(self, room_id: str) -> MeetingRoom:
        """从Redis加载房间数据"""
        room_data = redis_client.get_room(room_id)
        if room_data:
            users_data = redis_client.get_room_users(room_id)
            # 将字典格式的用户数据转换为列表格式
            user_list = list(users_data.values()) if users_data else None
            return MeetingRoom.from_dict(room_data, user_list)
        return None

    # 保存房间到Redis
    def _save_room_to_redis(self, room_id: str, room: MeetingRoom) -> None:
        """将房间数据保存到Redis"""
        room_dict = room.to_dict()
        # 保存房间信息
        redis_client.set_room(room_id, room_dict["room_data"])
        # 保存用户信息 - 将列表转换为字典格式
        users_data = {user_dict["user_id"]: user_dict for user_dict in room_dict["user_list"]}
        redis_client.set_room_users(room_id, users_data)

    # 获取房间
    async def get_room(self, room_id: str) -> MeetingRoom:
        return self._get_room_from_redis(room_id)

    # 获取房间内的用户列表
    async def get_room_users(self, room_id: str) -> List[MeetingMember]:
        room = self._get_room_from_redis(room_id)
        return room.get_all_users() if room else []

    # 创建/预定房间
    async def create_room(self, room_id: str, host_user_id: str, host_user_name: str, room_name: str = None) -> bool:
        # 检查房间是否已存在
        if redis_client.exists_room(room_id):
            return False

        # 创建房间
        room_state = RoomState(
            app_id=settings.rtc_app_id,
            room_id=room_id,
            room_name=room_name or room_id,
            host_user_id=host_user_id,
            host_user_name=host_user_name,
            start_time=current_timestamp_s(),
            base_time=current_timestamp_s(),
        )
        redis_client.set_room(room_id, room_state.model_dump())
        return True

    # 取消会议
    async def cancel_meeting(self, room_id: str, user_id: str) -> tuple[int, str]:
        """
        取消会议

        Args:
            room_id: 房间ID
            user_id: 操作用户ID

        Returns:
            (状态码, 消息)
            - 200: 成功
            - 403: 权限不足
            - 404: 房间不存在
            - 409: 会议中有人
        """
        # 检查房间是否存在
        room_data = redis_client.get_room(room_id)
        if not room_data:
            return 404, "房间不存在"

        # 验证是否是主持人
        room_state = RoomState.model_validate(room_data)
        if room_state.host_user_id != user_id:
            return 403, "只有主持人可以取消会议"

        # 检查房间是否有人
        user_count = redis_client.get_room_user_count(room_id)
        if user_count > 0:
            return 409, "会议中有人，无法取消"

        # 删除房间
        redis_client.delete_room(room_id)
        return 200, "会议已取消"

    # 查询用户的所有会议
    async def get_user_meetings(self, user_id: str) -> List[Dict[str, Any]]:
        meetings = []
        all_room_ids = redis_client.get_all_room_ids()

        for room_id in all_room_ids:
            room_data = redis_client.get_room(room_id)
            if room_data:
                room_state = RoomState.model_validate(room_data)
                # 只返回该用户作为主持人的会议
                if room_state.host_user_id == user_id:
                    user_count = redis_client.get_room_user_count(room_id)
                    meetings.append({
                        "room_id": room_state.room_id,
                        "room_name": room_state.room_name,
                        "host_user_id": room_state.host_user_id,
                        "host_user_name": room_state.host_user_name,
                        "start_time": room_state.start_time,
                        "user_count": user_count,  # 会议中的用户数量
                    })

        return meetings

    # 检查房间是否存在
    async def check_room_exists(self, room_id: str) -> bool:
        """
        检查房间是否存在

        Args:
            room_id: 房间ID

        Returns:
            房间是否存在
        """
        return redis_client.exists_room(room_id)

    # 检查用户是否在房间中
    async def check_user_in_room(self, room_id: str, user_id: str) -> int:
        """
        检查用户是否在房间中

        Args:
            room_id: 房间ID
            user_id: 用户ID

        Returns:
            -1: 房间不存在
            0: 用户不在房间中
            1: 用户在房间中
        """
        # 检查房间是否存在
        if not redis_client.exists_room(room_id):
            return -1

        # 检查用户是否在房间中
        user_data = redis_client.get_room_user(room_id, user_id)
        return 1 if user_data is not None else 0

    # 用户进入房间
    async def join_room(self, user: MeetingMember, room_id: str) -> MeetingRoom:
        # 检查房间是否存在
        room = self._get_room_from_redis(room_id)
        if room:
            # 使用 MeetingRoom 的业务逻辑来添加用户（自动判断角色）
            room.add_user(user)
            # 保存用户到 Redis（细粒度操作）
            redis_client.add_room_user(room_id, user.id, user.to_dict())

        # 返回完整房间数据（加载所有用户）
        return room

    # 用户离开房间
    async def leave_room(self, user_id: str, room_id: str) -> None:
        # 细粒度操作：只删除单个用户
        if redis_client.exists_room(room_id):
            redis_client.remove_room_user(room_id, user_id)
            if redis_client.get_room_user_count(room_id) == 0:
                # 房间没有用户了，从Redis中删除
                redis_client.delete_room(room_id)

    # 用户关闭房间
    async def finish_room(self, user_id: str, room_id: str) -> None:
        # 细粒度操作：只检查房间信息
        room_data = redis_client.get_room(room_id)
        if room_data:
            room_state = RoomState.model_validate(room_data)
            assert room_state.host_user_id == user_id, "只允许主持人关闭房间"
            # 从Redis中删除
            redis_client.delete_room(room_id)

    # 操作自己的摄像头
    async def operate_self_camera(self, user_id: str, room_id: str, operate: DeviceState) -> None:
        # 细粒度操作：只读写单个用户
        assert redis_client.exists_room(room_id), "房间不存在"
        user_data = redis_client.get_room_user(room_id, user_id)
        assert user_data, "用户不在房间内"
        user = MeetingMember.from_dict(user_data)
        user.operate_camera(operate)
        redis_client.set_room_user(room_id, user_id, user.to_dict())

    # 操作自己的麦克风
    async def operate_self_mic(self, user_id: str, room_id: str, operate: DeviceState) -> None:
        # 细粒度操作：只读写单个用户
        assert redis_client.exists_room(room_id), "房间不存在"
        user_data = redis_client.get_room_user(room_id, user_id)
        assert user_data, "用户不在房间内"
        user = MeetingMember.from_dict(user_data)
        user.operate_mic(operate)
        redis_client.set_room_user(room_id, user_id, user.to_dict())

    # 操作其他用户的摄像头
    async def operate_other_camera(self, user_id: str, room_id: str, operate_user_id: str, operate: DeviceState) -> None:
        # 细粒度操作：只读写单个用户
        assert redis_client.exists_room(room_id), "房间不存在"
        user_data = redis_client.get_room_user(room_id, user_id)
        assert user_data, "操作用户不在房间内"
        user = MeetingMember.from_dict(user_data)
        assert user.role == UserRole.HOST, "只有主持人才能操作其他用户的摄像头"

        operate_user_data = redis_client.get_room_user(room_id, operate_user_id)
        assert operate_user_data, "被操作用户不在房间内"
        operate_user = MeetingMember.from_dict(operate_user_data)
        operate_user.operate_camera(operate)
        redis_client.set_room_user(room_id, operate_user_id, operate_user.to_dict())

    # 操作其他用户的麦克风
    async def operate_other_mic(self, user_id: str, room_id: str, operate_user_id: str, operate: DeviceState) -> None:
        # 细粒度操作：只读写单个用户
        assert redis_client.exists_room(room_id), "房间不存在"
        user_data = redis_client.get_room_user(room_id, user_id)
        assert user_data, "操作用户不在房间内"
        user = MeetingMember.from_dict(user_data)
        assert user.role == UserRole.HOST, "只有主持人才能操作其他用户的麦克风"

        operate_user_data = redis_client.get_room_user(room_id, operate_user_id)
        assert operate_user_data, "被操作用户不在房间内"
        operate_user = MeetingMember.from_dict(operate_user_data)
        operate_user.operate_mic(operate)
        redis_client.set_room_user(room_id, operate_user_id, operate_user.to_dict())

    # 操作其他用户的屏幕共享权限
    async def operate_other_share_permission(self, user_id: str, room_id: str, operate_user_id: str, operate: Permission) -> None:
        # 细粒度操作：只读写单个用户
        assert redis_client.exists_room(room_id), "房间不存在"
        user_data = redis_client.get_room_user(room_id, user_id)
        assert user_data, "操作用户不在房间内"
        user = MeetingMember.from_dict(user_data)
        assert user.role == UserRole.HOST, "只有主持人才能操作其他用户的屏幕共享权限"

        operate_user_data = redis_client.get_room_user(room_id, operate_user_id)
        assert operate_user_data, "被操作用户不在房间内"
        operate_user = MeetingMember.from_dict(operate_user_data)
        operate_user.update_share_permission(operate)
        redis_client.set_room_user(room_id, operate_user_id, operate_user.to_dict())

    # 操作自己的麦克风权限申请
    async def operate_self_mic_apply(self, user_id: str, room_id: str, operate: Permission) -> None:
        # 细粒度操作：只读写单个用户
        assert redis_client.exists_room(room_id), "房间不存在"
        user_data = redis_client.get_room_user(room_id, user_id)
        assert user_data, "用户不在房间内"
        user = MeetingMember.from_dict(user_data)
        user.update_mic_permission(operate)
        redis_client.set_room_user(room_id, user_id, user.to_dict())
    
    # 开始共享
    async def start_share(self, user_id: str, room_id: str, share_type: ShareType) -> None:
        # 细粒度操作：只读写单个用户
        assert redis_client.exists_room(room_id), "房间不存在"
        user_data = redis_client.get_room_user(room_id, user_id)
        assert user_data, "用户不在房间内"
        user = MeetingMember.from_dict(user_data)
        user.start_share(share_type)
        redis_client.set_room_user(room_id, user_id, user.to_dict())

    # 结束共享
    async def finish_share(self, user_id: str, room_id: str) -> None:
        # 细粒度操作：只读写单个用户
        assert redis_client.exists_room(room_id), "房间不存在"
        user_data = redis_client.get_room_user(room_id, user_id)
        assert user_data, "用户不在房间内"
        user = MeetingMember.from_dict(user_data)
        user.finish_share()
        redis_client.set_room_user(room_id, user_id, user.to_dict())

    # 申请共享权限
    async def share_permission_apply(self, user_id: str, room_id: str) -> None:
        # 细粒度操作：只读写单个用户
        assert redis_client.exists_room(room_id), "房间不存在"
        user_data = redis_client.get_room_user(room_id, user_id)
        assert user_data, "用户不在房间内"
        user = MeetingMember.from_dict(user_data)
        user.update_share_permission(Permission.HAS_PERMISSION)
        redis_client.set_room_user(room_id, user_id, user.to_dict())

    # 操作所有用户的麦克风
    async def operate_all_mic(self, user_id: str, room_id: str, operate_self_mic_permission: Permission, operate: DeviceState) -> None:
        # 批量操作：读写所有用户
        assert redis_client.exists_room(room_id), "房间不存在"
        user_data = redis_client.get_room_user(room_id, user_id)
        assert user_data, "用户不在房间内"
        user = MeetingMember.from_dict(user_data)
        assert user.role == UserRole.HOST, "只有主持人才能操作所有用户的麦克风"

        # 批量读取所有用户
        all_users_data = redis_client.get_room_users(room_id)
        for other_user_id, other_user_data in all_users_data.items():
            if other_user_id != user_id:
                other_user = MeetingMember.from_dict(other_user_data)
                other_user.operate_mic(operate)
                other_user.update_mic_permission(operate_self_mic_permission)
                all_users_data[other_user_id] = other_user.to_dict()

        # 批量保存所有用户
        redis_client.set_room_users(room_id, all_users_data)

    # 观众请求麦克风使用权限后, 主持人答复
    async def operate_self_mic_permit(self, user_id: str, room_id: str, apply_user_id: str, permit: Permission) -> None:
        # 细粒度操作：只读写单个用户
        assert redis_client.exists_room(room_id), "房间不存在"
        user_data = redis_client.get_room_user(room_id, user_id)
        assert user_data, "用户不在房间内"
        user = MeetingMember.from_dict(user_data)
        assert user.role == UserRole.HOST, "只有主持人才能审批其他用户的麦克风权限申请"

        apply_user_data = redis_client.get_room_user(room_id, apply_user_id)
        assert apply_user_data, "申请用户不在房间内"
        apply_user = MeetingMember.from_dict(apply_user_data)
        apply_user.update_mic_permission(permit)
        redis_client.set_room_user(room_id, apply_user_id, apply_user.to_dict())

    # 操作自己的屏幕共享权限申请
    async def operate_self_share_permission_permit(self, user_id: str, room_id: str, apply_user_id: str, permit: Permission) -> None:
        # 细粒度操作：只读写单个用户
        assert redis_client.exists_room(room_id), "房间不存在"
        user_data = redis_client.get_room_user(room_id, user_id)
        assert user_data, "用户不在房间内"
        user = MeetingMember.from_dict(user_data)
        assert user.role == UserRole.HOST, "只有主持人才能审批其他用户的屏幕共享权限申请"

        apply_user_data = redis_client.get_room_user(room_id, apply_user_id)
        assert apply_user_data, "申请用户不在房间内"
        apply_user = MeetingMember.from_dict(apply_user_data)
        apply_user.update_share_permission(permit)
        redis_client.set_room_user(room_id, apply_user_id, apply_user.to_dict())

# 创建服务实例
rtsService = RtsService()
