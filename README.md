## 项目结构

```
meeting_server/
├── app/
│   ├── __init__.py
│   ├── main.py              # 主程序入口
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   ├── rts.py           # RTS相关模型
│   │   ├── meeting.py       # 会议相关模型
│   │   └── user.py          # 用户相关模型
│   ├── routers/             # API路由
│   │   ├── __init__.py
│   │   └── rts.py           # RTS消息处理路由
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   ├── meeting_service.py  # 会议服务
│   │   └── user_service.py     # 用户服务
│   └── utils/               # 工具函数
│       ├── __init__.py
│       └── volcengine_utils.py  # 火山引擎工具
├── config.py                # 配置文件
├── requirements.txt         # 依赖列表
└── run.sh                   # 启动脚本
```

## 依赖安装

```bash
pip install fastapi uvicorn pydantic python-dotenv volcengine
```

## 配置文件 (config.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # FastAPI配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Meeting Room Server"
    DEBUG: bool = True
    
    # 火山引擎配置
    VOLC_ACCESS_KEY: str
    VOLC_SECRET_KEY: str
    VOLC_REGION: str = "cn-beijing"
    
    # RTS配置
    RTS_APP_ID: str
    RTS_APP_KEY: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## 数据模型 (app/models/rts.py)

```python
from enum import Enum
from pydantic import BaseModel
from typing import Optional, List, Dict

# 设备状态枚举
class DeviceState(str, Enum):
    CLOSED = "0"
    OPEN = "1"

# 权限枚举
class Permission(str, Enum):
    NO_PERMISSION = "0"
    HAS_PERMISSION = "1"

# 共享类型枚举
class ShareType(str, Enum):
    SCREEN = "0"
    BOARD = "1"

# 静默状态枚举
class Silence(str, Enum):
    NOT_SILENT = "0"
    SILENCE = "1"

# 用户角色枚举
class UserRole(str, Enum):
    VISITOR = "0"
    HOST = "1"

# RTS消息基础模型
class RTSMessage(BaseModel):
    event_name: str
    content: Dict

# 响应模型
class BaseResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Dict] = None
```

## 会议相关模型 (app/models/meeting.py)

```python
from pydantic import BaseModel
from typing import Optional, List
from .rts import *

# 会议房间状态
class MeetingRoomState(BaseModel):
    room_id: str
    room_name: Optional[str] = None
    create_time: int
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    status: int = 0  # 0: 未开始, 1: 进行中, 2: 已结束

# 会议用户信息
class MeetingUser(BaseModel):
    user_id: str
    user_name: str
    user_role: UserRole
    camera: DeviceState
    mic: DeviceState
    join_time: int
    share_permission: Permission
    share_status: int = 0  # 0: 未共享, 1: 共享中
    share_type: Optional[ShareType] = None
    is_silence: Optional[Silence] = None
    isLocal: Optional[bool] = False

# 加入房间响应
class JoinMeetingRoomRes(BaseModel):
    room: MeetingRoomState
    user: MeetingUser
    user_list: List[MeetingUser]
    token: str
    wb_room_id: str
    wb_user_id: str
    wb_token: str

# 重连响应
class ReconnectRes(BaseModel):
    room: MeetingRoomState
    user: MeetingUser
    user_list: List[MeetingUser]

# 获取用户列表响应
class GetUserListRes(BaseModel):
    user_count: int
    user_list: List[MeetingUser]
```

## API路由 (app/routers/rts.py)

