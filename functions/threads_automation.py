import logging
import typing
from sqlite3.dbapi2 import threadsafety

import redis_om
import requests
import sys
import os
import time
import redis
import threading
import random
import re
import json
from multiprocessing import Pipe
from urllib.parse import parse_qs
from bs4 import BeautifulSoup
from schemes.graph_api_response_threads_schemes import Data
from data.constants import Path, ThreadsPayload, ThreadsHeaders
from schemes.general_schemes import ThreadsUserInfo, ThreadsFriendshipStatus, ThreadsSiteData
from schemes.sf_account_schemes import SFMetaAccount, Threads
from schemes.user_schemes import UserAccount, UserThreads
from schemes.follower_schemes import FollowerThreads
from functions.meta_account_function import get_sf_account, create_sf_account, generate_uid
from functions.utils import try_cookies, aes_decrypt, aes_encrypt, download_head_pic
from DrissionPage import ChromiumPage, Chromium
from DrissionPage import ChromiumOptions
from fcaptcha.twocaptcha import TwoCaptcha
from data.account_data import api_key, email_
from data.account_data import account_, password_


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"  # 設定時間格式
)
api_url = "https://www.threads.net/graphql/query"
headers = {
    "accept": "*/*",
    "accept-language": "zh-TW,zh;q=0.9",
    "content-type": "application/x-www-form-urlencoded",
    "priority": "u=1, i",

    "sec-ch-prefers-color-scheme": "light",
    "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-full-version-list": '"Chromium";v="136.0.7103.114", "Google Chrome";v="136.0.7103.114", "Not.A/Brand";v="99.0.0.0"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": "",
    "sec-ch-ua-platform": "macOS",
    "sec-ch-ua-platform-version": "15.4.0",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "x-fb-friendly-name": "BarcelonaFriendshipsFollowersTabRefetchableQuery",
}
down_header = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Priority": "u=0, i",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",

    "Sec-Ch-Ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',  # 下载粉丝头像的时候会换
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0"  # 下载粉丝头像的时候会换
}


def print_background_package(tab_: ChromiumPage.get_tab):
    for packet in tab_.listen.steps():
        response = packet.response
        url = packet.url
        method = packet.method


def get_threads_followers(
        cookies,
        session: requests.session,
        user_site_data: ThreadsSiteData,
        user_data: UserThreads,
        data,
        cursor: str = "",
        total_req: int = 1,
) -> bool | dict:
    headers.update(
        {
            "x-fb-lsd": user_site_data.lsd,
            "x-ig-app-id": user_site_data.app_id,
            "x-csrftoken": user_site_data.csrf_token,
            "x-bloks-version-id": user_site_data.vid,
            "referer": f"https://www.threads.com/@{user_data.name}",
            "origin": f"https://www.threads.com",
        }
    )
    return try_cookies(
        session,
        url=Path.ThreadsGraphqlQuery,
        headers=headers,
        cookie_str=cookies,
        cursor=cursor,
        total_req=total_req,
        data=data,
        max_trys=6
    )


def is_in_main_page(
        tab_: ChromiumPage.get_tab,
        timeout: float = 5,
        micro_timeout: float = 0.25
) -> bool:
    if not tab_.url == "https://www.threads.com/":
        return False

    num_of_bottom = 5

    web_form_bar = "x7c8izy x6s0dn4 xktjril x1g7m7fl x78zum5 xdt5ytf x5yr21d x17qophe x5mc7k8 x1plvlek xryxfnj xixxii4 x13vifvy x120sd54 x1vjfegm"
    web_form_buttons = "x6s0dn4 x78zum5 xng8ra xijvv9e xl56j7k x71s49j x13dflua x11xpdln xz4gly6 x1247r65"
    if tab_.wait.ele_displayed(f"@@class={web_form_bar}", timeout=timeout):
        side_bar_selector = tab_.ele(f"@@class={web_form_bar}")

        if len(side_bar_selector.eles(f"@@class={web_form_buttons}", timeout=timeout)) >= num_of_bottom:
            logging.info("in main page")
            return True
    logging.info("not in main page")
    return False


