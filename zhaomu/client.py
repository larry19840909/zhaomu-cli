import os
import time
from typing import Any

import requests

from zhaomu.config import Config
from zhaomu.errors import AuthError, APIError, NetworkError
from zhaomu.api.region import RegionAPI
from zhaomu.api.product import ProductAPI
from zhaomu.api.cloud import CloudAPI
from zhaomu.api.accelerator import AcceleratorAPI
from zhaomu.api.other import OtherAPI

RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


class ZhaomuClient:
    BASE_URL = "https://api.zhaomu.net"

    def __init__(self, apikey: str, timeout: int = 30, max_retries: int = 3):
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {apikey}"
        self._timeout = timeout
        self._max_retries = max_retries

        self.region = RegionAPI(self)
        self.product = ProductAPI(self)
        self.cloud = CloudAPI(self)
        self.accelerator = AcceleratorAPI(self)
        self.other = OtherAPI(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self._session.close()

    @classmethod
    def from_config(cls, path: str = "config.json", **kwargs) -> "ZhaomuClient":
        if os.path.isfile(path):
            config = Config.load(path)
        else:
            config = Config.from_env()
        return cls(apikey=config.apikey, **kwargs)

    def _parse_or_raise(self, resp: requests.Response, path: str) -> Any:
        status = resp.status_code
        try:
            body = resp.json()
        except requests.exceptions.JSONDecodeError:
            raise APIError(status, resp.text[:500] or f"non-JSON response (HTTP {status})")
        if isinstance(body, dict) and not body.get("success", True):
            msg = body.get("message", f"HTTP {status}")
            return body  # let caller handle success field
        return body

    def _request(self, method: str, path: str, params: dict | None = None,
                 data: dict | None = None) -> Any:
        url = f"{self.BASE_URL}{path}"
        last_error = None

        for attempt in range(self._max_retries):
            try:
                resp = self._session.request(
                    method, url, params=params, json=data, timeout=self._timeout,
                )
                status = resp.status_code

                if status in (401, 403):
                    raise AuthError(f"HTTP {status} - authentication failed")

                if status == 404:
                    raise APIError(status, "resource not found")

                if status in RETRYABLE_STATUS and attempt < self._max_retries - 1:
                    retry_after = resp.headers.get("Retry-After")
                    wait = (
                        int(retry_after)
                        if retry_after and retry_after.isdigit()
                        else min(2 ** (attempt + 1), 16)
                    )
                    last_error = APIError(status, resp.text[:200] or f"HTTP {status}")
                    time.sleep(wait)
                    continue

                if not resp.ok:
                    msg = resp.text[:500] or f"HTTP {status}"
                    raise APIError(status, msg)

                return self._parse_or_raise(resp, path)

            except requests.exceptions.Timeout:
                last_error = NetworkError(f"request to {path} timed out")
            except requests.exceptions.ConnectionError as e:
                last_error = NetworkError(f"connection failed: {e}")
            except (AuthError, APIError):
                raise

            if attempt < self._max_retries - 1:
                time.sleep(min(2 ** attempt, 8))

        raise last_error

    def get(self, path: str, params: dict | None = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, data: dict | None = None) -> Any:
        return self._request("POST", path, data=data)

    def put(self, path: str, data: dict | None = None) -> Any:
        return self._request("PUT", path, data=data)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)
