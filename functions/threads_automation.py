import logging
import requests
import sys
import os
import time
import redis
import random
import re
import json
from urllib.parse import parse_qs
from bs4 import BeautifulSoup
from schemes.general_schemes import ThreadsUserInfo, ThreadsFriendshipStatus, ThreadsSiteData
from schemes.sf_account_schemes import SFMetaAccount, Threads
from schemes.user_schemes import UserAccount, UserThreads
from schemes.follower_schemes import FollowerInstagram
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
    "accept-language": "en,zh-CN;q=0.9,zh;q=0.8,zh-TW;q=0.7,ckb;q=0.6",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://www.threads.net",
    "priority": "u=1, i",
    "referer": "https://www.threads.net/@theradoll",
    "sec-ch-prefers-color-scheme": "light",
    "sec-ch-ua": "\"Not(A:Brand\";v=\"99\", \"Google Chrome\";v=\"133\", \"Chromium\";v=\"133\"",
    "sec-ch-ua-full-version-list": "\"Not(A:Brand\";v=\"99.0.0.0\", \"Google Chrome\";v=\"133.0.6943.99\", \"Chromium\";v=\"133.0.6943.99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": "\"\"",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-ch-ua-platform-version": "\"15.3.1\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "x-asbd-id": "359341",
    "x-bloks-version-id": "c16e9c7c1a812f60d22c42530908301bfdaebb593260b5e4c267e3b8371a1113",
    "x-csrftoken": "WG1PpdNpk4cpjIGhXCpcvyQD5BprM8kl",
    "x-fb-friendly-name": "BarcelonaFriendshipsFollowersTabRefetchableQuery",
    "x-fb-lsd": "I8ucRd9QtV35vsOpyFsREx",
    "x-ig-app-id": "238260118697367"
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

    "Sec-Ch-Ua": "\"Microsoft Edge\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",  # 下载粉丝头像的时候会换
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0"  # 下载粉丝头像的时候会换
}



def get_threads_followers(
        cookies,
        session: requests.session,
        uid: str,
        cursor: str = "",
        total_req: int = 1,
) -> bool | dict:
    url = "https://www.threads.com/graphql/query"

    return try_cookies(
        session,
        url=url,
        headers=headers,
        cookie_str=cookies,
        cursor=cursor,
        total_req=total_req, max_trys=6
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

    if __spin_r:
        result = ThreadsSiteData(
            av=av.group(1),
            rev=rev.group(1),
            lsd=lsd.group(1),
            __spin_r=__spin_r.group(1),
            __spin_b=__spin_b.group(1),
            __spin_t=__spin_t.group(1),
            __hsi=hsi.group(1),
            jazoest=jazoest.group(1),
            fb_dtsg=dtsg.group(1),
            hs=haste_session.group(1),
            app_id=app_id.group(1),
            vid=vid.group(1),
            csrf_token=csrf_token.group(1)
        )

        return result
    return False


def get_user_id(
        cookies,
        username: str,
        session: requests.session,
        timeout: float = 5
) -> tuple[ThreadsUserInfo, ThreadsSiteData] or tuple[False, False]:
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-TW,zh;q=0.9",
        "cache-control": "max-age=0",
        "dpr": "2",
        "priority": "u=0, i",
        "sec-ch-prefers-color-scheme": "light",
        "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
        "sec-ch-ua-full-version-list": "\"Chromium\";v=\"136.0.7103.114\", \"Google Chrome\";v=\"136.0.7103.114\", \"Not.A/Brand\";v=\"99.0.0.0\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": "\"\"",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-ch-ua-platform-version": "\"15.4.0\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "viewport-width": "1180"
    }
    headers.update({"cookie": cookies})
    url = f"https://www.threads.com/@{username}/"
    res = session.get(url=url, headers=headers).text
    user_info_data = extract_threads_user_info(res)
    user_site_data = extract_site_data(res)
    user_site_data.uid = user_info_data.pk
    return user_info_data, user_site_data


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
    tab = login(
        account=account_data.account,
        password=aes_decrypt(account_data.password),
        tab_=tab
    )

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