def have_login_button(tab_: ChromiumPage.get_tab, timeout: float = 5):
    login_button_class = "x1i10hfl x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x18d9i69 x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x1lku1pv x1a2a7pz x6s0dn4 x1a2cdl4 xnhgr82 x1qt0ttw xgk8upj x9f619 x3nfvp2 x1s688f x90ne7k xl56j7k x193iq5w x1swvt13 x1pi30zi x1g2r6go x12w9bfk x11xpdln xz4gly6 x87ps6o xuxw1ft x19kf12q x111bo7f x1vmvj1k x45e8q x3tjt7u x35z2i1 x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x178xt8z xm81vs4 xso031l xy80clv xteu7em"
    login_button = tab_.wait.ele_displayed(
        f"@@class={login_button_class}@@role=link", timeout=timeout
    )
    if login_button:
        logging.info("have login button")
        return False

    return True


def click_login_button(tab_: ChromiumPage.get_tab, timeout: float = 5):
    login_button_class = "x1i10hfl x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x18d9i69 x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x1lku1pv x1a2a7pz x6s0dn4 x1a2cdl4 xnhgr82 x1qt0ttw xgk8upj x9f619 x3nfvp2 x1s688f x90ne7k xl56j7k x193iq5w x1swvt13 x1pi30zi x1g2r6go x12w9bfk x11xpdln xz4gly6 x87ps6o xuxw1ft x19kf12q x111bo7f x1vmvj1k x45e8q x3tjt7u x35z2i1 x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x178xt8z xm81vs4 xso031l xy80clv xteu7em"
    login_button = tab_.wait.ele_displayed(
        f"@@class={login_button_class}@@role=link", timeout=timeout
    )
    if login_button:
        login_button.click()
        logging.info("click login button")

    return True


def have_another_login_button(tab_: ChromiumPage.get_tab, timeout: float = 5):
    another_login_button_class = "x1lliihq x1plvlek xryxfnj x1n2onr6 x1ji0vk5 x18bv5gf x193iq5w xeuugli x1fj9vlw x13faqbe x1vvkbs x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1i0vuye xjohtrz xo1l8bm x12rw4y6 x2b8uid xqui205"
    another_login_button = tab_.wait.ele_displayed(
        f"@@class={another_login_button_class}", timeout=timeout
    )
    if another_login_button:
        logging.info("have another login button")
        return False

    return True


def click_another_login_button(tab_: ChromiumPage.get_tab, timeout: float = 5):
    another_login_button_class = "x1lliihq x1plvlek xryxfnj x1n2onr6 x1ji0vk5 x18bv5gf x193iq5w xeuugli x1fj9vlw x13faqbe x1vvkbs x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1i0vuye xjohtrz xo1l8bm x12rw4y6 x2b8uid xqui205"
    another_login_button = tab_.wait.ele_displayed(
        f"@@class={another_login_button_class}", timeout=timeout
    )
    if another_login_button:
        another_login_button.click()
        logging.info("click another login button")
        return False

    return True


def is_init_ig_to_threads(tab_: ChromiumPage.get_tab, timeout: float = 5):
    init_profile_set_class = "x1i10hfl x9f619 xggy1nq xtpw4lu x1tutvks x1s3xk63 x1s07b3s x1ypdohk x5yr21d xdj266r x11i5rnm xat24cr x1mh8g0r x1w3u9th x1a2a7pz xexx8yu x4uap5 x18d9i69 xkhd6sd x10l6tqk x17qophe x13vifvy xh8yej3"
    init_profile_continue_button_class = "x1i10hfl x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x18d9i69 x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x1lku1pv x1a2a7pz x6s0dn4 x9f619 x3nfvp2 x1s688f xl56j7k x193iq5w x1swvt13 x1pi30zi x1g2r6go x12w9bfk x11xpdln xz4gly6 x87ps6o xuxw1ft x19kf12q xdd8jsf x111bo7f x1vmvj1k x45e8q x3tjt7u x35z2i1 x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x178xt8z xm81vs4 xso031l xy80clv xteu7em x1tlxs6b x1g8br2z x1gn5b1j x230xth xh8yej3"
    if tab_.wait.ele_displayed(
        f"@@class={init_profile_set_class}", timeout=timeout
    ) and  tab_.wait.ele_displayed(
        f"@@class={init_profile_continue_button_class}", timeout=timeout
    ):
        init_profile_continue_button = tab_.ele(f"@@class={init_profile_continue_button_class}", timeout=timeout)
        init_profile_continue_button.click()
        logging.info("in init profile")
        return True
    return False


