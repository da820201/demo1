import datetime
import time
from redis_om import (
    EmbeddedJsonModel,
    JsonModel,
    Field,
    Migrator,
    get_redis_connection
)

from typing import Optional
from enum import Enum


redis = get_redis_connection(port=6380, db=0)


class ScapyStatus(Enum):
    Off = 0
    Running = 1
    Waiting = 2


class FacebookGroup(EmbeddedJsonModel):
    uid: Optional[str] = Field(index=True, primary_key=True)
    name: Optional[str] = Field(index=True)
    scapy_status: Optional[int] = 0
    cookies_str: Optional[str] = None
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "sf_user_facebook_group"


class FacebookPage(EmbeddedJsonModel):
    uid: Optional[str] = Field(index=True, primary_key=True)
    name: Optional[str] = Field(index=True)
    profile_url: Optional[str] = None
    head_pic_url: Optional[str] = None
    followers: Optional[list[str]] = []
    scapy_status: Optional[int] = 0
    cookies_str: Optional[str] = None
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "sf_user_facebook_page"


class Facebook(EmbeddedJsonModel):
    dtsg: Optional[str] = None
    uid: Optional[str] = Field(index=True, primary_key=True)
    name: Optional[str] = Field(index=True)
    profile_url: Optional[str] = None
    pages: Optional[list[FacebookPage]] = None
    groups: Optional[list[FacebookGroup]] = None
    cookies_str: Optional[str] = None
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "sf_user_facebook"


class Instagram(EmbeddedJsonModel):
    uid: Optional[str] = Field(index=True, primary_key=True)
    name: Optional[str] = Field(index=True)
    account: Optional[str] = Field(index=True, default=None)
    password: Optional[str] = None
    from_fb: Optional[bool] = True
    scapy_status: Optional[int] = 0
    cookies_str: Optional[str] = None
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "sf_account_instagram"



class Threads(EmbeddedJsonModel):
    uid: Optional[str] = Field(index=True, primary_key=True)
    name: Optional[str] = Field(index=True)
    scapy_status: Optional[int] = 0
    cookies_str: Optional[str] = None
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "sf_account_threads"


class UserAccount(JsonModel):
    uid: str = Field(index=True, primary_key=True)
    account: str = Field(index=True)
    password: str
    facebook: Optional[list[Facebook]] = None
    instagram: Optional[list[Instagram]]  = None
    threads: Optional[list[Threads]] = None
    birthday: Optional[datetime.date]
    phone_number: Optional[str]
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "sf_meta_account"