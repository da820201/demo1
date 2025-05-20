import logging
import requests
import sys
import os
import time
import redis
import random
import re
from urllib.parse import parse_qs
from bs4 import BeautifulSoup
from schemes.general_schemes import IGSiteData, IGUserInfo
from schemes.user_schemes import UserAccount, UserInstagram
from schemes.sf_account_schemes import SFMetaAccount, Instagram
from schemes.follower_schemes import FollowerInstagram
from functions.meta_account_function import get_sf_account, create_sf_account, generate_uid
from functions.utils import try_cookies, aes_decrypt, aes_encrypt, download_head_pic
from DrissionPage import ChromiumPage, Chromium
from DrissionPage import ChromiumOptions
from fcaptcha.twocaptcha import TwoCaptcha
from data.account_data import api_key, email_
from data.account_data import account_, password_


_email = email_
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
api_key = os.getenv(api_key["env"], api_key["key"])
solver = TwoCaptcha(api_key)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"  # 設定時間格式
)

# recapture_url = "https://www.facebook.com/captcha/tfbimage/"
headers = {
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,de-AT;q=0.6,de;q=0.5,it;q=0.4,de-DE;q=0.3,en-GB;q=0.2,en-IE;q=0.1",
    "Dpr": "1",
    "Referer": "https://www.instagram.com/vp/following/",
    "Sec-Ch-Prefers-Color-Scheme": "light",
    "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Microsoft Edge\";v=\"120\"",
    "Sec-Ch-Ua-Full-Version-List": "\"Not_A Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"120.0.6099.234\", \"Microsoft Edge\";v=\"120.0.2210.144\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Model": "\"\"",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Ch-Ua-Platform-Version": "\"10.0.0\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Viewport-Width": "2512",
    "X-Asbd-Id": "129477",
    "X-Csrftoken": "S00MMTu9F7yiqAAwV18B2QEyUDEjmiGm",
    "X-Ig-App-Id": "936619743392459",
    "X-Ig-Www-Claim": "hmac.AR1lJHcc0gF0WSQS_kos2-kfKhxzkKnKkqCYkIhfqzqppOXa",
    "X-Requested-With": "XMLHttpRequest"
}


def get_ig_followers(
        cookies,
        uid: str,
        cursor: str = "",
        total_req: int = 1
) -> bool | dict:
    url = f"https://www.instagram.com/api/v1/friendships/{uid}/followers/?count=25&search_surface=follow_list_page"
    if cursor:
        url = f"{url}&max_id={cursor}"

    session = requests.session()
    return try_cookies(
        session,
        url=url,
        headers=headers,
        cookie_str=cookies,
        cursor=cursor,
        total_req=total_req, max_trys=6
    )


def get_ig_posts(
        cookies,
        uid: str,
        cursor: str = "",
        total_req: int = 1
) -> bool | dict:
    url = f"https://www.instagram.com/api/v1/feed/user/{uid}/?count=12&max_id={cursor}"
    if cursor:
        url = f"{url}&max_id={cursor}"

    session = requests.session()
    return try_cookies(
        session,
        url=url,
        headers=headers,
        cookie_str=cookies,
        cursor=cursor,
        total_req=total_req, max_trys=6
    )