def is_init_threads_join_button(tab_: ChromiumPage.get_tab, timeout: float = 5):
    init_threads_join_button_class = "x1i10hfl x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x18d9i69 x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x1lku1pv x1a2a7pz x6s0dn4 x9f619 x3nfvp2 x1s688f xl56j7k x193iq5w x1swvt13 x1pi30zi x1g2r6go x12w9bfk x11xpdln xz4gly6 x87ps6o xuxw1ft x19kf12q xdd8jsf x111bo7f x1vmvj1k x45e8q x3tjt7u x35z2i1 x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x178xt8z xm81vs4 xso031l xy80clv xteu7em x1tlxs6b x1g8br2z x1gn5b1j x230xth xh8yej3"
    if tab_.wait.ele_displayed(
        f"@@class={init_threads_join_button_class}@@role=button", timeout=timeout
    ):
        buttons = tab_.eles(f"@@class={init_threads_join_button_class}@@role=button")
        if len(buttons) == 2:
            init_threads_join_button = buttons[-1]
            init_threads_join_button.click()
            logging.info("click init threads join button")
            return True
    return False


def logout(
        tab_: ChromiumPage.get_tab,
        timeout: float = 5,
        micro_timeout: float = 0.25
) -> bool:
    more_box_class = "xg7h5cd x91k8ka"
    more_box = tab_.wait.ele_displayed(
        f"@@class={more_box_class}", timeout=timeout
    )

    if not more_box:
        logging.info("no more box")
        return False

    more_box = tab_.eles(
        f"@@class={more_box_class}", timeout=timeout
    )[-1]

    more_box.click()

    time.sleep(micro_timeout)
    logout_button_class = "x1i10hfl x1qjc9v5 xjbqb8w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xeuugli x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x3nfvp2 x1q0g3np x87ps6o x1lku1pv x1a2a7pz x6bh95i x1re03b8 x1hvtcl2 x3ug3ww xyi19xy x1ccrb07 xtf3nb5 x1pc53ja xjwf9q1 x1g2khh7 x1ye3gou xn6708d xyinxu5 x1g2r6go x12w9bfk x11xpdln xh8yej3 xk4oym4 x1eos6md"
    logout_button = tab_.wait.ele_displayed(
        f"@@class={logout_button_class}@@role=button", timeout=timeout
    )
    if not logout_button:
        logging.info("no logout button")
        return False
    logout_button = tab_.eles(
        f"@@class={logout_button_class}@@role=button", timeout=timeout
    )[-1]
    logout_button.click()

    # 會短暫跳出一個請重新登入的視窗，給他五秒理論上就可以了。
    time.sleep(timeout)

    return True


def login(
        account: str,
        password: str,
        tab_: ChromiumPage.get_tab,
        timeout: float = 5,
        micro_timeout: float = 0.25
) -> ChromiumPage.get_tab:
    placeholder_class = "x1i10hfl x9f619 xggy1nq xtpw4lu x1tutvks x1s3xk63 x1s07b3s x1kdt53j x1a2a7pz x90nhty x1v8p93f xogb00i x16stqrj x1ftr3km xyi19xy x1ccrb07 xtf3nb5 x1pc53ja x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x178xt8z xm81vs4 xso031l xy80clv xp07o12 xjohtrz x1a6qonq xyamay9 x1pi30zi x1l90r2v x1swvt13 x1yc453h xh8yej3 x1e899rk x1sbm3cl x1rpcs5s x1c5lum3 xd5rq6m"
    submit_button_class = "x6s0dn4 xrvj5dj xofrnu2 x1o2pa38 xh8yej3"

    account_placeholder = tab_.wait.ele_displayed(
        f"@@class={placeholder_class}@@autocomplete=username", timeout=timeout
    )
    if account_placeholder:
        account_placeholder.clear()
        account_placeholder.input(account)
        logging.info("account input success")
    else:
        raise Exception("Account placeholder not found")

    time.sleep(micro_timeout)

    password_placeholder = tab_.ele(
        f"@@class={placeholder_class}@@autocomplete=current-password"
    )

    if password_placeholder:
        password_placeholder.clear()
        password_placeholder.input(password)
        tab_.ele(f"@@class={submit_button_class}").click()
    else:
        raise Exception("Password placeholder not found")
    return tab_


