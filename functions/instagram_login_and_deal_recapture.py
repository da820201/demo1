import datetime
import time
import logging
import json
import requests
import sys
import os
import time
import redis
import platform
import random
import string
from redis_om import Migrator
from redis_om import get_redis_connection
from schemes.sf_account_schemes import SFMetaAccount, SocialMedias, Facebook, Instagram, Threads
from functions.meta_account_function import get_sf_account, create_sf_account, generate_uid
from functions.utils import try_loops, aes_decrypt, aes_encrypt
from functions.config_manager import ConfigManager
from DrissionPage import common, ChromiumPage, Chromium
from DrissionPage import ChromiumOptions
from fcaptcha.twocaptcha import TwoCaptcha


# ConfigManager.read_yaml(rf"./configs/config.yaml")
# picture_save_path = ConfigManager.server.social_midia.fb.recapture.picture_save_path
_email = "daniel.guan@shell.fans"
_password = "983B0ca2"
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
api_key = os.getenv('APIKEY_2CAPTCHA', '6d99c583d898aed9fc01e95fed325ced')
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
down_header = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Priority": "u=0, i",
    "Sec-Ch-Ua": "\"Microsoft Edge\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0"
}



account_ = ""
password_ = ""
main_path = "/Users/shellfans-/PycharmProjects/demo1/data"


def download_head_pic(
        pic_url,
        max_retry=5
):
    for i in range(1, max_retry):
        try:
            file_content = requests.get(url=pic_url, headers=down_header)
            break
        except requests.RequestException as e:
            sleep_time = i * 2 + 1
            logging.info(f"請求 {i} 次請求崩潰：{e}，{sleep_time} 秒後重試")
            time.sleep(sleep_time)
            pass
    else:
        raise Exception("5次重試均失敗")
    html1 = file_content.content
    file_name = ''.join(random.sample(string.ascii_letters + string.digits, 12))
    if platform.system() == "Darwin":
        file_path = f"{main_path}/ig_head_pics/{time.strftime('%Y%m%d')}"
    else:
        file_path = f"{main_path}/ig_head_pics/{time.strftime('%Y%m%d')}"
    if not os.path.exists(file_path):
        os.mkdir(file_path)
    a_path = f"{file_path}/{file_name}.png"
    with open(a_path, "wb") as fp:
        fp.write(html1)
    return a_path.replace(f"{main_path}/ig_head_pics", ".")


def try_cookies(
        cookies,
        uid: str,
        cursor: str = "",
        total_req: int = 1
) -> bool | dict:
    url = f"https://www.instagram.com/api/v1/friendships/{uid}/followers/?count=25&search_surface=follow_list_page"
    if cursor:
        url = f"{url}&max_id={cursor}"

    session = requests.session()
    return try_loops(
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
    # 更多的選項，不知道為什麼有機會出現兩組參數。
    more_box_aria_type_a = "«r1a»"
    more_box_aria_type_b = "«Rmreillkqbrj5ipd5aq»"
    more_box = (
        tab_.wait.ele_displayed(
            f"@@class={more_box_class}@@aria-describedby={more_box_aria_type_a}", timeout=timeout
        ), tab_.wait.ele_displayed(
            f"@@class={more_box_class}@@aria-describedby={more_box_aria_type_b}", timeout=timeout
        )
    )
    if not any(more_box):
        print(more_box)
        logging.info("no more box")
        return False

    for i in more_box:
        if i:
            more_box = i
            break

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


def get_followers(
        cookies,
        target_uid: str="6770296405",  # "5951385086"
        timeout: float = 5
):
    plate = 2  # 2: Instagram
    cursor, ok_fans_num, total_req = "", 0, 1
    while True:
        targets = try_cookies(cookies=cookies, uid=target_uid, cursor=cursor)
        for k, v in targets.items():
            print(k, v)
        print(len(targets["users"]))
        for target in targets["users"]:
            uid = target["id"]
            head_pic = download_head_pic(target['profile_pic_url'])
            dic = {
                'plate': plate,
                'url_uid': target_uid,
                'type': 0,
                'nickname': target['username'],
                'head_pic': head_pic[1:],  # 去掉前面的點
                'uid': uid,
                'create_time': int(time.time()),
                'update_time': 0,
                'delete_time': 0
            }
            # print(dic)
            print(target)
            time.sleep(random.uniform(3, 6))
            ok_fans_num += 1

        if "next_max_id" not in targets:
            logging.info("該帳號設置不能查看更多了，只有該帳號本身能看全部追蹤者")
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
    r = redis.Redis(host="localhost", port=6380, db=0, decode_responses=True)
    create_sf_account(
        account=account_,
        password=aes_encrypt(password_),
        redis_server=r,
        instagram=Instagram(
            uid=generate_uid(account=account_),
            name=account_,
            account=account_,
            password=aes_encrypt(password_),
            from_fb=False
        )
    )
    accounts = get_sf_account(account_)
    if not accounts.social_medias.instagram.from_fb:
        cookies = login_for_cookies(account_data=accounts)
        accounts.social_medias.instagram.cookies_str = cookies
        accounts.social_medias.instagram.update_time = time.time()
        accounts.save()

    get_followers(cookies=accounts.social_medias.instagram.cookies_str)


