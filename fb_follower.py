import redis
import time
import json
from schemes import old_db_schemes
from functions import facebook_login_and_deal_recapture


putong_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8,zh-TW;q=0.7",
    "Cache-Control": "max-age=0",
    "Dpr": "2",
    "Priority": "u=0, i",
    "Sec-Ch-Prefers-Color-Scheme": "light",
    "Sec-Ch-Ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
    "Sec-Ch-Ua-Full-Version-List": "\"Google Chrome\";v=\"125.0.6422.176\", \"Chromium\";v=\"125.0.6422.176\", \"Not.A/Brand\";v=\"24.0.0.0\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Model": "\"\"",
    "Sec-Ch-Ua-Platform": "\"macOS\"",
    "Sec-Ch-Ua-Platform-Version": "\"14.5.0\"",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Viewport-Width": "1260"
}
pd = ""
all_url = [
    old_db_schemes.DbUrlSchema(
        id=0,
        local_userid=0,
        zhua=1,
        url="https://www.facebook.com/Nine.gods.Onmyoji",
        create_time=int(time.time()),
        fans_ut=int(time.time()-99999),
        update_at=int(time.time()),
    ).model_dump()
]


if __name__ == '__main__':
    redis_server = redis.Redis(
        host='127.0.0.1',
        port=6379,
        db=0,
        decode_responses=True
    )

    # TODO 雖然解掉了 Recapture1 的驗證，但有可能遇到 Recapture2 的驗證，這還需要想辦法處理。
    redis_name = "shellfans_fb_manager_account"
    email_ = "daniel.guan@shell.fans"
    data = facebook_login_and_deal_recapture.login_and_get_cookies(
        email_,
        _password=pd,
    )

    # TODO 這邊要補一段，確認粉專有該管理員之後需要切換Facebook帳號->粉專並且取出Cookies
    page_index = facebook_login_and_deal_recapture.check_is_facebook_page_manager(
        data, "365914203781117"
    )

    # TODO 這邊要補一段，登入進行通知檢查，並做到自動接受粉專管理員邀請

    # redis_server.hset(
    #     redis_name,
    #     key=email_,
    #      value=data.json()
    # )
    # print(json.loads(redis_server.hget(redis_name, email_)))