def extract_threads_user_info(html: str) -> ThreadsUserInfo or dict:
    # 抽出 user 區塊 JSON 字串
    user_start = re.search(r'"user"\s*:\s*{', html)
    if not user_start:
        return {"error": "找不到 user 起始位置"}
    start_index = html.find('{', user_start.start())

    # 2. 花括號平衡掃描
    brace_count = 0
    in_string = False
    escape = False
    end_index = None

    for i in range(start_index, len(html)):
        char = html[i]
        if char == '"' and not escape:
            in_string = not in_string
        elif not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_index = i + 1
                    break
        escape = (char == '\\' and not escape)

    if end_index is None:
        return {"error": "花括號配對失敗"}

    json_like = html[start_index:end_index]
    print("json_like", json_like)
    try:
        fixed = re.sub(r'\\/', '/', json_like)
        result = json.loads(fixed)
        friendship_status = result.pop("friendship_status", None)
        if friendship_status:
            if isinstance(friendship_status, list):
                friendship_status = friendship_status[0]
            return ThreadsUserInfo(
                **result,
                friendship_status=ThreadsFriendshipStatus(
                    **friendship_status
                )
            )
        return ThreadsUserInfo(**result, friendship_status=ThreadsFriendshipStatus())
    except Exception as e:
        return {"error": f"JSON解析錯誤: {str(e)}"}


def extract_site_data(html: str) -> ThreadsSiteData or False:
    dtsg = re.search(r'"DTSGInitialData".*?"token"\s*:\s*"([^"]+)"', html, re.DOTALL)
    lsd = re.search(r'"LSD".*?"token"\s*:\s*"([^"]+)"', html, re.DOTALL)
    __spin_r = re.search(r'"__spin_r"\s*:\s*(?:"([^"]+)"|(\d+))', html)
    av = re.search(r'"NON_FACEBOOK_USER_ID"\s*:\s*(?:"([^"]+)"|(\d+))', html)
    rev = re.search(r'"server_revision"\s*:\s*(?:"([^"]+)"|(\d+))', html)
    csrf_token = re.search(r'"csrf_token"\s*:\s*(?:"([^"]+)"|(\d+))', html)
    __spin_t = re.search(r'"__spin_t"\s*:\s*(?:"([^"]+)"|(\d+))', html)
    __spin_b = re.search(r'"__spin_b"\s*:\s*"([^"]+)"', html)
    hsi = re.search(r'"hsi"\s*:\s*"([^"]+)"', html)
    app_id = re.search(r'"X-IG-App-ID"\s*:\s*(?:"([^"]+)"|(\d+))', html)
    haste_session = re.search(r'"haste_session"\s*:\s*"([^"]+)"', html)
    jazoest = re.search(r'jazoest=([0-9]+)', html)
    vid = re.search(r'"versioningID"\s*:\s*(?:"([^"]+)"|(\d+))', html)
    maid = re.search(r'"machine_id"\s*:\s*(?:"([^"]+)"|(\d+))', html)

    if __spin_r:
        result = ThreadsSiteData(
            av=av.group(1),
            rev=str(rev.group(0).split(":")[1]),
            lsd=lsd.group(1),
            spin_r=__spin_r.group(0).split(":")[1].replace("'", ""),
            spin_b=__spin_b.group(1),
            spin_t=__spin_t.group(0).split(":")[1].replace("'", ""),
            hsi=hsi.group(1),
            jazoest=jazoest.group(1),
            fb_dtsg=dtsg.group(1),
            hs=haste_session.group(1),
            app_id=app_id.group(1),
            vid=vid.group(1),
            csrf_token=csrf_token.group(1),
            machine_id=maid.group(1),
        )
        return result
    return False


def get_user_site_data(
    cookies,
    username: str,
    session: requests.session,
    timeout: float = 5
) -> ThreadsSiteData:
    headers = ThreadsHeaders.GetUserProfile
    headers.update({"cookie": cookies})
    url = f"https://www.threads.com/@{username}/"
    res = session.get(url=url, headers=headers).text
    user_site_data = extract_site_data(res)
    return user_site_data


def get_user_info(
        cookies,
        username: str,
        session: requests.session,
        timeout: float = 5
) -> ThreadsUserInfo or False:
    headers = ThreadsHeaders.GetUserProfile
    headers.update({"cookie": cookies})
    url = f"https://www.threads.com/@{username}/"
    res = session.get(url=url, headers=headers).text
    user_info_data = extract_threads_user_info(res)
    return user_info_data


