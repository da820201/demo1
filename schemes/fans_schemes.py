import datetime
import time
from typing import Optional
from enum import Enum
from redis_om import (
    EmbeddedJsonModel,
    JsonModel,
    Field,
    get_redis_connection
)


redis = get_redis_connection(port=6380, db=0)


class PlatformType(Enum):
    facebook = 0
    instagram = 1
    threads = 2


class FansSchemes(JsonModel):
    uid: Optional[str] = Field(index=True)
    platform_uid: Optional[str] = Field(index=True)
    platform_type: Optional[int] = Field(index=True, default=PlatformType.facebook.value)
    platform_name: Optional[str] = Field(index=True)
    head_pic: Optional[str] = None
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())
    delete_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis


