from typing import List, Optional
from models import *
from user_service import UserService
from utils import generate_rtc_token, generate_whiteboard_token
import time

class MeetingService:
    def __init__(self):
        self.rooms = {}  # 简单内存存储，实际项目中使用数据库
        self.user_service = UserService()
    
    async def join_room(self, user: MeetingUser, room_id: str = None, app_id: str = None, 
                        login_token: str = None, request_id: str = None) -> JoinMeetingRoomRes:
            
        if room_id not in self.rooms:
            self.rooms[room_id] = MeetingRoomState(
                room_id=room_id,
                room_name="Meeting Room",
                create_time=int(time.time())
            )
        
        room = self.rooms[room_id]
        
        # 如果是第一个用户，设置为主持人
        if not room.start_time:
            user.user_role = UserRole.HOST
            room.start_time = int(time.time())
            room.status = 1
        else:
            user.user_role = UserRole.VISITOR
        
        # 获取房间用户列表
        user_list = await self.get_room_users(room_id)
        user_list.append(user)
        
        # 生成RTC token
        token = generate_rtc_token(user.user_id, room_id)
        
        # 生成白板相关信息
        wb_room_id = f"wb_{room_id}"
        wb_user_id = f"wb_{user.user_id}"
        wb_token = generate_whiteboard_token(wb_user_id, wb_room_id)
        
        return JoinMeetingRoomRes(
            room=room,
            user=user,
            user_list=user_list,
            token=token,
            wb_room_id=wb_room_id,
            wb_user_id=wb_user_id,
            wb_token=wb_token
        )
    
    async def leave_room(self, user_id: str):
        # 简化处理，实际应更新房间状态和用户列表
        pass
    
    async def finish_room(self, room_id: str):
        if room_id in self.rooms:
            self.rooms[room_id].end_time = int(time.time())
            self.rooms[room_id].status = 2
    
    async def reconnect(self, room_id: str, user_id: str) -> ReconnectRes:
        # 简化处理，实际应从数据库获取房间和用户信息
        room = self.rooms.get(room_id)
        user = await self.user_service.get_user(user_id)
        user_list = await self.get_room_users(room_id)
        
        return ReconnectRes(
            room=room,
            user=user,
            user_list=user_list
        )
    
    async def get_user_list(self, room_id: str) -> GetUserListRes:
        user_list = await self.get_room_users(room_id)
        
        return GetUserListRes(
            user_count=len(user_list),
            user_list=user_list
        )
    
    async def get_room_users(self, room_id: str) -> List[MeetingUser]:
        # 简化处理，实际应从数据库获取
        return []
    
    async def apply_mic_permission(self, user_id: str):
        # 简化处理，实际应记录申请并通知主持人
        pass
    
    async def apply_share_permission(self, user_id: str):
        # 简化处理，实际应记录申请并通知主持人
        pass
    
    async def mute_all(self, room_id: str, operate_self_mic_permission: Permission):
        # 简化处理，实际应更新所有用户的麦克风状态
        pass
    
    async def permit_mic_apply(self, apply_user_id: str, permit: DeviceState):
        # 简化处理，实际应更新用户的麦克风状态并通知用户
        pass
    
    async def permit_share_apply(self, apply_user_id: str, permit: Permission):
        # 简化处理，实际应更新用户的共享权限并通知用户
        pass
