# coding:utf-8
import time
import json
from vertc_service import VertcService
from access_token import AccessToken, PrivSubscribeStream, PrivPublishStream
from config import settings


class VertcClient:
    def __init__(self):
        self.rtc_app_id = settings.rtc_app_id
        self.rtc_app_key = settings.rtc_app_key

        self.cai_app_id = settings.volc_cai_app_id
        self.cai_app_key = settings.volc_cai_app_key

        self.s2s_app_id = settings.doubao_s2s_app_id
        self.s2s_access_token = settings.doubao_s2s_access_token
        
        self.rtc_service = VertcService()
        self.rtc_service.set_ak(settings.volc_ak)
        self.rtc_service.set_sk(settings.volc_sk)

    # ============================ 转推直播 ============================

    # 启动合流转推（StartPushMixedStreamToCDN）
    def start_push_mixed_stream(self, room_id, user_id, task_id, push_url="", **kwargs):
        """启动合流转推"""
        request = {
            "AppId": self.rtc_app_id,
            "RoomId": room_id,
            "TaskId": task_id,
            "PushURL": push_url,
            "ExcludeStreams": {
                "StreamList": [
                    {
                        "UserId": user_id
                    }
                ]
            },
            "Control": {
                "MediaType": kwargs.get('media_type', 1),            # 0: 音视频，1: 纯音频
                "PushStreamMode": kwargs.get('push_stream_mode', 1)  # 0：房间内有用户推流时才触发推流，1：调用接口即触发推流
            }
        }

        body = json.dumps(request)
        return self.rtc_service.start_push_mixed_stream_to_cdn(body)

    # 停止合流转推（StopPushStreamToCDN）
    def stop_push_stream_to_cdn(self, room_id, task_id):    
        """停止合流转推"""
        request = {
            "AppId": self.rtc_app_id,
            "RoomId": room_id,
            "TaskId": task_id
        }

        body = json.dumps(request)
        return self.rtc_service.stop_push_stream_to_cdn(body)

    # ============================ 输入在线媒体流 ============================

    # 启动在线媒体流输入（StartRelayStream）
    def start_relay_stream(self, room_id, user_id, task_id, stream_url, **kwargs):
        """启动在线媒体流输入"""
        atobj = AccessToken(self.rtc_app_id, self.rtc_app_key, room_id, user_id)
        atobj.add_privilege(PrivSubscribeStream, 0)
        atobj.add_privilege(PrivPublishStream, int(time.time()) + settings.volc_token_expire_seconds)
        atobj.expire_time(int(time.time()) + settings.volc_token_expire_seconds)  # TODO: 复用优化，将token放在redis中，设定过期时间
        token = atobj.serialize()

        request = {
            "AppId": self.rtc_app_id,
            "RoomId": room_id,
            "UserId": user_id,
            "TaskId": task_id,
            "Token": token,
            "Control": {
                "StreamUrl": stream_url,
                "VideoWidth": 1280,
                "VideoHeight": 720
            }
        }

        body = json.dumps(request)
        return self.rtc_service.start_relay_stream(body)
    
    # 停止在线媒体流输入（StopRelayStream）
    def stop_relay_stream(self, room_id, task_id):
        """停止在线媒体流输入"""
        request = {
            "AppId": self.rtc_app_id,
            "RoomId": room_id,
            "TaskId": task_id
        }

        body = json.dumps(request)
        return self.rtc_service.stop_relay_stream(body)
    
    # ============================ 实时对话式AI ============================

    # 启动实时对话式AI（StartVoiceChat）
    def start_voice_chat(self, room_id, bot_id, user_id, task_id, dialog_id, **kwargs):
        """启动实时对话式AI"""
        request = {
            "AppId": self.rtc_app_id,
            "RoomId": room_id,
            "TaskId": task_id,
            "Config": {
                "S2SConfig": {           # 端到端语音模型核心配置
                    "Provider": "volcano",  # 端到端语音模型服务提供商，当前固定取值 volcano
                    "ProviderParams": {  # 语音端到端模型的详细配置
                        "app": {         # 认证信息
                            "appid": self.s2s_app_id,  # 必填，端到端模型的appid
                            "token": self.s2s_access_token  # 必填，端到端模型的token
                        },
                        "tts": {  # TTS配置
                            "speaker": "zh_female_vv_jupiter_bigtts"  # 指定发音人
                        },
                        "dialog": {  # 对话设定
                            "bot_name": "巨思AI助手",
                            "system_role": ("##人设\n你的名字叫巨思（英文Juice），是一个全能的超级助手，具备强大的知识库、情感理解能力和解决问题的能力。"
                                + "你的目标是高效、专业、友好地帮助用户完成各类任务，包括但不限于日常生活、工作安排、信息检索、学习辅导、创意写作、语言翻译和技术支持等；"
                                + "\n\n##约束\n始终主动、礼貌、有条理；\n回答准确但不冗长，必要时可提供简洁总结+详细解释；\n不清楚的任务会主动澄清，不假设、不误导。"
                                ),
                            "speaking_style": "亲切",
                            "dialog_id": dialog_id  # 可选项，加载相同dialog id的对话历史，如未设置，会默认生成一个唯一的 ID
                        }
                    }
                }
            },
            "AgentConfig": {
                "TargetUserId": [user_id],  # 单个房间内，仅支持一个用户与智能体一对一通话
                "WelcomeMessage": "我是巨思AI助手，有什么需要我为您效劳的吗？",  # 智能体启动后的欢迎词
                "UserId": bot_id  # 智能体 ID，用于标识智能体
            }
        }

        body = json.dumps(request)
        return self.rtc_service.start_voice_chat(body)
        
    # 关闭实时对话式AI（StopVoiceChat）
    def stop_voice_chat(self, room_id, task_id):
        """停止实时对话式AI"""
        request = {
            "AppId": self.rtc_app_id,
            "RoomId": room_id,
            "TaskId": task_id
        }

        body = json.dumps(request)
        return self.rtc_service.stop_voice_chat(body)
    
    # ============================ 音视频互动智能体 ============================

    # 启动音视频互动智能体（StartVideoChat）
    def start_video_chat(self, room_id, bot_id, user_id, task_id, **kwargs):
        """启动音视频互动智能体"""
        request = {
            "AppId": self.cai_app_id,
            "RoomId": room_id,  # 房间ID
            "TaskId": task_id,  # 任务ID
            "Config": {
                "ASRConfig": {
                "Provider": "volcano",
                "ProviderParams": {
                    "Mode": "bigmodel",
                    "StreamMode": 0
                },
                "VADConfig": {},
                "InterruptConfig": {}
                },
                "LLMConfig": {
                    "Mode": "ArkV3",
                    "ModelName": "doubao-seed-1-6-251015",
                    "TopP": 0.3,
                    "SystemMessages": [
                        "##人设\n你的名字叫巨思（英文Juice），是一个全能的超级助手，具备强大的知识库、情感理解能力和解决问题的能力。你的目标是高效、专业、友好地帮助用户完成各类任务，包括但不限于日常生活、工作安排、信息检索、学习辅导、创意写作、语言翻译和技术支持等；\n\n##约束\n始终主动、礼貌、有条理；\n回答准确但不冗长，必要时可提供简洁总结+详细解释；\n不清楚的任务会主动澄清，不假设、不误导。"
                    ],
                    "HistoryLength": 10,
                    "ThinkingType": "disabled",
                    "VisionConfig": {
                        "SnapshotConfig": {},
                        "StorageConfig": {
                        "TosConfig": {}
                        }
                    }
                },
                "TTSConfig": {
                    "Provider": "volcano_bidirection",
                    "ProviderParams": {
                        "Credential": {
                            "ResourceId": "seed-tts-1.0"
                        },
                        "VolcanoTTSParameters": "{\"req_params\":{\"speaker\":\"zh_female_shuangkuaisisi_emo_v2_mars_bigtts\",\"audio_params\":{\"speech_rate\":0}}}"
                    }
                },
                "SubtitleConfig": {
                    "DisableRTSSubtitle": True
                },
                "InterruptMode": 0,
                "FunctionCallingConfig": {},
                "WebSearchAgentConfig": {},
                "MemoryConfig": {},
                "MusicAgentConfig": {}
            },
            "AgentConfig": {
                "TargetUserId": [user_id],  # 目前仅支持一个用户与智能体对话
                "UserId": bot_id,
                "WelcomeMessage": "我是巨思AI助手，有什么需要我为您效劳的吗？",
                "Burst": {
                    "Enable": False,
                    "BufferSize": 0,
                    "Interval": 0
                },
                "VoicePrint": {
                    "MetaList": None,
                    "VoicePrintList": None
                }
            }
        }
        body = json.dumps(request)
        return self.rtc_service.start_video_chat(body)

    # 关闭音视频互动智能体（StopVideoChat）
    def stop_video_chat(self, room_id, task_id):
        """停止音视频互动智能体"""
        request = {
            "AppId": self.cai_app_id,
            "RoomId": room_id,
            "TaskId": task_id
        }

        body = json.dumps(request)
        return self.rtc_service.stop_video_chat(body)

