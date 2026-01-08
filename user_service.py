from typing import Optional
from models import *
import uuid
import time

class UserService:
    def __init__(self):
        self.users = {}  # 简单内存存储，实际项目中使用数据库
    
    async def create_user(self, user_id: str, user_name: str, camera: DeviceState, 
                         mic: DeviceState, is_silence: Optional[Silence] = None,
                         device_id: str = None) -> MeetingUser:
        # 如果没有提供user_id，则生成一个
        if not user_id:
            user_id = str(uuid.uuid4())
        
        user = MeetingUser(
            user_id=user_id,
            user_name=user_name,
            user_role=UserRole.VISITOR,  # 默认访客，第一个进房的用户会被设置为主持人
            camera=camera,
            mic=mic,
            join_time=int(time.time()),
            share_permission=Permission.NO_PERMISSION,
            is_silence=is_silence
        )
        
        self.users[user_id] = user
        return user
    
    async def get_user(self, user_id: str) -> Optional[MeetingUser]:
        return self.users.get(user_id)
    
    async def update_camera_state(self, user_id: str, state: DeviceState):
        if user_id in self.users:
            self.users[user_id].camera = state
    
    async def update_mic_state(self, user_id: str, state: DeviceState):
        if user_id in self.users:
            self.users[user_id].mic = state
    
    async def update_share_permission(self, user_id: str, permission: Permission):
        if user_id in self.users:
            self.users[user_id].share_permission = permission
    
    async def start_share(self, user_id: str, share_type: ShareType):
        if user_id in self.users:
            self.users[user_id].share_status = 1
            self.users[user_id].share_type = share_type
    
    async def stop_share(self, user_id: str):
        if user_id in self.users:
            self.users[user_id].share_status = 0
            self.users[user_id].share_type = None
