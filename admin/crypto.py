"""admin/crypto.py — 密码哈希与密钥加密模块。

提供两种安全原语：
1. 密码哈希（argon2id） — 用于存储用户登录密码
2. 密钥加密（Windows DPAPI / 明文回退） — 用于存储 API Key 等敏感配置
"""

import base64
from argon2 import PasswordHasher  # type: ignore[import-untyped]
from argon2.exceptions import VerifyMismatchError  # type: ignore[import-untyped]

# 全局共享的 PasswordHasher 实例 — argon2 内部有 GIL 保护，线程安全
_ph = PasswordHasher()

# Windows DPAPI 标志：CRYPTPROTECT_LOCAL_MACHINE = 0x00400000
# 该标志使密钥绑定到本机而非当前用户，适合服务场景
_CRYPTPROTECT_LOCAL_MACHINE = 0x00400000

# 非 Windows 平台的明文回退前缀
_PLAINTEXT_PREFIX = b"[PLAINTEXT]"

# 尝试加载 Windows DPAPI — pywin32 不在所有环境中安装
try:
    from win32crypt import CryptProtectData, CryptUnprotectData  # type: ignore[import-untyped]

    _has_dpapi = True
except ImportError:
    CryptProtectData = None  # type: ignore[assignment]
    CryptUnprotectData = None  # type: ignore[assignment]
    _has_dpapi = False


def hash_password(password: str) -> str:
    """使用 argon2id 对密码进行哈希。

    返回以 $argon2id$ 开头的哈希字符串，每次调用使用不同的随机盐。
    空字符串、含 Unicode 字符的密码均正确支持。
    """
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码是否匹配存储的哈希值。

    Args:
        password: 待验证的明文密码
        password_hash: 由 hash_password 生成的哈希字符串

    Returns:
        True 表示密码匹配，False 表示密码错误或哈希格式无效。
    """
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def encrypt_secret(data: str) -> str:
    """加密敏感数据。

    Windows 平台使用 DPAPI (CryptProtectData + CRYPTPROTECT_LOCAL_MACHINE)，
    其他平台使用明文回退（base64 编码并添加 [PLAINTEXT] 前缀）。

    返回 base64 编码的密文字符串。
    """
    plain_bytes = data.encode("utf-8")

    if _has_dpapi:
        encrypted = CryptProtectData(  # pyright: ignore[reportOptionalCall]
            plain_bytes,
            None,  # DataDescr
            None,  # OptionalEntropy
            None,  # Reserved
            None,  # PromptStruct
            _CRYPTPROTECT_LOCAL_MACHINE,
        )
        return base64.b64encode(encrypted).decode("ascii")

    # 非 Windows 回退：明文 + 前缀标记
    return base64.b64encode(_PLAINTEXT_PREFIX + plain_bytes).decode("ascii")


def decrypt_secret(encrypted: str) -> str:
    """解密由 encrypt_secret 生成的密文。

    Args:
        encrypted: base64 编码的密文字符串

    Returns:
        解密后的明文字符串

    Raises:
        ValueError: base64 解码失败、密文损坏或格式无法识别。
    """
    # base64 解码
    try:
        cipher_bytes = base64.b64decode(encrypted, validate=True)
    except Exception as exc:
        raise ValueError("无效的 base64 编码") from exc

    # 尝试 Windows DPAPI 解密
    if _has_dpapi:
        # 排除明文回退格式 — 防止误将回退密文传给 DPAPI
        if cipher_bytes.startswith(_PLAINTEXT_PREFIX):
            return cipher_bytes[len(_PLAINTEXT_PREFIX):].decode("utf-8")

        try:
            _description, plain_bytes = CryptUnprotectData(cipher_bytes)  # pyright: ignore[reportOptionalCall]
            return plain_bytes.decode("utf-8")
        except Exception as exc:
            raise ValueError("密文解密失败") from exc

    # 非 Windows 回退：检查 [PLAINTEXT] 前缀
    if cipher_bytes.startswith(_PLAINTEXT_PREFIX):
        return cipher_bytes[len(_PLAINTEXT_PREFIX):].decode("utf-8")

    raise ValueError("无法识别的密文格式")
