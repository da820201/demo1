from pydantic import BaseModel


class VideoData(BaseModel):
    uid: str
    url: str
    describe: str
    user_mood: list = []


class VideoDatas(BaseModel):
    key: str
    data: VideoData

