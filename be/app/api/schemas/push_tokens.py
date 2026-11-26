"""Push token schemas."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.ports.repositories import PushTokenRecord

EXPO_TOKEN_PATTERN = r"^(ExponentPushToken|ExpoPushToken)\[[^\]\s]{1,200}\]$"


class PushPlatform(StrEnum):
    IOS = "ios"
    ANDROID = "android"


class PushTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(pattern=EXPO_TOKEN_PATTERN, max_length=255)
    platform: PushPlatform


class PushTokenOut(BaseModel):
    token: str
    platform: PushPlatform

    @classmethod
    def from_record(cls, record: PushTokenRecord) -> PushTokenOut:
        return cls(token=record.token, platform=PushPlatform(record.platform))
