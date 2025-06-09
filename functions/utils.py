import logging
import time
import json
import base64
import hashlib
import requests
import orjson
import copy
import redis
import os
import random
import string
import platform
from data.constants import Path
from bs4 import BeautifulSoup
from typing import Optional
from pydantic import BaseModel
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from data.account_data import AES_KEY, AES_IV, main_path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"  # 設定時間格式
)


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

def find_value(data, target_key):
    if isinstance(data, dict):
        if target_key in data:
            return data[target_key]
        for key, value in data.items():
            result = find_value(value, target_key)
            if result is not None:
                return result
    elif isinstance(data, list):
        for iii in data:
            result = find_value(iii, target_key)
            if result is not None:
                return result
    return None


def try_cookies(
        session: requests.Session,
        cookie_str,
        url,
        headers,
        cursor,
        total_req,
        data=None,
        max_trys=6
) -> bool | dict:
    for i in range(1, max_trys):
        try:
            logging.info(
                f"【{time.strftime('%H:%M:%S')}】嘗試第 {i}-{total_req} 次請求追蹤者數據，cursor：{cursor}..."
            )
            headers["Cookie"] = cookie_str
            if data:
                result = session.post(url=url, headers=headers, data=data).json()
            else:
               result = session.get(url=url, headers=headers).json()
            return result
        except requests.RequestException as e:
            sleep_time = i * 2 + 1
            logging.info(f"請求 {i} 次請求崩潰：{e}，{sleep_time} 秒後重試")
            time.sleep(sleep_time)
        except json.JSONDecodeError as e:
            logging.info(f"JSON解析錯誤：{e}")
            return False
        except Exception as e:
            logging.info(f"未知錯誤：{e}")
            return False
    else:
        logging.info(f"5次重試均失敗，放棄追蹤者數據")
        return False


class ORJSONEncoder:
    def encode(self, obj):
        return orjson.dumps(obj).decode("utf-8")


class ORJSONDecoder:
    def decode(self, s):
        return orjson.loads(s)


def aes_encrypt(plaintext: str) -> str:
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(ct).decode()


def aes_decrypt(ciphertext_b64: str) -> str:
    ct = base64.b64decode(ciphertext_b64.encode())
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_data) + unpadder.finalize()
    return plaintext.decode()


def get_redis_path_from_model_field(root: BaseModel, target_ref, prefix="") -> Optional[str]:
    for name, value in root.__dict__.items():
        path_segment = f"{prefix}.{name}" if prefix else name
        if value is target_ref:
            return "." + path_segment
        elif isinstance(value, BaseModel):
            sub_path = get_redis_path_from_model_field(value, target_ref, path_segment)
            if sub_path:
                return sub_path
    return None


def generate_uid(account: str) -> str:
    raw = f"{account}"
    digest = hashlib.sha1(raw.encode()).hexdigest()  # 40 hex chars

    return digest


