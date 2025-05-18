import datetime
import time
import logging
import json
import requests
import sys
import os
from functions.utils import find_value
# from function import predictor
from schemes import old_db_schemes
from functions.config_manager import ConfigManager
from DrissionPage import common, ChromiumPage, Chromium
from DrissionPage import ChromiumOptions
from bs4 import BeautifulSoup
from fcaptcha.twocaptcha import TwoCaptcha
from functions.utils import try_loops, aes_decrypt, aes_encrypt
from functions.meta_account_function import get_sf_account, create_sf_account, generate_uid
from data.account_data import email_, password_


# ConfigManager.read_yaml(rf"L:\demo1\configs")
# picture_save_path = ConfigManager.server.social_midia.fb.recapture.picture_save_path
picture_save_path = rf"L:\demo1\data\f_p"

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
api_key = os.getenv('APIKEY_2CAPTCHA', '6d99c583d898aed9fc01e95fed325ced')
solver = TwoCaptcha(api_key)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"  # 設定時間格式
)

recapture_url = "https://www.facebook.com/captcha/tfbimage/"
page_url = "https://www.facebook.com/pages/"

# def print_background_package(tab_: ChromiumPage.get_tab):
#     for packet in tab_.listen.steps():
#         response = packet.response
#         url = packet.url
#         if recapture_url in url:
#             update_friend_data(response.body)


def check_is_facebook_page_manager(
        data: old_db_schemes.DBShellAccount,
        target_page_id: str
) -> int | None:
    facebook_page_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Dest": "document",
        "Priority": "u=0, i",
        # sa的cookie
        "cookie": data.cookies_str
    }

    params_ = {
        "category": "your_pages",
        "ref": "bookmarks"
    }
    res = requests.get(
        url="https://www.facebook.com/pages/",
        headers=facebook_page_headers,
        params=params_
    ).text

    soup = BeautifulSoup(res, 'html.parser')
    madan = {}
    for tag in soup.find_all('script', {'type': 'application/json'}):
        json_content = tag.string
        json_data = json.loads(json_content)
        if 'additional_profiles_with_biz_tools' in json_content:
            madan = json_data
            break

    fz_list = find_value(madan, "additional_profiles_with_biz_tools")
    index_ = None
    try:
        for iter_, item in enumerate(fz_list['edges']):
            print('當前管理者管理的粉專：', item['node']['delegate_page_id'], item['node']['name'])
            if str(target_page_id) == str(item['node']['delegate_page_id']):
                index_ = iter_
                logging.info(f"粉專管理員權限驗證成功~")
                # break
    except Exception as e:
        logging.info(f"[{data.id}]{data.account} 账号掉线了", 1)

    if index_ is False:
        logging.info('目标账号管理的粉专不包括被抓url，说明对方还没将账号设置成管理员')

    return index_


def get_fb_dtsg(cookie_str):
    retry_times = 3
    followers_url = f"https://www.facebook.com/"
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
        "Viewport-Width": "1260",
        "Cookie": cookie_str
    }

    # 根據帳號的cookie_str取得 fb_dtsg 參數，重試retry_times次
    for i in range(1, retry_times):
        logging.info(f"第 {i} 次根據帳號的cookie_str取得 fb_dtsg 參數")
        try:
            res = requests.get(url=followers_url, headers=putong_headers).text
            break
        except requests.RequestException as e:
            sl_time = i * 2 + 1
            logging.info(f"第 {i} 次請求失敗：{e}，{sl_time} 秒後重試")
            time.sleep(sl_time)
    else:
        raise Exception(f"{retry_times} 次重試都失敗了，需要重新執行登入腳本")

    logging.info("拿到數據，準備解析獲取fb_dtsg")
    soup = BeautifulSoup(res, 'html.parser')
    madan = {}
    for tag in soup.find_all('script', {'type': 'application/json'}):
        json_content = tag.string
        json_data = json.loads(json_content)
        if 'FBInteractionTracingDependencies' in json_content:
            madan = json_data
            break

    fb_dtsg = find_value(madan, "token")
    logging.info(f"取得fb_dtsg：{fb_dtsg} \n")
    return fb_dtsg


def check_has_login_and_registry_button(tab_: ChromiumPage.get_tab, timeout: float = 5) -> bool:
    general_class = "x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3"
    close_button_class = "x1i10hfl xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x87ps6o x1lku1pv x1a2a7pz x6s0dn4 xzolkzo x12go9s9 x1rnf11y xprq8jg x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x78zum5 xl56j7k xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 xc9qbxq x14qfxbe x1qhmfi1"

    registry_button = tab_.wait.ele_displayed(f"@@role=button@@class={general_class}", timeout=timeout)
    login_button = tab_.wait.ele_displayed(f"@@class={general_class}@@aria-label=Accessible login button", timeout=timeout)

    if registry_button and login_button:
        close_button = tab_.wait.ele_displayed(f"@@aria-label=關閉@@class={close_button_class}", timeout=timeout)
        if close_button:
            tab_.wait.ele_displayed(f"@@aria-label=關閉@@class={close_button_class}").click()
            logging.info("leave login_and_registry_button page")
        return True
    logging.info("not in login_and_registry_button page")
    return False