def get_followers(
        account_data: SFMetaAccount,
        cookies: str,
        uid,
        crawler_data: ThreadsSiteData,
        user_data: UserInstagram,
        session: requests.session,
        timeout: float = 5
):
    cursor, ok_fans_num, total_req = "", 0, 1
    headers = {
        "accept": "*/*",
        "accept-language": "zh-TW,zh;q=0.9",
        "content-type": "application/x-www-form-urlencoded",
        "priority": "u=1, i",
        "sec-ch-prefers-color-scheme": "light",
        "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
        "sec-ch-ua-full-version-list": "\"Chromium\";v=\"136.0.7103.114\", \"Google Chrome\";v=\"136.0.7103.114\", \"Not.A/Brand\";v=\"99.0.0.0\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": "\"\"",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-ch-ua-platform-version": "\"15.4.0\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-asbd-id": "359341",
        "x-bloks-version-id": "cf39c6377e026a1760665d37cfc1b31a93ae150e5d202da0aa6d36af9f0749fd",
        "x-csrftoken": "sBD4Py5CNWugwGZ2DIdTmkosjd90859F",
        "x-fb-friendly-name": "BarcelonaFriendshipsFollowersTabQuery",
        "x-fb-lsd": "M2LDCAcPD0qxRYodVH85TM",
        "x-ig-app-id": "238260118697367",
        "x-root-field-name": "fetch__XDTUserDict"
    }
    headers.update(crawler_data.dict(exclude_unset=True))
    headers.update({"cookie": cookies})
    payload = (
        f"av=17841474859429560"
        f"&__user=0"
        f"&__a=1"
        f"&__req=ji"
        f"&__hs=20230.HYP%3Abarcelona_web_pkg.2.1...0"
        f"&dpr=2"
        f"&__ccg=EXCELLENT"
        f"&__rev=1023085245"
        f"&__s=jd4at2%3Ascqrpm%3Axss97y"
        f"&__hsi=7507174385136303460"
        f"&__dyn=7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W0qa0FE2awgo9oO0n24oaEd82lwv89k2C1Fwc60D85m1mzXwae4UaEW0Loco5G0zK5o4q0HU1IEGdwtU2ewbS1LwTwKG0hq1Iwqo9EpwUwiQ1mwLwHxW17y9UjgbVE-19xW1Vwn85SU7y"
        f"&__csr=ghh5Wex75tTbICDbllQzuC_NkGpp2yAFogKUKV5VayoV2XAVVuqpypbGvKbQAULw05Eny8kw11d6z0Gb4G3u7A1oxol81lw8-8N2xd1ongC6o7W29xe2S1cPwvK3G0J8z4UjgmS0Nrx3hpA1Gw8iUjw3OU12U2oK1bK5VUmw54w2dE3HwLwU41y5N0dS3EEo2bk9wcd04uwenwtodUzw6fxTSKaVxE5a2i4af41i15AFzsh4a4Qfogg1HU0Ky096ycM02c7gghk"
        f"&__hsdp=gbR9NikZ52kJyIMi0Wyq3xx31pc9bEEH9tMOMxaz4kO2W9Bsby0-G5E9Eo5NoiclE6wE9b6QoM4Mid6E4x8EEjhQ4iNP2oN8o19a4BzoCfl1i7VERxh3oqwn4u5pU4K3Ki4o5C2q2Wbwpob8y58a8O2uuEKq5U26wlEb98lye32m2Sp0"
        f"&__hblp=0mawfS9yA8zovyoJ3AAEe8J1DF0HwgUe84iqayVbzXCwzwDxmm3W8xy4AF8O8y99U-q6EaojwHG7otwAg5e1ew42wcu2O8gjCKEOdXCxicgOEix2Wxm5E8UnVE88S4Qu7Ub98C3ufBwJCg"
        f"&__comet_req=29&fb_dtsg=NAftAvIGjS2E7kW9v62eWhPgh0h193JBxqHY81AaFFCS7dN036ya-yw%3A17853667720085245%3A1747898157&jazoest=25937&lsd=M2LDCAcPD0qxRYodVH85TM"
        f"&__spin_r=1023085245"
        f"&__spin_b=trunk"
        f"&__spin_t=1747900244"
        f"&__crn=comet.threads.BarcelonaProfileThreadsColumnRoute"
        f"&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=BarcelonaFriendshipsFollowersTabQuery"
        f"&variables=%7B%22first%22%3A{20}%2C%22userID%22%3A%22{uid}%22%2C%22__relay_internal__pv__BarcelonaIsLoggedInrelayprovider%22%3Atrue%2C%22__relay_internal__pv__BarcelonaIsCrawlerrelayprovider%22%3Afalse%2C%22__relay_internal__pv__BarcelonaHasDisplayNamesrelayprovider%22%3Afalse%2C%22__relay_internal__pv__BarcelonaShouldShowFediverseListsrelayprovider%22%3Atrue%7D"
        f"&server_timestamps=true"
        f"&doc_id=29257825927198293"
    )
    payload = {k: v[0] for k, v in parse_qs(payload).items()}
    payload.update(crawler_data.dict())
    while True:
        targets = get_threads_followers(cookies=cookies, uid=uid, cursor=cursor, session=session)
        for k, v in targets.items():
            print(k, v)
        print(len(targets["users"]))
        for target in targets["users"]:
            uid = generate_uid(target["id"])
            if uid in user_data.followers:
                logging.info(f"{target['id']}: {uid} 已經存在於該帳號中，不儲存該追蹤者")
                continue
            head_pic = download_head_pic(target['profile_pic_url'])
            FollowerInstagram(
                uid=uid,
                ig_id=target["id"],
                name=target["username"],
                head_pic=head_pic[1:],
                full_name=target["full_name"],
                is_private=target["is_private"],
                is_verified=target["is_verified"],
                create_time=time.time(),
                update_time=time.time(),
            ).save()
            user_data.followers.append(uid)
            user_data.save()
            # time.sleep(random.uniform(3, 6))
        ok_fans_num += 1
        if total_req > 5:
            logging.info(f"單次循環超過2次，為了盡快抓到其他鏈結的追蹤者，本次先跳出本鏈結，等下一次循環繼續抓取...\n")
            # break

        total_req += 1
        logging.info('分頁間隔，隨機休眠20~50秒\n')
        time.sleep(random.randint(20, 50))