def is_in_ig_main_page(
        tab_: ChromiumPage.get_tab,
        timeout: float = 5,
        micro_timeout: float = 0.25
):
    mobile_form_bar = "x9f619 xjbqb8w x78zum5 x168nmei x13lgxp2 x5pf9jr xo71vjh xixxii4 x1ey2m1c x1plvlek xryxfnj x1c4vz4f x2lah0s xdt5ytf xqjyukv x1qjc9v5 x1oa3qoh x1nhvcw1 xg7h5cd xh8yej3 xhtitgo x6w1myc x1jeouym"
    mobile_form_buttons  = "x9f619 xxk0z11 xii2z7h x11xpdln x19c4wfv xvy4d1p"
    num_of_bottom = 6
    if tab_.wait.ele_displayed(f"@@class={mobile_form_bar}", timeout=timeout):
        bottom_bar_selector = tab_.ele(f"@@class={mobile_form_bar}")
        if len(bottom_bar_selector.eles(f"@@class={mobile_form_buttons}", timeout=timeout)) >= num_of_bottom:
            logging.info("in main page")
            return True

    pad_form_bar = "x1iyjqo2 xh8yej3"
    pad_form_buttons = "x9f619 x3nfvp2 xr9ek0c xjpr12u xo237n4 x6pnmvc x7nr27j x12dmmrz xz9dl7a xn6708d xsag5q8 x1ye3gou x80pfx3 x159b3zp x1dn74xm xif99yt x172qv1o x10djquj x1lhsz42 xzauu7c xdoji71 x1dejxi8 x9k3k5o xs3sg5q x11hdxyr x12ldp4w x1wj20lx x1lq5wgf xgqcy7u x30kzoy x9jhf4c"
    if tab_.wait.ele_displayed(f"@@class={pad_form_bar}", timeout=timeout):
        side_bar_selector = tab_.ele(f"@@class={pad_form_bar}")

        if len(side_bar_selector.eles(f"@@class={pad_form_buttons}", timeout=timeout)) >= num_of_bottom:
            logging.info("in main page")
            return True

    web_form_bar = "x1iyjqo2 xh8yej3"
    web_form_buttons = "x9f619 x3nfvp2 xr9ek0c xjpr12u xo237n4 x6pnmvc x7nr27j x12dmmrz xz9dl7a xn6708d xsag5q8 x1ye3gou x80pfx3 x159b3zp x1dn74xm xif99yt x172qv1o x10djquj x1lhsz42 xzauu7c xdoji71 x1dejxi8 x9k3k5o xs3sg5q x11hdxyr x12ldp4w x1wj20lx x1lq5wgf xgqcy7u x30kzoy x9jhf4c"
    if tab_.wait.ele_displayed(f"@@class={web_form_bar}", timeout=timeout):
        side_bar_selector = tab_.ele(f"@@class={web_form_bar}")

        if len(side_bar_selector.eles(f"@@class={web_form_buttons}", timeout=timeout)) >= num_of_bottom:
            logging.info("in main page")
            return True
    return False


def is_in_account_onetap(
        tab_: ChromiumPage.get_tab,
        timeout: float = 5,
        micro_timeout: float = 0.25
):
    save_button_class = " _acan _acap _acas _aj1- _ap30"
    ignore_button_class = "x1i10hfl xjqpnuy xa49m3k xqeqjp1 x2hbi6w xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x1lku1pv x1a2a7pz x6s0dn4 xjyslct x1ejq31n xd10rxx x1sy0etr x17r0tee x9f619 x1ypdohk x1f6kntn xwhw2v2 xl56j7k x17ydfre x2b8uid xlyipyv x87ps6o x14atkfc xcdnw81 x1i0vuye xjbqb8w xm3z3ea x1x8b98j x131883w x16mih1h x972fbf xcfux6l x1qhh985 xm0m39n xt0psk2 xt7dq6l xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x1n5bzlp x173jzuc x1yc6y37"

    save_button = tab_.wait.ele_displayed(
        f"@@class={save_button_class}", timeout=timeout
    )
    if save_button:
        ignore_button = tab_.wait.ele_displayed(
            f"@@class={ignore_button_class}", timeout=timeout
        )
        if ignore_button:
            tab_.ele(f"@@class={ignore_button_class}").click()
        logging.info("is in account onetap page")
        return True
    else:
        return False


def login(
        account: str,
        password: str,
        tab_: ChromiumPage.get_tab,
        timeout: float = 5,
        micro_timeout: float = 0.25
) -> ChromiumPage.get_tab:
    tab_.get(f'https://www.instagram.com/')
    login_account_class = "_aa4b _add6 _ac4d _ap35"
    login_password_class = "_aa4b _add6 _ac4d _ap35"
    element_account_name = "username"
    element_password_name = "password"
    submit_button_class = "x9f619 xjbqb8w x78zum5 x168nmei x13lgxp2 x5pf9jr xo71vjh x1n2onr6 x1plvlek xryxfnj x1c4vz4f x2lah0s xdt5ytf xqjyukv x1qjc9v5 x1oa3qoh x1nhvcw1"

    account_placeholder = tab_.wait.ele_displayed(
        f"@@class={login_account_class}@@name={element_account_name}", timeout=timeout
    )
    if account_placeholder:
        account_placeholder.clear()
        account_placeholder.input(account)
        logging.info("account input success")
    else:
        raise Exception("Account placeholder not found")

    time.sleep(micro_timeout)

    password_placeholder = tab_.ele(
        f"@@class={login_password_class}@@name={element_password_name}"
    )

    if password_placeholder:
        password_placeholder.clear()
        password_placeholder.input(password)
        tab_.ele(f"@@class={submit_button_class}").click()
    else:
        raise Exception("Password placeholder not found")
    return tab_


