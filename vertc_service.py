# coding:utf-8
import json
import threading
import logging

from volcengine.ApiInfo import ApiInfo
from volcengine.Credentials import Credentials
from volcengine.base.Service import Service
from volcengine.ServiceInfo import ServiceInfo
from config import settings

logger = logging.getLogger(__name__)


class VertcService(Service):
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not hasattr(VertcService, "_instance"):
            with VertcService._instance_lock:
                if not hasattr(VertcService, "_instance"):
                    VertcService._instance = object.__new__(cls)
        return VertcService._instance

    def __init__(self):
        self.service_info = VertcService.get_service_info()
        self.api_info = VertcService.get_api_info()
        super(VertcService, self).__init__(self.service_info, self.api_info)

    @staticmethod
    def get_service_info():
        service_info = ServiceInfo("rtc.volcengineapi.com", {'Accept': 'application/json'},
                                   Credentials('', '', 'rtc', settings.volc_region), 30, 30)
        return service_info

    @staticmethod
    def get_api_info():
        api_info = {
            # 云端录制
            "StartRecord": ApiInfo("POST", "/", {"Action": "StartRecord", "Version": "2023-11-01"}, {}, {}),
            "StopRecord": ApiInfo("POST", "/", {"Action": "StopRecord", "Version": "2023-11-01"}, {}, {}),
            "GetRecordTask": ApiInfo("GET", "/", {"Action": "GetRecordTask", "Version": "2023-11-01"}, {}, {}),
            
            # 转推直播
            "StartPushMixedStreamToCDN": ApiInfo("POST", "/", {"Action": "StartPushMixedStreamToCDN", "Version": "2023-11-01"}, {}, {}),
            "StopPushStreamToCDN": ApiInfo("POST", "/", {"Action": "StopPushStreamToCDN", "Version": "2023-11-01"}, {}, {}),

            # 输入在线媒体流
            "StartRelayStream": ApiInfo("POST", "/", {"Action": "StartRelayStream", "Version": "2023-11-01"}, {}, {}),
            "StopRelayStream": ApiInfo("POST", "/", {"Action": "StopRelayStream", "Version": "2023-11-01"}, {}, {}),

            # 实时对话式AI
            "StartVoiceChat": ApiInfo("POST", "/", {"Action": "StartVoiceChat", "Version": "2024-12-01"}, {}, {}),
            "StopVoiceChat": ApiInfo("POST", "/", {"Action": "StopVoiceChat", "Version": "2024-12-01"}, {}, {}),

            # 音视频互动智能体
            "StartVideoChat": ApiInfo("POST", "/", {"Action": "StartVoiceChat", "Version": "2025-06-01"}, {}, {}),
            "StopVideoChat": ApiInfo("POST", "/", {"Action": "StopVoiceChat", "Version": "2025-06-01"}, {}, {}),

            # 实时消息通信
            "SendUnicast": ApiInfo("POST", "/", {"Action": "SendUnicast", "Version": "2023-07-20"}, {}, {}),
            "SendBroadcast": ApiInfo("POST", "/", {"Action": "SendBroadcast", "Version": "2023-07-20"}, {}, {}),
            "SendRoomUnicast": ApiInfo("POST", "/", {"Action": "SendRoomUnicast", "Version": "2023-07-20"}, {}, {}),

            # 房间管理
            "BanRoomUser": ApiInfo("POST", "/", {"Action": "BanRoomUser", "Version": "2023-11-01"}, {}, {}),
        }
        return api_info

    # ============================ 云端录制 ============================

    def start_record(self, body):
        res = self.json("StartRecord", {}, body)
        if res == '':
            raise Exception("StartRecord: empty response")
        res_json = json.loads(res)
        return res_json

    def stop_record(self, body):
        res = self.json("StopRecord", {}, body)
        if res == '':
            raise Exception("StopRecord: empty response")
        res_json = json.loads(res)
        return res_json

    def get_record_task(self, params):
        res = self.get("GetRecordTask", params)
        if res == '':
            raise Exception("GetRecordTask: empty response")
        res_json = json.loads(res)
        return res_json

    # ============================ 转推直播 ============================

    # 启动合流转推（StartPushMixedStreamToCDN）
    def start_push_mixed_stream_to_cdn(self, body):
        res = self.json("StartPushMixedStreamToCDN", {}, body)
        if res == '':
            raise Exception("StartPushMixedStreamToCDN: empty response")
        res_json = json.loads(res)
        return res_json
    
    # 停止转推直播（StopPushStreamToCDN）
    def stop_push_stream_to_cdn(self, body):
        res = self.json("StopPushStreamToCDN", {}, body)
        if res == '':
            raise Exception("StopPushStreamToCDN: empty response")
        res_json = json.loads(res)
        return res_json

    # ============================ 输入在线媒体流 ============================

    # 开始在线媒体流输入（StartRelayStream）
    def start_relay_stream(self, body):
        res = self.json("StartRelayStream", {}, body)
        if res == '':
            raise Exception("StartRelayStream: empty response")
        res_json = json.loads(res)
        return res_json
    
    # 停止在线媒体流输入（StopRelayStream）
    def stop_relay_stream(self, body):
        res = self.json("StopRelayStream", {}, body)
        if res == '':
            raise Exception("StopRelayStream: empty response")
        res_json = json.loads(res)
        return res_json

    # ============================ 实时对话式AI ============================

    # 启动音视频互动智能体（StartVoiceChat）
    def start_voice_chat(self, body):
        res = self.json("StartVoiceChat", {}, body)
        if res == '':
            raise Exception("StartVoiceChat: empty response")
        res_json = json.loads(res)
        return res_json
    
    # 停止音视频互动智能体（StopVoiceChat）
    def stop_voice_chat(self, body):
        res = self.json("StopVoiceChat", {}, body)
        if res == '':
            raise Exception("StopVoiceChat: empty response")
        res_json = json.loads(res)
        return res_json


    # ============================ 音视频互动智能体 ============================

    # 启动音视频互动智能体（StartVoiceChat）
    def start_video_chat(self, body):
        res = self.json("StartVideoChat", {}, body)
        if res == '':
            raise Exception("StartVideoChat: empty response")
        res_json = json.loads(res)
        return res_json
    
    # 停止音视频互动智能体（StopVoiceChat）
    def stop_video_chat(self, body):
        res = self.json("StopVideoChat", {}, body)
        if res == '':
            raise Exception("StopVideoChat: empty response")
        res_json = json.loads(res)
        return res_json

