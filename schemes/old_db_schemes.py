import datetime
import time

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class DBShellAccount(BaseModel):
    id: int = 0
    acc_type: int = 1
    account: str = "daniel.guan@shell.fans"
    password: str = ""
    nickname: Optional[str] = "daniel.guan"
    cookies_str: Optional[str] = ""
    fb_dtsg: Optional[str] = ""
    status: Optional[bool] = True
    is_del: Optional[bool] = False


class DbUrlSchema(BaseModel):
    id: Optional[int] = Field(None, description="ID")
    local_userid: int = Field(..., description="本系统用户ID")
    plate: Optional[int] = Field(1, description="平台：1facebook；2ig；6抖音；7 threader")
    zhua: int = Field(0, description="是否抓取：0不抓，1抓")
    url: str = Field(..., description="前端提交过来的 URL")
    u_id: Optional[str] = Field('', description="URL 對應的 ID")
    type: Optional[int] = Field(None, description="1粉絲專頁、2公開社團、3私密社團、4ig連結")
    sa_id: Optional[int] = Field(None, description="shell_account 表的帳號 ID")
    sa_name: Optional[str] = Field(None, description="使用帳號名稱")
    head_pic: Optional[str] = Field(None, description="頭像 URL")
    name: Optional[str] = Field("待抓取", description="名稱")
    profile_desc: Optional[str] = Field(None, description="簡介")
    status: Optional[int] = Field(0, description="URL 狀態：9無法抓取")
    post_status: Optional[int] = Field(0, description="貼文抓取狀態")
    post_page: Optional[str] = Field(None, description="抓到哪一頁了")
    fans_cookie: Optional[str] = Field(None, description="抓粉絲用的 cookie")
    fans_status: Optional[int] = Field(0, description="粉絲抓取狀態")
    fans_page: Optional[str] = Field(None, description="粉絲抓到哪一頁")
    fans_ut: Optional[int] = Field(None, description="粉絲抓取完成時間")
    create_time: Optional[int] = Field(None, description="建立時間（timestamp）")
    update_at: Optional[int] = Field(None, description="更新時間（timestamp）")
    is_active: Optional[int] = Field(1, description="是否有效：1有效，0失效")

    class Config:
        orm_mode = True



if __name__ == "__main__":
    print(
        DbUrlSchema(
            id=0,
            local_userid=0,
            zhua=1,
            url="",
            create_time=int(time.time()),
            fans_ut=int(time.time()),
            update_at=int(time.time()),
        ).model_dump()
    )

    print(DBShellAccount(id=0, acc_type=1))

