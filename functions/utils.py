import logging
import time
import json
import base64
import hashlib
import requests
import orjson
import redis
from typing import Optional
from pydantic import BaseModel
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from data.account_data import AES_KEY, AES_IV


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"  # 設定時間格式
)


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
