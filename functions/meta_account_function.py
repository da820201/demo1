import time
import redis
from functions.utils import aes_encrypt, aes_decrypt, generate_uid, aes_encrypt
from schemes.sf_account_schemes import SFMetaAccount, SocialMedias, Facebook, Instagram, Threads, UpdateSocialMedias,UpdateInstagram, UpdateSFMetaAccount
from pydantic import BaseModel


def create_sf_account(
        account: str,
        password: str,
        facebook: Facebook = None,
        instagram: Instagram | dict | None = None,
        threads: Threads = None
):
    encrypted_pw = aes_encrypt(password)
    uid = generate_uid(account=account)
    data = SFMetaAccount(
        uid=uid,
        account=account,
        password=encrypted_pw,
        social_medias=SocialMedias(
            uid=uid,
            facebook=Facebook(
                uid=uid,
                name=account
            ) if facebook is None else facebook,
            instagram=instagram,
            threads=threads
        )
    )

    data.save()


def get_sf_account(
        account: str,
        decrypt: bool = True
) -> SFMetaAccount:
    uid = generate_uid(account=account)
    data = SFMetaAccount.get(uid)
    if decrypt:
        data.password = aes_decrypt(data.password)

    return data


def merge_models(base: BaseModel, patch: BaseModel) -> BaseModel:
    """
    遞迴合併 patch 模型到 base 模型，僅更新非 None 欄位
    """
    base_dict = base.model_dump()
    patch_dict = patch.model_dump(exclude_unset=True, exclude_none=True)

    def deep_merge(d1, d2):
        for k, v in d2.items():
            if isinstance(v, dict) and isinstance(d1.get(k), dict):
                d1[k] = deep_merge(d1.get(k, {}), v)
            else:
                d1[k] = v
        return d1

    merged_data = deep_merge(base_dict, patch_dict)
    return base.__class__.model_validate(merged_data)


def get_data_by_uid(
        uid: str,
        model: BaseModel,
) -> BaseModel:
    return model.get(uid)


def update_sf_account(
        account: str,
        data: UpdateSFMetaAccount
):
    current = get_sf_account(account=account)
    if not current:
        raise ValueError("Account not found")
    # 更新原模型
    updated = merge_models(current, data)
    updated.update_time = time.time()
    updated.save()


def update_model_by_uid(
        uid: str,
        model,
        data: dict or BaseModel,
        uid_encrypted: bool = False
):
    """
    更新模型
    :param uid: uid
    :param model: any model
    :param uid_encrypted: uid 是否加密
    :return:
    """
    current = get_data_by_uid(uid=uid if uid_encrypted else generate_uid(uid), model=model)
    if not current:
        raise ValueError("Account not found")
    if isinstance(data, dict):
        data = model(**data)
    # 更新原模型
    updated = merge_models(current, data)
    updated.update_time = time.time()
    updated.save()


if __name__ == "__main__":
    r = redis.Redis(host="localhost", port=6380, db=0, decode_responses=True)
    from data.account_data import account_, password_

    partial_update = UpdateSFMetaAccount(
        password=aes_encrypt(password_),
        social_medias=UpdateSocialMedias(
            instagram=UpdateInstagram(
                cookies_str="new_cookie"
            )
        )
    )

    update_sf_account(account=account_, data=partial_update)
