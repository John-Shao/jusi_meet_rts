from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # FastAPI配置
    app_name: str = "JUSI Meet RTS"
    app_desc: str = "JUSI Meet RTS Server"
    api_vstr: str = "/api/v1"

    # AK/SK配置
    account_id: str = ""
    volc_ak: str = ""
    volc_sk: str = ""
    volc_region: str = "cn-beijing"
    volc_token_expire_seconds: int = 3600  # 默认1小时

    # 音视频互动智能体（Conversational-AI）
    volc_cai_app_id: str
    volc_cai_app_key: str

    # RTC配置
    rtc_app_id: str = ""
    rtc_app_key: str = ""

     # 豆包端到端实时语音大模型
    doubao_s2s_app_id: str
    doubao_s2s_access_token: str

    # 接收X5设备推送视频流的RTMP服务器地址和端口
    video_rtmp_host: str
    video_rtmp_port: int
    
    # 接收VeRTC推送音频流的RTMP服务器地址和端口
    audio_rtmp_host: str
    audio_rtmp_port: int
    audio_rtsp_port: int

    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # MySQL配置
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "jusi_db"

    # 其他配置项
    token_expire_ts: int = 24 * 60 * 60
    app_name: str = "JUSI RTS"
    app_version: str = "1.0.0"
    bind_addr: str = "0.0.0.0"
    bind_port: int = 9000
    debug: bool = True
    
    # 指定配置文件和相关参数
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False

# 创建配置实例
settings = Settings()