# veRTC全局实例
rtc_client: VertcClient = VertcClient()


# 测试代码
if __name__ == "__main__":
    jusi_device_uid = "4ee0ebf6ac0b49bc9825c7e0107d1e31"  # 巨思设备的用户ID

    class TestMode:
        AUDIO_START = 10
        AUDIO_STOP =  11
        VIDEO_START = 20
        VIDEO_STOP =  21

    test_mode = TestMode.AUDIO_STOP  # 修改此处以切换测试模式

    if test_mode == TestMode.AUDIO_START:
        # 测试启动合流转推
        response = rtc_client.start_push_mixed_stream(
            room_id="100",
            user_id=jusi_device_uid,  # 排除的用户ID
            task_id="200",
            push_url=f"rtmp://{settings.audio_rtmp_host}:{settings.audio_rtmp_port}/live/00a4b5697e3d16796b818d656ccea433"
        )
        print(response)
        
        # 测试启动在线媒体流输入
        response = rtc_client.start_relay_stream(
            room_id="100",
            user_id=jusi_device_uid,  # 在线媒体流输入的用户ID
            task_id="100",
            stream_url=f"rtmp://{settings.video_rtmp_host}:{settings.video_rtmp_port}/live/00a4b5697e3d16796b818d656ccea433"
        )
        print(response)

        # 测试启动实时对话式AI
        response = rtc_client.start_voice_chat(
            room_id="100",
            bot_id="bot_008",  # 智能体的用户ID
            user_id=jusi_device_uid,  # 与AI对话的用户ID
            task_id="300",
            dialog_id="dialog_123"
        )
        print(response)
    
    if test_mode == TestMode.AUDIO_STOP:
        # 测试停止合流转推
        response = rtc_client.stop_push_stream_to_cdn(
            room_id="100",
            task_id="200"
        )
        print(response)

        # 测试停止在线媒体流输入
        response = rtc_client.stop_relay_stream(
            room_id="100",
            task_id="100"
        )
        print(response)

        # 测试关闭实时对话式AI
        response = rtc_client.stop_voice_chat(
            room_id="100",
            task_id="300"
        )
        print(response)
    
    
    # ============================ 测试音视频互动智能体 ============================
    
    if test_mode == TestMode.VIDEO_START:
        # 测试启动音视频互动智能体
        response = rtc_client.start_video_chat(
            room_id="100",
            bot_id="jusi_00a4b5697e3d16796b818d656ccea433",
            user_id="user_615",  # 与智能体对话的用户ID
            task_id="400"
        )
        print(response)

    if test_mode == TestMode.VIDEO_STOP:
        # 测试关闭音视频互动智能体
        response = rtc_client.stop_video_chat(
            room_id="100",
            task_id="400"
        )
        print(response)