def logout(
        tab_: ChromiumPage.get_tab,
        timeout: float = 5,
        micro_timeout: float = 0.25
) -> bool:
    more_box_class = "html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1hl2dhg x16tdsg8 x1vvkbs x4k7w5x x1h91t0o x1h9r5lt x1jfb8zj xv2umb2 x1beo9mf xaigb6o x12ejxvf x3igimt xarpa2k xedcshv x1lytzrv x1t2pt76 x7ja8zs x1qrby5j"

    more_box = tab_.wait.ele_displayed(
        f"@@class={more_box_class}", timeout=timeout
    )

    if not more_box:
        logging.info("no more box")
        return False

    more_box = tab_.eles(
        f"@@class={more_box_class}", timeout=timeout
    )[-1]

    more_button_class = "x9f619 x3nfvp2 xr9ek0c xjpr12u xo237n4 x6pnmvc x7nr27j x12dmmrz xz9dl7a xn6708d xsag5q8 x1ye3gou x80pfx3 x159b3zp x1dn74xm xif99yt x172qv1o x10djquj x1lhsz42 xzauu7c xdoji71 x1dejxi8 x9k3k5o xs3sg5q x11hdxyr x12ldp4w x1wj20lx x1lq5wgf xgqcy7u x30kzoy x9jhf4c"
    more_box.ele(f"@@class={more_button_class}").click()

    time.sleep(micro_timeout)
    logout_button_class = "x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x87ps6o x1lku1pv x1a2a7pz x1dm5mii x16mil14 xiojian x1yutycm x1lliihq x193iq5w xh8yej3"
    logout_button_role = "button"
    logout_button = tab_.wait.ele_displayed(
        f"@@class={logout_button_class}@@role={logout_button_role}", timeout=timeout
    )
    if not logout_button:
        logging.info("no logout button")
        return False
    logout_button = tab_.eles(f"@@class={logout_button_class}@@role={logout_button_role}", timeout=timeout)[-1]
    logout_button.click()

    # 會短暫跳出一個請重新登入的視窗，給他五秒理論上就可以了。
    time.sleep(timeout)

    return True


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
    if is_in_ig_main_page(tab, timeout=timeout):
        if not logout(tab_=tab):
            raise Exception("logout fail")
    tab = login(account=account_data.account, password=aes_decrypt(account_data.password), tab_=tab)
    is_in_account_onetap(tab, timeout=timeout)

    is_in_ig_main_page(tab, timeout=timeout)
    logging.info(f"Cookies: {tab.cookies().as_str()}")
    return tab.cookies().as_str()


# 定義函數：從 DTSGInitialData 中提取 token
def extract_site_data(html: str) -> IGSiteData or False:
    dtsg = re.search(r'"DTSGInitialData".*?"token"\s*:\s*"([^"]+)"', html, re.DOTALL)
    lsd = re.search(r'"LSDLSD".*?"token"\s*:\s*"([^"]+)"', html, re.DOTALL)
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
    print(lsd)
    print(av, rev, app_id, vid, csrf_token)
    if __spin_r:
        result = IGSiteData(
            av=av.group(1),
            rev=rev.group(1),
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
) -> IGSiteData:
    profile_url = f"https://www.instagram.com/{username}/"
    headers["Cookie"] = cookies
    result = session.get(url=profile_url, headers=headers).text
    # print(result)
    site_data = extract_site_data(result)
    # 使用BS4解析
    soup = BeautifulSoup(result, "html.parser")
    scripts = soup.find_all("script")
    for script in scripts:
        if script.string and ('profile_id' in script.string):
            try:
                # 嘗試直接從中擷取 profile_id
                match = re.search(r'"profile_id"\s*:\s*"(\d+)"', script.string)
                if match:
                    site_data.uid =  match.group(1)
                    return site_data
            except Exception as e:
                continue

    return False


