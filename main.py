import time
import threading as td
import logging
from functions.fb_function import check_has_login_and_registry_button, check_uid, go_to_videos_page, go_to_post_page, go_to_reels_page
from DrissionPage import ChromiumOptions
from DrissionPage import common, Chromium
from conf import is_mute
from schemes.es_db_scjemes import es, index_name


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"  # 設定時間格式
)


co = ChromiumOptions()
co.mute(is_mute)
c = Chromium(addr_or_opts=co)
tab = c.latest_tab

uid = "ParamountTaiwan"
data = go_to_post_page(c, uid, get_post_count=10, timeout=1.5, micro_timeout=0.15)
for doc in data:
    es.index(index=index_name, id=doc.sid, document=doc.dict())
[print(i) for i in data]


uid = "xcwork"
data = go_to_post_page(c, uid, get_post_count=10, timeout=1.5, micro_timeout=0.15)
for doc in data:
    es.index(index=index_name, id=doc.sid, document=doc.dict())
[print(i) for i in data]

