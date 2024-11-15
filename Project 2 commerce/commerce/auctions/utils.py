from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Message:
    text: str
    type: str = "success"
    details: Optional[List[str]] = None

    @classmethod
    def success(cls, text: str) -> "Message":
        return cls(text=text, type="success")

    @classmethod
    def error(cls, text: str, details: Optional[List[str]] = None) -> "Message":
        return cls(text=text, type="danger", details=details)

    @classmethod
    def warning(cls, text: str) -> "Message":
        return cls(text=text, type="warning")

    @property
    def bootstrap_class(self) -> str:
        return f"alert-{self.type}"