def login_for_cookies(
        account_data: SFMetaAccount,
        timeout: float = 5
):
    co = ChromiumOptions()
    co.mute(True)
    co.set_pref(
        "profile.default_content_setting_values",
        {
            'notifications': 2  # 隱藏 chromedriver 的通知
        }
    )
    co.set_pref("credentials_enable_service", False)
    co.set_pref("profile.password_manager_enabled", False)
    co.headless(False)
    co.incognito(True)

    c = Chromium(addr_or_opts=co)
    tab = c.latest_tab
    tab.get(f'https://www.threads.com/')
    if is_in_main_page(tab, timeout=timeout):
        if not logout(tab_=tab):
            logout(
                tab_=tab
            )

    if is_in_main_page(tab, timeout=timeout):
        if not have_login_button(tab_=tab):
            click_login_button(
                tab_=tab
            )
        elif not have_another_login_button(tab_=tab):
            click_another_login_button(
                tab_=tab
            )
    print(aes_decrypt(account_data.password))
    tab = login(
        account=account_data.account,
        password="983b0ca2@!",
        tab_=tab
    )
    #
    if not is_in_main_page(tab, timeout=timeout):
        is_init_ig_to_threads(tab_=tab)
        time.sleep(timeout)
        is_init_threads_join_button(tab_=tab)

    if is_in_main_page(tab, timeout=timeout):
        logging.info("login success")

    logging.info(f"Cookies: {tab.cookies().as_str()}")

    return tab.cookies().as_str()


def get_threads(account_data: SFMetaAccount, timeout: float = 5):
    cookies = login_for_cookies(account_data, timeout)
    return cookies


def build_payload(
        crawler_data: ThreadsSiteData,
        threads_uid: str,
        cursor: int = 0,
        query_count: int = 10
) -> dict:
    payload_base = ThreadsPayload.PayloadBase
    payload_base = {k: v[0] for k, v in parse_qs(payload_base).items()}
    payload_base["av"] = crawler_data.av
    payload_base["fb_dtsg"] = crawler_data.fb_dtsg
    payload_base["lsd"] = crawler_data.lsd
    payload_base["__hsi"] = crawler_data.hsi
    payload_base["__hs"] = crawler_data.hs
    payload_base["__spin_r"] = crawler_data.spin_r
    payload_base["__spin_b"] = crawler_data.spin_b
    payload_base["__spin_t"] = crawler_data.spin_t
    payload = {
        "fb_api_req_friendly_name": "BarcelonaFriendshipsFollowersTabRefetchableQuery",
        "variables": '{"after":"' + str(cursor) + '","first":"' + str(query_count) + '","id":"' + str(threads_uid) +
                     '","__relay_internal__pv__BarcelonaIsLoggedInrelayprovider":true,'
                     '"__relay_internal__pv__BarcelonaIsCrawlerrelayprovider":false,'
                     '"__relay_internal__pv__BarcelonaHasDisplayNamesrelayprovider":false,'
                     '"sort_order":"TOP"}',
        "server_timestamps": "true",
        # "doc_id": "9226067564176291"
        "doc_id": "29248147168134162"
    }
    print(f"from {cursor} to {cursor + query_count}")
    payload_base.update(payload)
    return payload_base


def get_followers(
        cookies: str,
        user_id,
        user_site_data: ThreadsSiteData,
        user_data: UserThreads,
        session: requests.session,
        timeout: float = 5
):
    wait_time_min, wait_time_max = 5, 10
    cursor, total_req, query_count = 0, 1, 25
    while True:
        if cursor == user_data.num_of_followers:
            break
        cursor = int(user_data.num_of_followers) if int(user_data.num_of_followers) < int(cursor) else int(cursor)

        payload = build_payload(
            user_site_data, user_id, cursor, query_count=int(user_data.num_of_followers) - cursor
            if int(user_data.num_of_followers) < (cursor + query_count)
            else query_count
        )
        targets = get_threads_followers(
            cookies=cookies, user_site_data=user_site_data, data=payload,
            cursor=str(cursor), user_data=user_data,
            session=session,
        )
        targets = Data(**targets)
        followers_ = targets.data.fetch__XDTUserDict.followers
        if followers_.page_info.end_cursor:
            cursor = int(followers_.page_info.end_cursor)
        else:
            cursor = user_data.num_of_followers
            logging.info("no more followers")
        if followers_.edges is None:
            logging.info("no more followers")
            break

        for target in followers_.edges:
            node = target.node
            uid = generate_uid(node.pk)
            if uid in user_data.followers:
                logging.info(f"{node.pk}: {uid} 已經存在於該帳號中，不儲存該追蹤者")
                continue
            head_pic = download_head_pic(node.profile_pic_url)
            fs = FollowerThreads(
                uid=uid,
                threads_id=node.pk,
                name=node.username,
                head_pic=head_pic[1:] if head_pic else "",
                head_pic_url=node.profile_pic_url,
                full_name=node.full_name,
                is_private=node.text_post_app_is_private,
                is_verified=node.is_verified,
                create_time=time.time(),
                update_time=time.time(),
            )
            fs.save()
            user_data.followers.append(uid)
            user_data.save()

        print("followers num", len(user_data.followers))
        logging.info(f"分頁間隔，隨機休眠{wait_time_min}~{wait_time_max}秒\n")
        time.sleep(random.randint(wait_time_min, wait_time_max))


