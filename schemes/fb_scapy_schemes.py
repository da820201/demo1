import datetime
import time

from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class Platform(Enum):
    Facebook: "Facebook"
    IG: "IG"
    Threads: "Threads"


class ManagerAccount(BaseModel):
    id: int
    account: str
    password: str
    platform: List[Platform] = []
    cookies: Optional[str] = ""  # 抓取資料用的Cookies
    is_active: Optional[bool] = True  # 帳戶是否啟動


class PlatformBase(BaseModel):
    id: int
    name: Optional[str] = ""
    is_active: Optional[bool] = True
    head_picture: Optional[str] = ""
    profile_desc: Optional[str] = ""
    manager_account: Optional[(List[ManagerAccount])] = []

    create_time: Optional[datetime.datetime] = datetime.datetime.utcnow
    update_time: Optional[datetime.datetime] = datetime.datetime.utcnow


class FacebookPageCollectorStatus(BaseModel):
    total_followers: Optional[int] = 0
    number_of_get: Optional[int] = 0
    run_collector_interval_time: Optional[float] = 86400  # 1 day
    collector_done_time: Optional[float] = time.time  #  上次粉絲專頁資料收集完成的時間,為方便計算也避免二次轉換,直接使用timestamp
    update_time: Optional[datetime.datetime] = datetime.datetime.utcnow


class FacebookPage(PlatformBase):
    page_id: str
    facebook_collector_status: FacebookPageCollectorStatus


class IG(PlatformBase):
    ig_id: str
    facebook_collector_status: FacebookPageCollectorStatus

