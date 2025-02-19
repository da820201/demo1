from pydantic import BaseModel
from enum import Enum


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