```python
from fastapi import APIRouter, Depends
from typing import Optional
from ..models.rts import *
from ..models.meeting import *
from ..services.meeting_service import MeetingService
from ..services.user_service import UserService

router = APIRouter()

@router.post("/rts/message", response_model=BaseResponse)
async def handle_rts_message(message: RTSMessage):
    event_name = message.event_name
    content = message.content
    
    # 根据不同的事件名称处理不同的消息
    if event_name == "vcJoinRoom":
        return await handle_join_room(content)
    elif event_name == "vcLeaveRoom":
        return await handle_leave_room(content)
    elif event_name == "vcFinishRoom":
        return await handle_finish_room(content)
    elif event_name == "vcResync":
        return await handle_resync(content)
    elif event_name == "vcGetUserList":
        return await handle_get_user_list(content)
    elif event_name == "vcOperateSelfCamera":
        return await handle_operate_self_camera(content)
    elif event_name == "vcOperateSelfMic":
        return await handle_operate_self_mic(content)
    elif event_name == "vcOperateSelfMicApply":
        return await handle_operate_self_mic_apply(content)
    elif event_name == "vcStartShare":
        return await handle_start_share(content)
    elif event_name == "vcFinishShare":
        return await handle_finish_share(content)
    elif event_name == "vcSharePermissionApply":
        return await handle_share_permission_apply(content)
    elif event_name == "vcOperateOtherCamera":
        return await handle_operate_other_camera(content)
    elif event_name == "vcOperateOtherMic":
        return await handle_operate_other_mic(content)
    elif event_name == "vcOperateOtherSharePermission":
        return await handle_operate_other_share_permission(content)
    elif event_name == "vcOperateAllMic":
        return await handle_operate_all_mic(content)
    elif event_name == "vcOperateSelfMicPermit":
        return await handle_operate_self_mic_permit(content)
    elif event_name == "vcSharePermissionPermit":
        return await handle_share_permission_permit(content)
    else:
        return BaseResponse(code=400, message=f"Unknown event: {event_name}")

# 处理加入房间
async def handle_join_room(content: Dict):
    meeting_service = MeetingService()
    user_service = UserService()
    
    # 解析参数
    user_name = content.get("user_name")
    camera = DeviceState(content.get("camera", "0"))
    mic = DeviceState(content.get("mic", "0"))
    is_silence = Silence(content.get("is_silence", "0")) if content.get("is_silence") else None
    
    # 创建用户
    user = await user_service.create_user(user_name, camera, mic, is_silence)
    
    # 加入房间
    join_result = await meeting_service.join_room(user)
    
    return BaseResponse(data=join_result.dict())

# 处理离开房间
async def handle_leave_room(content: Dict):
    meeting_service = MeetingService()
    user_id = content.get("user_id")
    
    await meeting_service.leave_room(user_id)
    
    return BaseResponse()

# 处理关闭房间
async def handle_finish_room(content: Dict):
    meeting_service = MeetingService()
    room_id = content.get("room_id")
    
    await meeting_service.finish_room(room_id)
    
    return BaseResponse()

# 处理重连同步
async def handle_resync(content: Dict):
    meeting_service = MeetingService()
    user_id = content.get("user_id")
    room_id = content.get("room_id")
    
    reconnect_result = await meeting_service.reconnect(room_id, user_id)
    
    return BaseResponse(data=reconnect_result.dict())

# 处理获取用户列表
async def handle_get_user_list(content: Dict):
    meeting_service = MeetingService()
    room_id = content.get("room_id")
    
    user_list_result = await meeting_service.get_user_list(room_id)
    
    return BaseResponse(data=user_list_result.dict())

# 处理操作自己的摄像头
async def handle_operate_self_camera(content: Dict):
    user_service = UserService()
    user_id = content.get("user_id")
    operate = DeviceState(content.get("operate"))
    
    await user_service.update_camera_state(user_id, operate)
    
    return BaseResponse()

# 处理操作自己的麦克风
async def handle_operate_self_mic(content: Dict):
    user_service = UserService()
    user_id = content.get("user_id")
    operate = DeviceState(content.get("operate"))
    
    await user_service.update_mic_state(user_id, operate)
    
    return BaseResponse()

# 处理申请麦克风权限
async def handle_operate_self_mic_apply(content: Dict):
    meeting_service = MeetingService()
    user_id = content.get("user_id")
    
    await meeting_service.apply_mic_permission(user_id)
    
    return BaseResponse()

# 处理开始共享
async def handle_start_share(content: Dict):
    user_service = UserService()
    user_id = content.get("user_id")
    share_type = ShareType(content.get("share_type"))
    
    await user_service.start_share(user_id, share_type)
    
    return BaseResponse()

# 处理停止共享
async def handle_finish_share(content: Dict):
    user_service = UserService()
    user_id = content.get("user_id")
    
    await user_service.stop_share(user_id)
    
    return BaseResponse()

# 处理申请共享权限
async def handle_share_permission_apply(content: Dict):
    meeting_service = MeetingService()
    user_id = content.get("user_id")
    
    await meeting_service.apply_share_permission(user_id)
    
    return BaseResponse()

# 处理操作其他用户的摄像头
async def handle_operate_other_camera(content: Dict):
    user_service = UserService()
    operate_user_id = content.get("operate_user_id")
    operate = DeviceState(content.get("operate"))
    
    await user_service.update_camera_state(operate_user_id, operate)
    
    return BaseResponse()

# 处理操作其他用户的麦克风
async def handle_operate_other_mic(content: Dict):
    user_service = UserService()
    operate_user_id = content.get("operate_user_id")
    operate = DeviceState(content.get("operate"))
    
    await user_service.update_mic_state(operate_user_id, operate)
    
    return BaseResponse()

# 处理操作其他用户的共享权限
async def handle_operate_other_share_permission(content: Dict):
    user_service = UserService()
    operate_user_id = content.get("operate_user_id")
    operate = Permission(content.get("operate"))
    
    await user_service.update_share_permission(operate_user_id, operate)
    
    return BaseResponse()

# 处理全员禁言
async def handle_operate_all_mic(content: Dict):
    meeting_service = MeetingService()
    room_id = content.get("room_id")
    operate_self_mic_permission = Permission(content.get("operate_self_mic_permission"))
    operate = DeviceState.Closed
    
    await meeting_service.mute_all(room_id, operate_self_mic_permission)
    
    return BaseResponse()

# 处理主持人答复麦克风申请
async def handle_operate_self_mic_permit(content: Dict):
    meeting_service = MeetingService()
    apply_user_id = content.get("apply_user_id")
    permit = DeviceState(content.get("permit"))
    
    await meeting_service.permit_mic_apply(apply_user_id, permit)
    
    return BaseResponse()

# 处理主持人答复共享权限申请
async def handle_share_permission_permit(content: Dict):
    meeting_service = MeetingService()
    apply_user_id = content.get("apply_user_id")
    permit = Permission(content.get("permit"))
    
    await meeting_service.permit_share_apply(apply_user_id, permit)
    
    return BaseResponse()
```