def login(
        email: str,
        password: str,
        tab_: ChromiumPage.get_tab,
        timeout: float = 5,
        micro_timeout: float = 0.25
) -> ChromiumPage.get_tab:
    tab_.get(f'https://www.facebook.com')
    login_email_class = "inputtext _55r1 _6luy"
    login_password_class = "inputtext _55r1 _6luy _9npi"
    element_email_name = "email"
    element_password_name = "pass"
    submit_button_class = "_42ft _4jy0 _6lth _4jy6 _4jy1 selected _51sy"
    element_submit_name = "login"

    if not check_has_login_and_registry_button(tab_, timeout=1.5) and not tab_.wait.ele_displayed(
        f"@@class={login_email_class}@@name={element_email_name}", timeout=timeout
    ):
        return tab_

    email_placeholder = tab_.wait.ele_displayed(
        f"@@class={login_email_class}@@name={element_email_name}", timeout=timeout
    )
    if email_placeholder:
        email_placeholder.clear()
        email_placeholder.input(email)
        logging.info("email input success")
    else:
        raise Exception("Email placeholder not found")

    time.sleep(micro_timeout)
    password_placeholder = tab_.ele(
        f"@@class={login_password_class}@@name={element_password_name}"
    )

    if password_placeholder:
        password_placeholder.clear()
        password_placeholder.input(password)
        tab_.ele(f"@@class={submit_button_class}@@name={element_submit_name}").click()
    else:
        raise Exception("Password placeholder not found")
    return tab_


def is_in_recapture_page(tab_: ChromiumPage.get_tab, timeout: float = 5) -> bool:
    time.sleep(timeout)
    recapture = "www.facebook.com/two_step_verification/authentication/?encrypted_context"
    if recapture in tab_.url:
        logging.info("have recapture page")

        return True
    return False


def resolve_text_captcha(_path: str) -> str:
    result = solver.normal(_path)
    start_time = time.time()
    logging.info("wait for recapture")
    code = result.get("code")
    logging.info(f"get recapture code: {code}, Cost time: {time.time() - start_time}")
    return code


def deal_recapture_page(email, tab_: ChromiumPage.get_tab, micro_timeout: float = 0.25, timeout: float = 5) -> bool:
    canvas_ele = tab_.ele("@class=xz74otr x168nmei x13lgxp2 x5pf9jr xo71vjh")
    file_name = f"{email}_{time.time()}.jpg"
    canvas_ele.get_screenshot(picture_save_path, file_name)
    result = resolve_text_captcha(rf"{picture_save_path}{file_name}")

    recapture_placeholder = tab_.ele("@class=x1i10hfl xggy1nq xtpw4lu x1tutvks x1s3xk63 x1s07b3s x1kdt53j x1a2a7pz xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x9f619 xzsf02u x1uxerd5 x1fcty0u x132q4wb x1a8lsjc x1pi30zi x1swvt13 x9desvi xh8yej3")
    recapture_placeholder.clear()
    recapture_placeholder.input(result)

    time.sleep(micro_timeout)
    submit_button_class = "x6s0dn4 x78zum5 xl56j7k x1e0frkt x3fpzix xxdpisx"
    tab_.ele(f"@@class={submit_button_class}").click()
    return True


def login_and_get_cookies(
        _email,
        _password,
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
    co.incognito(True)

    c = Chromium(addr_or_opts=co)
    tab = c.latest_tab
    accounts = get_sf_account(_email)
    page_ = login(email=accounts.account, password=aes_decrypt(accounts.password), tab_=tab)
    if is_in_recapture_page(tab, timeout=timeout):
        deal_recapture_page(email=accounts.account, tab_=tab, timeout=timeout)
    time.sleep(5)
    cookies = page_.cookies().as_json()
    if cookies:
        logging.info(f"Cookies: {cookies}")
    else:
        raise Exception("no cookies")
    dtsg_ = get_fb_dtsg(page_.cookies().as_str())

    accounts.social_medias.facebook.cookies_str = cookies
    accounts.social_medias.facebook.dtsg = dtsg_
    accounts.social_medias.facebook.update_time = time.time()
    accounts.save()

    return accounts


def switch_to_target_page(page_index, timeout: float = 5):
    account_class = "_42ft _4jy0 _6lth _4jy6 _4jy1 selected _51sy"