if __name__ == "__main__":
    # Test Step 1: 創建爬蟲帳戶
    r = redis.Redis(host="localhost", port=6380, db=0, decode_responses=True)
    # 測試創建爬蟲帳戶
    create_sf_account(
        account=account_,
        password=aes_encrypt(password_),
        threads=Threads(
            uid=generate_uid(account=account_),
            name=account_,
            account=account_,
            password=aes_encrypt(password_),
            from_fb=False
        )
    )
    # accounts = get_sf_account(account_, decrypt=False)
    # print(accounts)
    # cookies = get_threads(account_data=accounts)
    # accounts.social_medias.threads.cookies_str = cookies
    # accounts.social_medias.threads.update_time = time.time()
    # accounts.save()
    # print(accounts.social_medias.threads.cookies_str)
    accounts = get_sf_account(account_, decrypt=False)
    co = ChromiumOptions()
    co.mute(True)
    co.set_pref(
        "profile.default_content_setting_values",
        {
            'notifications': 2  # 隱藏 chromedriver 的通知
        }
    )
    co.set_pref("credentials_enable_service", False)
    co.set_pref("profile.password_manager_enabled", False)
    co.headless(False)
    co.incognito(True)

    c = Chromium(addr_or_opts=co)
    tab = c.latest_tab
    # tab.get(f'https://www.threads.com/')
    a = tab.cookies().as_str()
    print(a)
    accounts.social_medias.threads.cookies_str = a
    accounts.social_medias.threads.update_time = time.time()
    accounts.save()
    # Test Step 2: 被動監聽取得CSR/DYN
    # share_dict = {}
    # p = threading.Thread(target=print_background_package, args=(share_dict, ))
    # p.start()

    # Test Step 2: 創建使用者帳戶
    session = requests.session()
    user_account = "snsconsul.kaori@gmail.com"
    threads_username = "snsconsul.kaori"
    user_password = "nothisaccount"
    #. 如果找不到UID 就自己創建一個
    try:
        user = UserAccount.get(generate_uid(account=account_))
    except redis_om.model.NotFoundError:
        user = UserAccount(
            uid=generate_uid(account=account_),
            account=user_account,
            password=aes_encrypt(user_password),
            phone_number="1234567890",
        )
        user.save()

    # Test Step 3: 校驗使用者帳戶資料與補全
    user_data = get_user_info(
        cookies=accounts.social_medias.threads.cookies_str,
        username=threads_username,
        session=session
    )
    user_site_data = get_user_site_data(
        cookies=accounts.social_medias.threads.cookies_str,
        username=threads_username,
        session=session
    )

    if generate_uid(user_data.pk) in user.threads:
        user_threads = UserThreads.get(generate_uid(user_data.pk))
    else:
        user_threads = UserThreads(
            uid=generate_uid(account=user_data.pk),
            name=threads_username,
            full_name=user_data.full_name,
            allow_crawlers=[accounts.uid],
            num_of_followers=user_data.follower_count,
            is_private=user_data.text_post_app_is_private,
            biography=user_data.biography,
            threads_id=user_data.pk
        )
        user_threads.save()
    #
    # if user_threads.uid not in user.threads:
    #     user.threads.append(user_threads.uid)
    #     user.save()

    # Test Step 4: 測試利用爬蟲帳號取得客戶IG的追蹤者
    get_followers(
        cookies=accounts.social_medias.threads.cookies_str,
        user_id=user_threads.threads_id,
        user_data=user_threads,
        session=session,
        user_site_data=user_site_data,
        timeout=5
    )

    # Test Step 5: 測試利用爬蟲帳號取得貼文資訊

