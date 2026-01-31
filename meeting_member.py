from typing import Dict, Any
from schemas import UserModel, UserRole, DeviceState, Permission, ShareType, ShareStatus
from utils import current_timestamp_ms


# 用户模型
class MeetingMember:
    def __init__(self, user: UserModel):
        """
        从 UserModel 创建 MeetingMember 实例

        Args:
            user: UserModel 实例
        """
        self._user = user


    @property
    def id(self) -> str:
        return self._user.user_id
    
    @property
    def name(self) -> str:
        return self._user.user_name
    
    @property
    def role(self) -> UserRole:
        return self._user.user_role

    # 进入房间
    def join_room(self, room_id: str, role: UserRole) -> None:
        self._user.join_time = current_timestamp_ms()
        self._user.room_id = room_id
        self._user.user_role = role
    
    # 操纵自己的摄像头
    def operate_camera(self, operate: DeviceState) -> None:
        self._user.camera = operate

    # 操纵自己的麦克风
    def operate_mic(self, operate: DeviceState) -> None:
        self._user.mic = operate
    
    # 更新屏幕共享权限
    def update_share_permission(self, permission: Permission) -> None:
        self._user.share_permission = permission
    
    # 更新麦克风权限
    def update_mic_permission(self, permission: Permission) -> None:
        self._user.operate_mic_permission = permission

    # 开始共享
    def start_share(self, share_type: ShareType) -> None:
        self._user.share_status = ShareStatus.SHARING
        self._user.share_type = share_type

    # 结束共享
    def finish_share(self) -> None:
        self._user.share_status = ShareStatus.NOT_SHARING
        self._user.share_type = ShareType.SCREEN

    # 转换成字典对象
    def to_dict(self) -> Dict[str, Any]:
        return self._user.model_dump()

    # 从字典对象创建用户实例
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MeetingMember':
        """
        从字典创建 MeetingMember 实例

        Args:
            data: 用户数据字典

        Returns:
            MeetingMember 实例
        """
        # 使用 Pydantic 的 model_validate 方法从字典创建 UserModel
        # Pydantic 会自动处理类型转换和验证
        user_model = UserModel.model_validate(data)
        return MeetingMember(user_model)