if __name__ == "__main__":
    # Test Step 1: 創建爬蟲帳戶
    r = redis.Redis(host="localhost", port=6380, db=0, decode_responses=True)
    # 測試創建爬蟲帳戶
    # create_sf_account(
    #     account=account_,
    #     password=aes_encrypt(password_),
    #     threads=Threads(
    #         uid=generate_uid(account=account_),
    #         name=account_,
    #         account=account_,
    #         password=aes_encrypt(password_),
    #         from_fb=False
    #     )
    # )
    accounts = get_sf_account(account_)
    # cookies = get_threads(account_data=accounts)
    # accounts.social_medias.threads.cookies_str = cookies
    # accounts.social_medias.threads.update_time = time.time()
    # accounts.save()
    print(accounts.social_medias.threads.cookies_str)

    # Test Step 2: 創建使用者帳戶
    session = requests.session()
    user_account = "xuu_.__@gmail.com"
    threads_username = "xuu_.__"
    user_password = "nothisaccount"

    user = UserAccount.get(generate_uid(account=account_))
    # user = UserAccount(
    #     uid=generate_uid(account=account_),
    #     account=user_account,
    #     password=aes_encrypt(user_password),
    #     phone_number="1234567890",
    # )
    # user.save()


    # Test Step 3: 校驗使用者帳戶資料與補全
    user_info_data, user_site_data = get_user_id(
        cookies=accounts.social_medias.threads.cookies_str,
        username=threads_username,
        session=session
    )

    user_threads = UserThreads(
        uid=generate_uid(account=user_site_data.uid),
        name=threads_username,
        allow_crawlers=[accounts.uid]
    )
    user_threads.save()

    if user_threads.uid not in user.threads:
        user.threads.append(user_threads.uid)
        user.save()

    # user_data = get_ig_user_info_by_graph_api(
    #     session=session,
    #     username=user_threads.name,
    #     uid=data.uid,
    #     crawler_data=data,
    # )

    # Test Step 4: 測試利用爬蟲帳號取得客戶IG的追蹤者
    get_followers(
        account_data=accounts,
        cookies=accounts.social_medias.instagram.cookies_str,
        uid=user_site_data.uid,
        user_data=user_threads,
        session=session,
        crawler_data=user_site_data,
        timeout=5
    )

    # Test Step 5: 測試利用爬蟲帳號取得貼文資訊