def get_ig_user_info_by_graph_api(
        session: requests.session,
        username,
        uid,
        crawler_data: IGSiteData,
        timeout=5
) -> IGUserInfo:
    #  使用Graph API獲取用戶信息，這個版本比較合法
    headers = {
        "accept": "*/*",
        "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "origin": f"https://www.instagram.com",
        "referer": f"https://www.instagram.com/{username}/",
        "content-type": "application/x-www-form-urlencoded", "priority": "u=1, i",
        "sec-ch-prefers-color-scheme": "light",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-full-version-list": '"Chromium";v="136.0.7103.113", "Google Chrome";v="136.0.7103.113", "Not.A/Brand";v="99.0.0.0"',
        "sec-ch-ua-mobile": "?0", "sec-ch-ua-model": "", "sec-ch-ua-platform": "macOS",
        "sec-ch-ua-platform-version": "15.4.0", "sec-fetch-dest": "empty", "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-asbd-id": None,
        "x-bloks-version-id": None,
        "x-csrftoken": None,
        "x-fb-friendly-name": "PolarisProfilePageContentQuery",
        "x-fb-lsd": None,
        "x-ig-app-id": None, "x-root-field-name": "fetch__XDTUserDict"
    }
    headers.update(
        {
            "x-bloks-version-id": crawler_data.vid,
            "x-ig-app-id": crawler_data.app_id,
            "x-csrftoken": crawler_data.csrf_token,
            "x-fb-lsd": crawler_data.lsd
        }
    )
    payload = f"av=17841474347125111&__d=www&__user=0&__a=1&__req=1a&__hs=20227.HYP%3Ainstagram_web_pkg.2.1...1&dpr=2&__ccg=EXCELLENT&__rev=1022957439&__s=smucnh%3Aimq43g%3Aw1vpw0&__hsi=7506036922928637977&__dyn=7xeUjG1mxu1syUbFp41twpUnwgU7SbzEdF8aUco2qwJxS0DU2wx609vCwjE1EE2Cw8G11wBz81s8hwGxu786a3a1YwBgao6C0Mo2swtUd8-U2zxe2GewGw9a361qwuEjUlwhEe87q0oa2-azqwt8d-2u2J0bS1LwTwKG1pg2fwxyo6O1FwlA3a3zhA6bwIxeUnAwHxW1oxe6UaU3cyUC4o16UswFw&__csr=jjgvT7gR3Yt5N58kSyIRljAfFll8OERelqCheQArpe_KlWjgFamnQjnhAOaQ-Zvh6EGhe8HBjFd4jiGHGjJ3ax2ZbACGj-i_8UF1efyGK_DVRXz98ZkmF98yFHD-GBKjF5GbhZ5CCB-EC9UHBgKqi9y9UG5ooxeAmqeUxa8DGRXg01iUU1g920fB04dJwyfDgGOwbK0WyambgkU2mDgd86OaChUO4U4q3C4O0867E0WG05q80x63i0i-1PyFGwDwE8TeUiwFA9a6o2JgaFQ0sfe0iQyx90rVA0HUcRg2mw1Vp02n949g062y0dHw60w0LDw&__hsdp=geXA4h4PiTk9GMyJ3W2M_AISOkAk4BmwhgV2QBFy9k8iOe2lb20We40pxgux2bwsO4wIzU-6ok9AoswNoKh3oryfwyxu3SQ4y3U4i2GfxO6EO3268gx-68KEmwaSEnwio3gwrU3LwibwcO0h-1lUswNwgU8E5O1oxa0Co1vS7o7a362S3pwQw921i-2uexS4o8o4aexe5zw&__hblp=0mUvwBxu7onwIgao6N3UpBUnwcq4QbzUgBAJ0RzomwMwxwzCGq16gkybCxa8yfzEjxt0xxle2mi9gyEbqyUrypqwAzUO2maghBx27UngKGyEycwhoC1gGqmawipE39wRwVwTw962m18K0KoCtwh87Sm1lByEuwBUswNwGxyUuwn8qwQy8iw9C0ZE6a9xJBxu2Z0gocoG2a6osod88WxS1bAx-2W2Gegsx66GK2jz8WejgS5zK&__comet_req=7&fb_dtsg=NAftilM-2UH6osDDeAPJlLKco1FiKdwRj-U9gxxg689eV393EqPJlSA%3A17843683195144578%3A1747633494&jazoest=26096&lsd=9v5jNVzlz9uzviLGT6-0zc&__spin_r=1022957439&__spin_b=trunk&__spin_t=1747635408&__crn=comet.igweb.PolarisProfilePostsTabRoute&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=PolarisProfilePageContentQuery&variables=%7B%22id%22%3A%22{uid}%22%2C%22render_surface%22%3A%22PROFILE%22%7D&server_timestamps=true&doc_id=9661599240584790"
    user_info_url = "https://www.instagram.com/graphql/query"
    payload = {k: v[0] for k, v in parse_qs(payload).items()}

    payload.update(crawler_data.dict())
    response = session.post(user_info_url, headers=headers, data=payload)
    ig_user_data = IGUserInfo(**response.json()['data']['user'])
    return ig_user_data


