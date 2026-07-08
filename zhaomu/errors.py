class ZhaomuError(Exception):
    """zhaomu API 错误基类"""
    pass


class AuthError(ZhaomuError):
    """认证错误（HTTP 401/403）"""
    pass


class APIError(ZhaomuError):
    """API 返回错误（HTTP 4xx/5xx）"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code} - {message}")


class NetworkError(ZhaomuError):
    """网络连接错误"""
    pass
