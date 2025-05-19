import logging
import time
import json
import base64
import hashlib
import requests
import orjson
import redis
import os
import random
import string
import platform
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


def try_loops(session: requests.Session, cookie_str, url, headers, cursor, total_req, max_trys=6) -> bool | dict:
    for i in range(1, max_trys):
        try:
            logging.info(
                f"【{time.strftime('%H:%M:%S')}】嘗試第 {i}-{total_req} 次請求追蹤者數據，cursor：{cursor[:30]}...")
            headers["Cookie"] = cookie_str
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


def load_lua_script(redis_server: redis.Redis, script_path: str = "./data/set_with_time.lua"):
    with open(f"{script_path}", "r") as f:
        lua_script = f.read()

    redis_server.function_load(lua_script, replace=True)


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
        raise Exception("5次重試均失敗")
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
