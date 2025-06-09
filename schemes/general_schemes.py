from pydantic import BaseModel, Field
from typing import Optional


class GeneralSchemes(BaseModel):
    sid: str
    account: str
    post_url: str = ""
    videos: list = []
    images: list = []
    reel: list = []
    describe: str = ""
    user_mood: list = []
    tags: list = []
    get_time: float


class MetaBaseSiteData(BaseModel):
    uid: Optional[str] = None
    av: Optional[str] = None
    lsd: Optional[str] = None
    rev: Optional[str] = None
    jazoest: str
    fb_dtsg: str
    hs: str
    app_id: str
    vid: str
    csrf_token: str


class IGSiteData(MetaBaseSiteData):
    uid: Optional[str] = None
    spin_r: str or int
    spin_b: str
    spin_t: str or int
    hsi: str


class ThreadsSiteData(MetaBaseSiteData):
    uid: Optional[str] = None
    spin_r: str
    spin_b: str
    spin_t: str
    hsi: str
    machine_id: str


class IGUserInfo(BaseModel):
    is_private: Optional[bool] = False
    username: Optional[str] = None
    pk: Optional[str] = None
    profile_pic_url: Optional[str] = None
    full_name: Optional[str] = None
    follower_count: Optional[int] = 0
    following_count: Optional[int] = 0
    city_name: Optional[str] = None
    is_business: Optional[bool] = False
    is_verified: Optional[bool] = False
    biography: Optional[str] = None


class ThreadsFriendshipStatus(BaseModel):
    followed_by: Optional[bool] = False
    following: Optional[bool] = False
    blocking: Optional[bool] = False
    outgoing_request: Optional[bool] = False
    incoming_request: Optional[bool] = False


class ThreadsUserInfo(BaseModel):
    text_post_app_is_private: Optional[bool] = False
    username: Optional[str] = None
    pk: Optional[str] = None
    profile_pic_url: Optional[str] = None
    hd_profile_pic_versions: Optional[list | dict | str] = Field(
        default_factory=lambda x: x if x is None else
        x[0].get("url")
        if isinstance(x, list) else
        x.get("url")
    )
    full_name: Optional[str] = None
    follower_count: Optional[int] = 0
    is_verified: Optional[bool] = False
    biography: Optional[str] = None
    text_app_last_visited_time: Optional[int] = 0
    friendship_status: Optional[list | dict | ThreadsFriendshipStatus] = Field(
        default_factory= lambda x: x
        if x is None or isinstance(x, ThreadsFriendshipStatus) else
        ThreadsFriendshipStatus(**x[0])
        if isinstance(x, list) else
        ThreadsFriendshipStatus(**x)
    )