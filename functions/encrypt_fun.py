import hashlib
import json


def generate_uid(account_: str, videos_: list, images_: list, text_: str):
    """
    生成唯一的 SHA-256 UID
    :param account_: 使用者帳號
    :param videos_: 影片列表 (list of URLs or filenames)
    :param images_: 圖片列表 (list of URLs or filenames)
    :param text_: 貼文內容 (string)
    :param get_time_: 取得(爬完)貼文的時間
    :return: SHA-256 UID
    """

    # 確保所有內容都是字串格式
    data = {
        "account": account_,
        "videos": sorted(videos_),
        "images": sorted(images_),
        "text": text_.strip(),
    }

    # 轉換為 JSON 字串，確保一致性
    data_string = json.dumps(data, separators=(',', ':'), ensure_ascii=False)

    # 生成 SHA-256 哈希值
    uid = hashlib.sha256(data_string.encode('utf-8')).hexdigest()

    return uid


if __name__ == '__main__':
    # 測試
    account = "user123"
    videos = ["video1.mp4", "video2.mp4"]
    images = ["img1.jpg", "img2.jpg"]
    text = "This is a sample post!"

    uid = generate_uid(account, videos, images, text)
    print("Generated UID:", uid)
