import logging
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rts_meeting import meeting_router
from rts_callback import callback_router
from config import settings
from log_mw import RequestLoggingMiddleware


# 配置日志
log_level = logging.DEBUG if settings.debug else logging.WARNING
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# 定义Lifespan事件
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期事件"""

    # 启动事件
    logger.info(f"启动 {settings.app_name} v{settings.app_version}")
    
    # 连接 Redis
    # await manager.connect_redis()
    
    # 启动心跳监控
    #await manager.start_heartbeat_monitor()
    
    logger.info("应用启动完成")
    
    yield  # 应用运行中
    
    # 关闭事件
    logger.info("应用正在关闭...")
    
    # 关闭所有 WebSocket 连接
    #for connection_id in list(manager.active_connections.keys()):
    #    await manager.disconnect(connection_id, reason="服务器关闭")
    
    logger.info("应用已关闭")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加Log中间件
app.add_middleware(RequestLoggingMiddleware)

# 注册路由
app.include_router(meeting_router, prefix=settings.api_vstr, tags=["Meeting RTS"])
app.include_router(callback_router, prefix=settings.api_vstr, tags=["Callback RTS"])

# 处理根路径请求
@app.get("/")
async def root():
    return {"message": "JUSI Meeting RTS Server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.bind_addr,
        port=settings.bind_port,
        reload=settings.debug,
        reload_dirs=["."],
        log_level=log_level)
