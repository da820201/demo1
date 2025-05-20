import datetime
import time
from schemes.follower_schemes import FollowerFacebook, FollowerInstagram, FollowerThreads
from schemes.sf_account_schemes import SFMetaAccount
from redis_om import (
    EmbeddedJsonModel,
    JsonModel,
    Field,
    get_redis_connection
)

from typing import Optional
from enum import Enum


redis = get_redis_connection(port=6380, db=0)


class ScapyStatus(Enum):
    Off = 0
    Running = 1
    Waiting = 2


class UserFacebookGroup(JsonModel, index=True):
    uid: Optional[str] = Field(index=True, primary_key=True)
    name: Optional[str] = Field(index=True)
    group_id: Optional[str] = None
    scapy_status: Optional[int] = 0
    is_allow_crawler: Optional[bool] = 0  # 該Group是否與許爬蟲訪問
    allow_crawlers: Optional[list[str]] = []  # 允許的爬蟲名單
    members: Optional[list[str]] = []  # 社團成員
    num_of_members: Optional[int] = 0  # 社團人數
    posts: Optional[list] = []  # 社團貼文
    num_of_posts: Optional[int] = 0  #  社團貼文數
    cookies_str: Optional[str] = None
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "user_facebook_group"


class UserFacebookPage(JsonModel, index=True):
    uid: Optional[str] = Field(index=True, primary_key=True)
    name: Optional[str] = Field(index=True)
    page_id: Optional[str] = None
    dtsg: Optional[str] = None
    profile_url: Optional[str] = None
    head_pic_url: Optional[str] = None
    allow_crawlers: Optional[list[str]] = []  # 允許的爬蟲名單
    followers: Optional[list[str]] = []  # 粉絲專頁追蹤者
    num_of_followers: Optional[int] = 0  # 粉絲專頁追蹤者數
    posts: Optional[list] = []  # 粉絲專頁貼文
    num_of_posts: Optional[int] = 0  # 粉絲專頁貼文數
    scapy_status: Optional[int] = 0
    cookies_str: Optional[str] = None
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "user_facebook_page"


class UserFacebook(JsonModel, index=True):
    uid: Optional[str] = Field(index=True, primary_key=True)
    name: Optional[str] = Field(index=True)
    fb_id: Optional[str] = None
    profile_url: Optional[str] = None
    head_pic_url: Optional[str] = None
    pages: Optional[list[str]] = None
    groups: Optional[list[str]] = None
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "user_facebook"


class UserInstagram(JsonModel, index=True):
    uid: Optional[str] = Field(index=True, primary_key=True)
    ig_id: Optional[str] = None
    name: Optional[str] = Field(index=True, default=None)
    scapy_status: Optional[int] = 0
    is_allow_crawler: Optional[bool] = False  # 該IG是否與許爬蟲訪問
    allow_crawlers: Optional[list[str]] = []  # 允許的爬蟲名單
    followers: Optional[list[str]] = []  # 追蹤者名單
    num_of_followers: Optional[int] = 0  # 追蹤者數
    courses: Optional[list] = []
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "user_instagram"



class UserThreads(JsonModel, index=True):
    uid: Optional[str] = Field(index=True, primary_key=True)
    name: Optional[str] = Field(index=True)
    scapy_status: Optional[int] = 0
    is_allow_crawler: Optional[bool] = 0   # 該Threads是否與許爬蟲訪問
    allow_crawlers: Optional[list[str]] = []  # 允許的爬蟲名單
    followers: Optional[list[str]] = []  # 追蹤者名單
    num_of_followers: Optional[int] = 0  # 追蹤者數
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "user_threads"


class UserAccount(JsonModel, index=True):
    uid: str = Field(index=True, primary_key=True)
    account: str = Field(index=True)
    password: str
    facebook: Optional[list[str]] = None
    instagram: Optional[list[str]]  = None
    threads: Optional[list[str]] = None
    birthday: Optional[float] = Field(default_factory=lambda: time.time())
    phone_number: Optional[str]
    create_time: Optional[float] = Field(default_factory=lambda: time.time())
    update_time: Optional[float] = Field(default_factory=lambda: time.time())

    class Meta:
        database = redis
        global_key_prefix: str = "user"