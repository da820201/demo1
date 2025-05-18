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


class Facebook(EmbeddedJsonModel):
    dtsg: Optional[str] = None
    uid: Optional[str] = Field(index=True, primary_key=True)
    name: Optional[str] = Field(index=True)
    scapy_status: Optional[int] = 0
    cookies_str: Optional[str] = None
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "sf_account_facebook"


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


class SocialMedias(EmbeddedJsonModel):
    uid: str = Field(index=True, primary_key=True)
    facebook: Optional[Facebook] = None
    instagram: Optional[Instagram] = None
    threads: Optional[Threads] = None

    class Meta:
        database = redis


class SFMetaAccount(JsonModel, index=True):
    uid: str = Field(index=True, primary_key=True)
    account: str = Field(index=True)
    password: str
    social_medias: Optional[SocialMedias] = None
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "sf_meta_account"


class UpdateInstagram(EmbeddedJsonModel):
    uid: Optional[str] = None
    name: Optional[str] = None
    account: Optional[str] = None
    password: Optional[str] = None
    from_fb: Optional[bool] = None
    scapy_status: Optional[int] = None
    cookies_str: Optional[str] = None
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "sf_account_instagram"


class UpdateSocialMedias(EmbeddedJsonModel):
    uid: Optional[str] = None
    facebook: Optional[Facebook] = None
    instagram: Optional[UpdateInstagram] = None
    threads: Optional[Threads] = None

    class Meta:
        database = redis


class UpdateSFMetaAccount(JsonModel):
    uid: Optional[str] = None
    account: Optional[str] = None
    password: Optional[str] = None
    social_medias: Optional[UpdateSocialMedias] = None
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "sf_meta_account"


Migrator().run()