def get_user_info_by_vi_api(
    username,
    cookies,
) -> IGUserInfo:
    #  使用IG V1 API，這比較不合法
    ig_headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Priority": "u=1, i",
        "Referer": "https://www.instagram.com/netaporter/followers/",
        "Sec-Ch-Prefers-Color-Scheme": "light",
        "Sec-Ch-Ua": "\"Chromium\";v=\"124\", \"Microsoft Edge\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
        "Sec-Ch-Ua-Full-Version-List": "\"Chromium\";v=\"124.0.6367.207\", \"Microsoft Edge\";v=\"124.0.2478.105\", \"Not-A.Brand\";v=\"99.0.0.0\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Model": "\"\"",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Sec-Ch-Ua-Platform-Version": "\"10.0.0\"",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
        "X-Asbd-Id": "129477",
        "X-Csrftoken": "8I0dg8w30nKUDNnGdc2pc20jzjZKGEv",
        "X-Ig-App-Id": "936619743392459",
        "X-Ig-Www-Claim": "hmac.AR1lJHcc0gF0WSQS_kos2-kfKhxzkKnKkqCYkIhfqzqppIuP",
        "X-Requested-With": "XMLHttpRequest"
    }

    putong_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8,zh-TW;q=0.7",
        "Cache-Control": "max-age=0",
        "Cookie": "sb=Mw6eZeWHJjcypUCF_pisW-nT; ps_n=1; ps_l=1; wl_cbv=v2%3Bclient_version%3A2551%3Btimestamp%3A1720163737; vpd=v1%3B736x414x3; dpr=1; locale=zh_TW; datr=ri60ZijyQ14lkWOESIUlN5WT; usida=eyJ2ZXIiOjEsImlkIjoiQXNodzN1cjZ4ZTFrNyIsInRpbWUiOjE3MjMxMDU5MzR9; c_user=61557016683521; xs=15%3A0J0vQ8XNsEddPw%3A2%3A1723112853%3A-1%3A10701; wd=1133x908; fr=1vxgzgFsQj4eqovc7.AWVJ8SHI352ARRbGSx-K6BzQn-I.BmtJmx..AAA.0.0.BmtJ2h.AWUfGrHOFaI; presence=C%7B%22t3%22%3A%5B%5D%2C%22utc3%22%3A1723112867820%2C%22v%22%3A1%7D",
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
    res = requests.get(url=f"https://www.instagram.com/{username}/", headers=putong_headers).text
    # print(res.encode().decode('raw_unicode_escape'))

    ig_id = re.findall('"props":\{"id":"(.*?)"', res, re.S)[0]

    ig_headers['Cookie'] = cookies
    res_info = requests.get(
        url=f'https://www.instagram.com/api/v1/users/{ig_id}/',
        headers=ig_headers
    ).json()
    return IGUserInfo(**res_info["user"])

def get_posts(
        cookies,
        target_uid: str = "6770296405",  # "5951385086"
        timeout: float = 5
):
    cursor, ok_post_num, total_req = "", 0, 1

    while True:
        targets = get_ig_posts(cookies=cookies, uid=target_uid, cursor=cursor)
        for k, v in targets.items():
            print(k, v)
        print(len(targets["users"]))
        user_ig = UserInstagram.get(generate_uid(account=target_uid))
        try:
            if not targets['items']:
                logging.info(f"空数据，可能是没数据了，也可能是对方的链接没公开，修改状态为2")
                if user_ig.post_status is not False:
                    user_ig.posts_status = False
                    user_ig.save()
                    logging.info('贴子抓取状态更新为不抓取，post_status=False')
                break
        except:
            logging.info(f"响应数据崩溃，跳出本链接")
            break

        # 更新状态
        if user_ig.post_status is not True:
            user_ig.posts_status = True
            user_ig.save()
            logging.info('贴子抓取状态更新为开始抓取，post_status=1')