# ============================ 实时消息通信 ============================

# 发送房间外点对点消息（SendUnicast）
    def send_unicast(self, body):
        try:
            res = self.json("SendUnicast", {}, body)
            if res == '':
                logger.error("SendUnicast: 收到空响应")
                return {"ResponseMetadata": {"Error": {"Code": "EmptyResponse", "Message": "Empty response from server"}}}
            res_json = json.loads(res)
            return res_json
        except Exception as e:
            logger.error(f"SendUnicast 调用失败: {str(e)}", exc_info=True)
            return {"ResponseMetadata": {"Error": {"Code": "APICallFailed", "Message": f"API call failed: {str(e)}"}}}

# 发送房间内广播消息（SendBroadcast）
    def send_broadcast(self, body):
        try:
            res = self.json("SendBroadcast", {}, body)
            if res == '':
                logger.error("SendBroadcast: empty response")
                return {"ResponseMetadata": {"Error": {"Code": "EmptyResponse", "Message": "Empty response from server"}}}
            res_json = json.loads(res)
            return res_json
        except Exception as e:
            logger.error(f"SendBroadcast 调用失败: {str(e)}", exc_info=True)
            return {"ResponseMetadata": {"Error": {"Code": "APICallFailed", "Message": f"API call failed: {str(e)}"}}}

# 发送房间内点对点消息（SendRoomUnicast）
    def send_room_unicast(self, body):
        try:
            res = self.json("SendRoomUnicast", {}, body)
            if res == '':
                logger.error("SendRoomUnicast: empty response")
                return {"ResponseMetadata": {"Error": {"Code": "EmptyResponse", "Message": "Empty response from server"}}}
            res_json = json.loads(res)
            return res_json
        except Exception as e:
            logger.error(f"SendRoomUnicast 调用失败: {str(e)}", exc_info=True)
            return {"ResponseMetadata": {"Error": {"Code": "APICallFailed", "Message": f"API call failed: {str(e)}"}}}

# ============================ 房间管理 ============================
    # 封禁房间用户（BanRoomUser）
    def ban_room_user(self, body):
        res = self.json("BanRoomUser", {}, body)
        if res == '':
            raise Exception("BanRoomUser: empty response")
        res_json = json.loads(res)
        return res_json


# 实时消息通信服务实例
rtc_service: VertcService = VertcService()
rtc_service.set_ak(settings.volc_ak)
rtc_service.set_sk(settings.volc_sk)
