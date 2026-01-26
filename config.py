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

    # RTC配置
    rtc_app_id: str = ""
    rtc_app_key: str = ""

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
