import datetime
import time
from redis_om import (
    JsonModel,
    Field,
    get_redis_connection
)

from typing import Optional

redis = get_redis_connection(port=6380, db=0)


class FollowerFacebook(JsonModel, index=True):
    uid: Optional[str] = Field(index=True, primary_key=True)
    name: Optional[str] = Field(index=True)
    profile_url: Optional[str] = None
    head_pic_url: Optional[str] = None
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "follower_facebook"


class FollowerInstagram(JsonModel, index=True):
    uid: Optional[str] = Field(index=True, primary_key=True)
    ig_id: Optional[str] = Field(index=True)
    name: Optional[str] = Field(index=True)
    subscribe_users: Optional[list[str]] = None
    full_name: Optional[str] = None
    is_private: Optional[bool] = False
    is_verified: Optional[bool] = False
    head_pic_url: Optional[str] = None
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "follower_instagram"


class FollowerThreads(JsonModel, index=True):
    uid: Optional[str] = Field(index=True, primary_key=True)
    name: Optional[str] = Field(index=True)
    profile_url: Optional[str] = None
    head_pic_url: Optional[str] = None
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "follower_threads"