## 业务逻辑实现

### 会议服务 (app/services/meeting_service.py)

```python
from typing import List, Optional
from ..models.meeting import *
from ..models.rts import *
from ..utils.volcengine_utils import VolcengineUtils
import time

class MeetingService:
    def __init__(self):
        self.volcengine_utils = VolcengineUtils()
        self.rooms = {}  # 简单内存存储，实际项目中使用数据库
        self.user_service = UserService()
    
    async def join_room(self, user: MeetingUser) -> JoinMeetingRoomRes:
        # 创建或获取房间
        room_id = "default_room"  # 简化处理，实际应动态生成或从参数获取
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
        
        # 获取房间用户列表
        user_list = await self.get_room_users(room_id)
        user_list.append(user)
        
        # 生成RTC token
        token = self.volcengine_utils.generate_rtc_token(user.user_id, room_id)
        
        # 生成白板相关信息
        wb_room_id = f"wb_{room_id}"
        wb_user_id = f"wb_{user.user_id}"
        wb_token = self.volcengine_utils.generate_whiteboard_token(wb_user_id, wb_room_id)
        
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
```

### 用户服务 (app/services/user_service.py)

```python
from typing import Optional
from ..models.meeting import MeetingUser
from ..models.rts import *
import uuid
import time

class UserService:
    def __init__(self):
        self.users = {}  # 简单内存存储，实际项目中使用数据库
    
    async def create_user(self, user_name: str, camera: DeviceState, 
                         mic: DeviceState, is_silence: Optional[Silence] = None) -> MeetingUser:
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
```

## 火山引擎工具 (app/utils/volcengine_utils.py)

```python
import volcengine
from volcengine.rtc.RtcService import RtcService
from volcengine.imp.ImpService import ImpService

class VolcengineUtils:
    def __init__(self):
        # 初始化火山引擎SDK
        volcengine.callback = None
        self.rtc_service = RtcService()
        # 配置火山引擎SDK
        # self.rtc_service.set_ak("your_ak")
        # self.rtc_service.set_sk("your_sk")
    
    def generate_rtc_token(self, user_id: str, room_id: str) -> str:
        # 简化处理，实际应使用火山引擎SDK生成真实的RTC token
        return f"rtc_token_{user_id}_{room_id}"
    
    def generate_whiteboard_token(self, user_id: str, room_id: str) -> str:
        # 简化处理，实际应使用火山引擎SDK生成真实的白板token
        return f"wb_token_{user_id}_{room_id}"
```

## 主程序入口 (app/main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import rts
from config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Meeting Room Backend Server",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(rts.router, prefix=settings.API_V1_STR, tags=["RTS"])

# 根路径
@app.get("/")
async def root():
    return {"message": "Meeting Room Server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

## 配置文件 (config.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # FastAPI配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Meeting Room Server"
    DEBUG: bool = True
    
    # 火山引擎配置
    VOLC_ACCESS_KEY: str = "your_volc_access_key"
    VOLC_SECRET_KEY: str = "your_volc_secret_key"
    VOLC_REGION: str = "cn-beijing"
    
    # RTS配置
    RTS_APP_ID: str = "your_rts_app_id"
    RTS_APP_KEY: str = "your_rts_app_key"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## 启动脚本 (run.sh)

```bash
#!/bin/bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 运行方式

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动服务：
```bash
python -m app.main
# 或
bash run.sh
```

3. 访问API文档：
```
http://localhost:8000/docs
```

## 注意事项

1. 本实现是一个简化版本，实际生产环境中需要：
   - 使用数据库存储会议和用户信息
   - 完善错误处理
   - 添加日志记录
   - 实现真实的火山引擎SDK集成
   - 添加认证和授权机制
   - 优化性能和并发处理

2. 火山引擎配置：
   - 需要替换为您自己的火山引擎Access Key和Secret Key
   - 需要正确配置RTS App ID和App Key
   - 实际使用时需要安装火山引擎的Python SDK并正确初始化

3. 前端集成：
   - 前端需要将RTS消息发送到后端的`/api/v1/rts/message`接口
   - 消息格式应为`{"event_name": "event_name", "content": {...}}`

这个实现提供了一个完整的框架，您可以根据实际需求进行扩展和优化。