def get_followers(
        cookies,
        user_data: UserInstagram,
        timeout: float = 5
):
    cursor, ok_fans_num, total_req = "", 0, 1
    while True:
        targets = get_ig_followers(cookies=cookies, uid=user_data.ig_id, cursor=cursor)
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
            user_ig.followers.append(uid)
            user_ig.save()
            # time.sleep(random.uniform(3, 6))
            ok_fans_num += 1

        if "next_max_id" not in targets:
            logging.info("該帳號設置不能查看更多了，只有該帳號本身能看全部追蹤者")
            logging.info(f"total: {ok_fans_num}")
            break

        cursor = targets["next_max_id"]
        logging.info(f"下一頁標籤：{targets['next_max_id']}")

        # if u_info['fans_status'] != 0:
        #     # 连续3页的贴文都存在就认为已经完事儿了，就跳出
        #     if total_req == 2 and ok_fans_num == 12:
        #         logging.info(f"连续3页的粉丝都存在，说明没有新增，跳出本链接，并设置抓取完成 fans_status=2")
        #         logging.info(f"粉丝抓取状态更新为抓取完成，fans_status=2")
        #         break

        if total_req > 5:
            logging.info(f"單次循環超過2次，為了盡快抓到其他鏈結的追蹤者，本次先跳出本鏈結，等下一次循環繼續抓取...\n")
            break

        total_req += 1
        logging.info('分頁間隔，隨機休眠20~50秒\n')
        time.sleep(random.randint(20, 50))


if __name__ == '__main__':
    # Test Step 1: 創建爬蟲帳戶
    r = redis.Redis(host="localhost", port=6380, db=0, decode_responses=True)
    # 測試創建爬蟲帳戶
    # create_sf_account(
    #     account=account_,
    #     password=aes_encrypt(password_),
    #     instagram=Instagram(
    #         uid=generate_uid(account=account_),
    #         name=account_,
    #         account=account_,
    #         password=aes_encrypt(password_),
    #         from_fb=False
    #     )
    # )
    accounts = get_sf_account(account_)
    # if not accounts.social_medias.instagram.from_fb:
    #     cookies = login_for_cookies(account_data=accounts)
    #     accounts.social_medias.instagram.cookies_str = cookies
    #     accounts.social_medias.instagram.update_time = time.time()
    #     accounts.save()
    # print(accounts.social_medias.instagram.cookies_str)

    # Test Step 2: 創建使用者帳戶
    user_account = "_.annastix@gmail.com"
    ig_username = "_.annastix"
    user_password = "nothisaccount"

    user = UserAccount(
        uid=generate_uid(account=account_),
        account=user_account,
        password=aes_encrypt(user_password),
        phone_number="1234567890",
    )
    user.save()

    # Test Step 3: 校驗使用者帳戶資料與補全
    session = requests.session()
    data = get_user_id(
        cookies=accounts.social_medias.instagram.cookies_str,
        username=ig_username,
        session=session
    )

    user_ig = UserInstagram(
        uid=generate_uid(account=data.uid),
        name=ig_username,
        allow_crawlers=[accounts.uid]
    )
    user_ig.save()

    if user_ig.uid not in user.instagram:
        user.instagram.append(user_ig.uid)
        user.save()

    user_data = get_ig_user_info_by_graph_api(
        session=session,
        username=user_ig.name,
        uid=data.uid,
        crawler_data=data,
    )
    # user_data = get_user_info_by_vi_api(
    #     username=user_ig.name,
    #     cookies=accounts.social_medias.instagram.cookies_str
    # )
    user_ig.ig_id=user_data.pk
    user_ig.update_time = time.time()
    user_ig.save()

    # Test Step 4: 測試利用爬蟲帳號取得客戶IG的追蹤者
    get_followers(
        cookies=accounts.social_medias.instagram.cookies_str,
        user_data=user_ig
    )

    # Test Step 5:


