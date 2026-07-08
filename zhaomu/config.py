import json
import os
from dataclasses import dataclass, field


@dataclass
class Config:
    apikey: str
    sos_token: str = ""
    web_session_file: str = ""

    def __repr__(self) -> str:
        apikey_masked = f"{self.apikey[:4]}...{self.apikey[-4:]}" if len(self.apikey) > 8 else "***"
        sos_masked = "set" if self.sos_token else "unset"
        web_masked = "set" if self.web_session_file else "unset"
        return f"Config(apikey={apikey_masked}, sos_token={sos_masked}, web_session={web_masked})"

    @classmethod
    def load(cls, path: str = "config.json") -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            apikey=data["apikey"],
            sos_token=data.get("sos_token", ""),
            web_session_file=data.get("web_session_file", ""),
        )

    @classmethod
    def from_env(cls) -> "Config":
        apikey = os.environ.get("ZHAOMU_APIKEY", "")
        if not apikey:
            raise ValueError("ZHAOMU_APIKEY environment variable is not set")
        return cls(
            apikey=apikey,
            sos_token=os.environ.get("ZHAOMU_SOS_TOKEN", ""),
            web_session_file=os.environ.get("ZHAOMU_WEB_SESSION_FILE", ""),
        )
