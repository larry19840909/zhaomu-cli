from zhaomu.client import ZhaomuClient
from zhaomu.config import Config
from zhaomu.errors import ZhaomuError, AuthError, APIError, NetworkError

__all__ = ["ZhaomuClient", "Config", "ZhaomuError", "AuthError", "APIError", "NetworkError"]


def get_web_client():
    """创建 ZhaomuWebClient 实例（延迟导入以避免循环依赖）。"""
    from zhaomu.web_client import ZhaomuWebClient
    return ZhaomuWebClient