def download_head_pic(
        pic_url,
        sub_path="ig_head_pics",
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
        logging.info("5次重試均失敗")
        return None
    html1 = file_content.content
    file_name = ''.join(random.sample(string.ascii_letters + string.digits, 12))

    if platform.system() == "Darwin":
        file_path = f"{main_path}/{sub_path}/{time.strftime('%Y%m%d')}"
    else:
        file_path = f"{main_path}/{sub_path}/{time.strftime('%Y%m%d')}"
    if not os.path.exists(file_path):
        os.makedirs(file_path, exist_ok=True)
    a_path = f"{file_path}/{file_name}.png"
    with open(a_path, "wb") as fp:
        fp.write(html1)
    return a_path.replace(f"{main_path}/{sub_path}", ".")


def get_fb_dtsg(cookie_str):
    retry_times = 3
    followers_url = Path.FacebookHost
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



if __name__ == "__main__":
    # putong_headers = {
    #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    #     "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8,zh-TW;q=0.7",
    #     "Cache-Control": "max-age=0",
    #     # "Cookie": "sb=Mw6eZeWHJjcypUCF_pisW-nT; datr=Mw6eZWYONK5_Zp3WgPGDwkZE; c_user=61553172127596; ps_n=1; ps_l=1; m_page_voice=61553172127596; dpr=1; xs=7%3AWlLIVE_WNcgg2A%3A2%3A1713455311%3A-1%3A-1%3A%3AAcVJ1VAZCekW6fypJ1gOI5a8XJF2jFYcUlDk3R3mfFFD; fr=1uvqW12KjiR8iPg0y.AWWhsD9nPO4vru9amgrh2G4UXsU.Bmc_B2..AAA.0.0.Bmc_B2.AWVeM0OtABI; usida=eyJ2ZXIiOjEsImlkIjoiQXNmZGd1dzFsbWlkb3YiLCJ0aW1lIjoxNzE4ODc1NTQ0fQ%3D%3D; presence=C%7B%22t3%22%3A%5B%5D%2C%22utc3%22%3A1718875545021%2C%22v%22%3A1%7D; wd=1260x908",
    #     "Cookie": "sb=Mw6eZeWHJjcypUCF_pisW-nT; ps_n=1; ps_l=1; wl_cbv=v2%3Bclient_version%3A2551%3Btimestamp%3A1720163737; vpd=v1%3B736x414x3; dpr=1; locale=zh_TW; datr=ri60ZijyQ14lkWOESIUlN5WT; usida=eyJ2ZXIiOjEsImlkIjoiQXNodzN1cjZ4ZTFrNyIsInRpbWUiOjE3MjMxMDU5MzR9; c_user=61557016683521; xs=15%3A0J0vQ8XNsEddPw%3A2%3A1723112853%3A-1%3A10701; wd=1133x908; fr=1vxgzgFsQj4eqovc7.AWVJ8SHI352ARRbGSx-K6BzQn-I.BmtJmx..AAA.0.0.BmtJ2h.AWUfGrHOFaI; presence=C%7B%22t3%22%3A%5B%5D%2C%22utc3%22%3A1723112867820%2C%22v%22%3A1%7D",
    #     "Dpr": "2",
    #     "Priority": "u=0, i",
    #     "Sec-Ch-Prefers-Color-Scheme": "light",
    #     "Sec-Ch-Ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
    #     "Sec-Ch-Ua-Full-Version-List": "\"Google Chrome\";v=\"125.0.6422.176\", \"Chromium\";v=\"125.0.6422.176\", \"Not.A/Brand\";v=\"24.0.0.0\"",
    #     "Sec-Ch-Ua-Mobile": "?0",
    #     "Sec-Ch-Ua-Model": "\"\"",
    #     "Sec-Ch-Ua-Platform": "\"macOS\"",
    #     "Sec-Ch-Ua-Platform-Version": "\"14.5.0\"",
    #     "Sec-Fetch-Dest": "document",
    #     "Sec-Fetch-Mode": "navigate",
    #     "Sec-Fetch-Site": "none",
    #     "Sec-Fetch-User": "?1",
    #     "Upgrade-Insecure-Requests": "1",
    #     "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    #     "Viewport-Width": "1260"
    # }
    # ig_headers = {
    #     "Accept": "*/*",
    #     "Accept-Language": "zh-CN,zh;q=0.9",
    #     # "Cookie": 'ps_n=1;datr=TjdiZ80QUxwOvDXUVLo-y3_F;ds_user_id=66977041392;csrftoken=R21BUDEe3_8t5xloOGvj9n;ig_did=C4FE4C0E-C798-46D0-9F9A-26F5A85C60BA;ps_l=1;wd=1208x906;mid=Z2I3TgAEAAFingu-Rbuv81aUNUnb;sessionid=66977041392%3ApuAv5UvZ4f86R2%3A13%3AAYeJt-QP27ufzBShI9EGWdZYDMYrIlE-WwHOjfstsg;rur="CCO\05466977041392\0541766026003:01f759c89653823cb2545aeb53c51e76679fd7adaf1a8b0e68b3800d03591c547fef2eea"',
    #     "Priority": "u=1, i",
    #     "Referer": "https://www.instagram.com/netaporter/followers/",
    #     "Sec-Ch-Prefers-Color-Scheme": "light",
    #     "Sec-Ch-Ua": "\"Chromium\";v=\"124\", \"Microsoft Edge\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
    #     "Sec-Ch-Ua-Full-Version-List": "\"Chromium\";v=\"124.0.6367.207\", \"Microsoft Edge\";v=\"124.0.2478.105\", \"Not-A.Brand\";v=\"99.0.0.0\"",
    #     "Sec-Ch-Ua-Mobile": "?0",
    #     "Sec-Ch-Ua-Model": "\"\"",
    #     "Sec-Ch-Ua-Platform": "\"Windows\"",
    #     "Sec-Ch-Ua-Platform-Version": "\"10.0.0\"",
    #     "Sec-Fetch-Dest": "empty",
    #     "Sec-Fetch-Mode": "cors",
    #     "Sec-Fetch-Site": "same-origin",
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    #     "X-Asbd-Id": "129477",
    #     "X-Csrftoken": "8I0dg8w30nKUDNnGdc2pc20jzjZKGEvz",
    #     "X-Ig-App-Id": "936619743392459",
    #     "X-Ig-Www-Claim": "hmac.AR1lJHcc0gF0WSQS_kos2-kfKhxzkKnKkqCYkIhfqzqppIuP",
    #     "X-Requested-With": "XMLHttpRequest"
    # }
    #
    # headers = {
    #     "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,de-AT;q=0.6,de;q=0.5,it;q=0.4,de-DE;q=0.3,en-GB;q=0.2,en-IE;q=0.1",
    #     # "Cookie": "mid=ZbNt0QALAAE5at-la2xXaGU6TbLU; ig_did=889F6792-718D-448E-9C34-D415D027D0A8; datr=0W2zZTDYYUkp-0cR6bHNpJOQ; ig_nrcb=1; csrftoken=S00MMTu9F7yiqAAwV18B2QEyUDEjmiGm; ds_user_id=8586471183; sessionid=8586471183%3AaYzA2myV7z3Cso%3A0%3AAYd8qVEIBcw0kOAao8tNDv8QtxNynV9U4AtWmHEInw; igd_ls=%7B%22c%22%3A%7B%7D%2C%22d%22%3A%2240c02de3-9902-4a57-8fd9-843bb9a2a877%22%2C%22s%22%3A%221%22%2C%22u%22%3A%22zy3607%22%7D; ps_n=0; ps_l=0; rur=\"PRN\\0548586471183\\0541737795433:01f765cf42ad05fac61a64819533a60d39ba877d35395c88095a4f446b9d45840ea21561\"",
    #     "Dpr": "1",
    #     "Referer": "https://www.instagram.com/vp/following/",
    #     "Sec-Ch-Prefers-Color-Scheme": "light",
    #     "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Microsoft Edge\";v=\"120\"",
    #     "Sec-Ch-Ua-Full-Version-List": "\"Not_A Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"120.0.6099.234\", \"Microsoft Edge\";v=\"120.0.2210.144\"",
    #     "Sec-Ch-Ua-Mobile": "?0",
    #     "Sec-Ch-Ua-Model": "\"\"",
    #     "Sec-Ch-Ua-Platform": "\"Windows\"",
    #     "Sec-Ch-Ua-Platform-Version": "\"10.0.0\"",
    #     "Sec-Fetch-Dest": "empty",
    #     "Sec-Fetch-Mode": "cors",
    #     "Sec-Fetch-Site": "same-origin",
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    #     "Viewport-Width": "2512",
    #     "X-Asbd-Id": "129477",
    #     "X-Csrftoken": "S00MMTu9F7yiqAAwV18B2QEyUDEjmiGm",
    #     "X-Ig-App-Id": "936619743392459",
    #     "X-Ig-Www-Claim": "hmac.AR1lJHcc0gF0WSQS_kos2-kfKhxzkKnKkqCYkIhfqzqppOXa",
    #     "X-Requested-With": "XMLHttpRequest"
    # }
    # import re
    # import requests
    # session = requests.session()
    # # url_info['url'] = 'https://www.instagram.com/binghong1898/'
    # res = session.get(url="https://www.instagram.com/jo.stillsingle/", headers=putong_headers).text
    #
    # id = re.findall('"props":\{"id":"(.*?)"', res, re.S)[0]
    # logging.info(f"id：{id}")
    # url = f"https://www.instagram.com/api/v1/friendships/{id}/followers/?count=25&search_surface=follow_list_page"
    # cursor = ''
    # if cursor:
    #     url = f"{url}&max_id={cursor}"
    # headers.update({"cookie": 'csrftoken=ZWQmjWd01QimPrQLO7pBd0TENEF3Gl8h; ds_user_id=75366648584; wd=1437x842; ps_n=1; ps_l=1; sessionid=75366648584%3A71mDK6mVUeQxC6%3A21%3AAYdQ5xEzUWOKoQO5_UPUQ-Pc45GbQ5tWMnfBsJugYA; mid=aEAddAAEAAHBL4QnHyizQ9w9W_-5; rur="PRN\05475366648584\0541780576127:01fe3746375da68ea8c5353ae8f75ecb982ed49ab6ff41587e86b49ec24477384ee47770"; ig_nrcb=1; ig_did=EEC87A87-1498-408A-9E56-AC8C9AD9A9C4; datr=dB1AaHB6d9GF5CJfBwNdo9Tv'})
    # res = session.get(url=url, headers=headers).json()
    # print(len(res['users']))
    # for i in res['users']:
    #     uid = i["id"]
    #     print(i)
    #
    # url = f"https://www.instagram.com/api/v1/feed/user/{id}/?count=12&max_id={cursor}"
    # res = requests.get(url=url, headers=headers).json()
    # for i in res['items']:
    #     # ti = i['taken_at']
    #     # tis = time.localtime(ti)
    #     # tim = int(str(time.strftime('%Y-%m-%d %H:%M:%S', tis)).split(' ')[0].replace('-', ''))
    #     # post_id = i['code']
    #     # postt_url = f'https://www.instagram.com/p/{post_id}/'
    #     print(i)

    putong_headers1 = {
        "cookie": "csrftoken=CiimhHOoYuTD8AaariB1d8; ig_did=2C1AF6CC-9729-4047-B6DA-CEF31853228D; mid=Z1RvkwAEAAGP7D6sipibiZPJIBrf",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "cache-control": "max-age=0",
        "dpr": "2",
        "priority": "u=0, i",
        "sec-ch-prefers-color-scheme": "light",
        "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-full-version-list": "\"Google Chrome\";v=\"131.0.6778.109\", \"Chromium\";v=\"131.0.6778.109\", \"Not_A Brand\";v=\"24.0.0.0\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": "\"\"",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-ch-ua-platform-version": "\"15.1.0\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport-width": "963"
    }

    res = requests.get(url="https://www.threads.com/@_xaivian", headers=putong_headers1).text
    soup = BeautifulSoup(res, 'html.parser')
    # 提取出每个<script>标签中的JSON内容
    madan = {}
    for tag in soup.find_all('script', {'type': 'application/json'}):
        json_content = tag.string
        # 将JSON字符串转换为Python字典
        json_data = json.loads(json_content)
        if 'hd_profile_pic_versions' in json_content:
            madan = json_data
            break
    if madan:
        user_info = madan["require"][0][3][0]["__bbox"]["require"][0][3][1]["__bbox"]["result"]["data"]["user"]
        # print(user_info)
        # new_head_url = down_head_pic(user_info["profile_pic_url"])
        new_head_url = ''
        user_info_data = {
            "u_id": user_info['pk'],  # userId
            "type": 7,
            "url_name": user_info['username'],  # 名称
            "head_pic": new_head_url,  # 头像
            "jianjie": user_info['biography'],  # 简介
            "follower_count": user_info['follower_count'],  # 关注人数
        }
    else:
        print('目标链接信息没查到')
    print(user_info_data)
    cursor = ''
    data = {
        # "fb_dtsg": "NAcNlWHsU_yx0nK3vOBoPCJrsCvkNvhmtUPPFiQWtNL2qFl49PELnnA:17843709688147332:1733563415",
        # "fb_dtsg": "NAcP5hEPA9dOmqbVwetRX564Xv2BvQtJjcnN_yDo59stBsyxFschEeQ:17865379441060568:1733650802",
        # "fb_dtsg": "NAcO1DN3m1N_MvgOMpf3ZsZD-9zQn8q-k2rOYjuC3HoZXYmvUr7yW6w:17864970403026470:1740555202",
        "fb_api_req_friendly_name": "BarcelonaFriendshipsFollowersTabRefetchableQuery",
        "variables": '{"after":"' + cursor + '","first":20,"id":"' + str(user_info_data["u_id"]) + '","__relay_internal__pv__BarcelonaIsLoggedInrelayprovider":true,"__relay_internal__pv__BarcelonaIsCrawlerrelayprovider":false,"__relay_internal__pv__BarcelonaHasDisplayNamesrelayprovider":false}',
        "server_timestamps": "true",
        "doc_id": "9226067564176291"
    }
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

    # # yingzhang8763 張應 的头
    cookies = {
        "csrftoken": "v9KDWJfAZN02zai6zUHEedccbzE9922T",
        "ds_user_id": "66805851320",
        "sessionid": "66805851320%3AHAVLSlvNdEXqir%3A5%3AAYcEcftJpXkxLWYQbjXgfE3PzhUG6uYRIVUXcP_HPg",
        "ig_did": "DEBB4C43-15EC-44AF-BE66-9BF52E87BB82",
        "mid": "Z1QdggAEAAEvuHT0QPspVeVXVCB1"
    }
    api_url = "https://www.threads.net/graphql/query"
    res = requests.post(url=api_url, headers=headers, data=data).json()
    print(res)
    for i in res['data']['fetch__XDTUserDict']['followers']['edges']:
        # uid = i['node']['pk']
        print(i)