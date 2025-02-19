import datetime
import time
import logging
from DrissionPage import common, ChromiumPage, Chromium
from functions import encrypt_fun
from schemes import video_schemes, general_schemes

friend_data_by_name = {}
friend_data = {}
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"  # 設定時間格式
)


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


def check_uid(tab_: ChromiumPage.get_tab, account: str, timeout: float = 5) -> bool:
    general_class = "x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1sur9pj xkrqix3 xi81zsa x1s688f"

    followers = tab_.wait.ele_displayed(f"@@class={general_class}@@href=https://www.facebook.com/{account}/followers/", timeout=timeout)
    friends_likes = tab_.wait.ele_displayed(f"@@class={general_class}@@href=https://www.facebook.com/{account}/friends_likes/", timeout=timeout)
    if followers and friends_likes:
        logging.info("check uid page")
        return True
    logging.info("not in target uid page")
    return False


def get_post_text(tab_: ChromiumPage.get_tab, tags: set, text: str, micro_timeout: float = 0.25) -> tuple[set, str]:
    post_text_class = "x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x3x7a5m x6prxxf xvq8zen xo1l8bm xzsf02u x1yc453h"
    post_more_content_button_class = "x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1sur9pj xkrqix3 xzsf02u x1s688f"
    post_text = tab_.eles(f"@class={post_text_class}")
    for ts in post_text:
        try:
            more_content_button = ts.ele(f"@@class={post_more_content_button_class}@@role=button", timeout=micro_timeout)
            more_content_button.click()
            logging.debug("has more_content_button")
        except Exception:
            logging.debug("no more_content_button")
        if ts.text:
            tags.add("text")
            text = ts.text
    return tags, text


def get_video_url(tab_: ChromiumPage.get_tab, tags: set, videos: list, post_url: str, micro_timeout: float = 0.25) -> tuple[set, str]:
    post_video_option_class = "x5yr21d x10l6tqk x13vifvy xh8yej3"
    videos_ = tab_.ele(f"@@class={post_video_option_class}", timeout=micro_timeout)
    if videos_:
        video_option = videos_.ele(f"@@aria-label=放大", timeout=micro_timeout)

        if video_option:
            try:
                href = video_option.attr("href").split("/?__cft")[0]
                if not post_url:
                    post_url = href
                videos.append(href)
                tags.add("video")
                logging.debug("get videos")
            except Exception:
                logging.debug("no videos")
    return tags, post_url


def get_reels_url(tab_: ChromiumPage.get_tab, tags: set, reels: list, post_url: str, micro_timeout: float = 0.25) -> tuple[set, str]:
    reels_class = "x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x1q0g3np x87ps6o x1lku1pv x1rg5ohu x1a2a7pz x1n2onr6 xh8yej3"
    reels_ = tab_.ele(f"@@class={reels_class}", timeout=micro_timeout)
    if reels_:
        try:
            href = reels_.attr("href").split("/?s=")[0]
            if not post_url:
                post_url = href
            reels.append(href)
            tags.add("reels")
            logging.info("get reels")
        except Exception:
            logging.info("no reels")
    return tags, post_url


def get_images_url(tab_: ChromiumPage.get_tab, tags: set, images: list, post_url: str, micro_timeout: float = 0.25) -> tuple[set, str]:
    post_photo_class_ = "x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x1q0g3np x87ps6o x1lku1pv x1rg5ohu x1a2a7pz x1ey2m1c xds687c x10l6tqk x17qophe x13vifvy x1pdlv7q"
    post_photo = tab_.eles(f"@@class={post_photo_class_}", timeout=micro_timeout)
    if post_photo:
        for photo in post_photo:
            try:
                href = photo.attr("href").split("&__cft__")[0]
                if not post_url:
                    post_url = href
                images.append(href)
                tags.add("images")
                logging.debug("get images")
            except Exception:
                logging.debug("no images")
    return tags, post_url


def get_user_mood(tab_: ChromiumPage.get_tab, tags: set, user_moods: list, micro_timeout: float = 0.25) -> list:
    user_mood_class = "x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x3nfvp2 x1q0g3np x87ps6o x1lku1pv x1a2a7pz"
    user_mood_with_reels_class = "x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x2lah0s x193iq5w x1xmf6yo x1e56ztr xzboxd6 x14l7nz5"
    user_mood_aria_class = "x1i10hfl xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x87ps6o x1lku1pv x1a2a7pz x6s0dn4 xzolkzo x12go9s9 x1rnf11y xprq8jg x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x78zum5 xl56j7k xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x1vqgdyp x100vrsf x1qhmfi1"
    user_mood_filter_ = ["留言", "傳送給朋友或在個人檔案上發佈。", "Available Voices"]
    if "reels" in tags:
        try:
            user_moods_aria_ = tab_.ele(f"@@class={user_mood_aria_class}@@role=button", index=3, timeout=micro_timeout)
            user_moods_ = tab_.ele(f"@@class={user_mood_with_reels_class}", index=3, timeout=micro_timeout)
            user_moods_text = f"{user_moods_aria_.attr('aria-label')}: {user_moods_.text}"
            user_moods.append(user_moods_text)
            logging.debug(user_moods_text)
        except Exception as e:
            logging.debug(f"can't get user mood")
    else:
        user_moods_ = tab_.eles(f"@@class={user_mood_class}@@tabindex=0", timeout=micro_timeout)
        for user_mood_ in user_moods_:
            try:
                if not user_mood_.attr("aria-label") in user_mood_filter_:
                    user_moods.append(user_mood_.attr("aria-label"))
            except Exception as e:
                logging.debug(f"can't get user mood")
    return user_moods


def go_to_post_page(chromium: Chromium, account: str, get_post_count: int = 3, timeout: float = 5, micro_timeout: float = 0.25):
    """
    用來爬取指定使用者的貼文
    :param chromium: DrissionPage 的實例化類別
    :param account: 使用者FB的ID或UID
    :param get_post_count: 希望爬取的貼文數量
    :param timeout: 大類的等待時間
    :param micro_timeout:
    :return:
    """

    post_class = "x9f619 x1n2onr6 x1ja2u2z xeuugli x1iyjqo2 xs83m0k xjl7jj x1xmf6yo x1emribx x1e56ztr x1i64zmx x19h7ccj x65f84u"
    login_post_class = "x9f619 x1n2onr6 x1ja2u2z xeuugli xs83m0k xjl7jj x1xmf6yo x1emribx x1e56ztr x1i64zmx x19h7ccj xu9j1y6 x7ep2pv"
    post_class_ = "x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z"
    post_url_class = "x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1sur9pj xkrqix3 xi81zsa x1s688f"


    tab_ = chromium.latest_tab
    tab_.get(f'https://www.facebook.com/{account}')
    is_login = not check_has_login_and_registry_button(tab_, timeout=timeout)
    result = []
    posts_displayed = tab_.wait.ele_displayed(f"@class={login_post_class if is_login else post_class}", timeout=timeout)
    if posts_displayed:
        logging.info("get in posts")
        while len(result) < get_post_count:
            tags, post_url, videos, reels, images, user_moods, text = set(), "", [], [], [], [], ""
            posts_ = tab_.ele(f"@class={login_post_class if is_login else post_class}")
            time.sleep(0.25)
            posts_ = posts_.eles(f"@class={post_class_}")
            for r in posts_:
                tags, text = get_post_text(r, tags, text, micro_timeout=micro_timeout)

                try:
                    post_url = r.ele(f"@@class={post_url_class}@@href:https://www.facebook.com/{account}/@@role=link", timeout=micro_timeout).attr("href")
                    logging.debug("get post_url")
                except Exception:
                    logging.debug("not get post_url")

                tags, post_url = get_video_url(r, tags, videos, post_url, micro_timeout=micro_timeout)
                tags, post_url = get_reels_url(r, tags, reels, post_url, micro_timeout=micro_timeout)
                tags, post_url = get_images_url(r, tags, images, post_url, micro_timeout=micro_timeout)
                user_moods = get_user_mood(r, tags, user_moods, micro_timeout=micro_timeout)

                tags, get_time = list(tags), time.time()
                scheme = general_schemes.GeneralSchemes(
                    sid=encrypt_fun.generate_uid(
                        account_=account,
                        videos_=videos,
                        images_=images,
                        text_=text
                    ),
                    account=account,
                    post_url=post_url,
                    videos=videos,
                    images=images,
                    describe=text,
                    user_mood=user_moods,
                    tags=tags,
                    get_time=get_time
                )
                tab_.actions.move_to(r)
                result.append(scheme)
                tab_.remove_ele(r)
                break
        return result


def go_to_videos_page(chromium: Chromium, account: str, get_video_count: int = 10, timeout: int = 5) -> ChromiumPage.get_tab:
    post_class = "x9f619 x1r8uery x1iyjqo2 x6ikm8r x10wlt62 x1n2onr6"
    video_and_des_class = "x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1heor9g x1sur9pj xkrqix3"
    user_mood_class = "x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x3nfvp2 x1q0g3np x87ps6o x1lku1pv x1a2a7pz"

    tab_ = chromium.latest_tab
    tab_.get(f'https://www.facebook.com/{account}/videos')
    check_has_login_and_registry_button(tab_, timeout=timeout)
    result = []
    posts_ = tab_.eles(f"@class={post_class}", timeout=timeout)
    if posts_:
        for r in posts_:
            if not r.text:
                continue

            try:
                video_data = r.ele(f"@@class={video_and_des_class}@@href:https://www.facebook.com/{account}/videos@@tabindex=-1")
                describe = r.ele(f"@@class={video_and_des_class}@@href:https://www.facebook.com/{account}/videos@@tabindex=0")
                user_moods = r.eles(f"@@class={user_mood_class}@@tabindex=0")
                user_moods_ = []
                for user_mood_ in user_moods:
                    user_moods_.append(user_mood_.attr("aria-label"))
                href = video_data.attr("href")
                describe = describe.text
                video_data = video_schemes.VideoData(
                    uid=account,
                    url=href,
                    describe=describe,
                    user_mood=user_moods_
                )
                result.append(video_data)

            except Exception as e:
                logging.warning(f"happen some error when try to get video data: {r}")

        return result
    logging.info("not in target uid page")
    return False


def go_to_reels_page(chromium: Chromium, account: str, get_reels_count: int = 10, timeout: int = 5) -> ChromiumPage.get_tab:
    reels_post_class = "x9f619 x1r8uery x1iyjqo2 x6ikm8r x10wlt62 x1n2onr6"
    video_and_des_class = "x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1heor9g x1sur9pj xkrqix3"
    user_mood_class = "x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x3nfvp2 x1q0g3np x87ps6o x1lku1pv x1a2a7pz"

    tab_ = chromium.latest_tab
    tab_.get(f'https://www.facebook.com/{account}/reels/')
    check_has_login_and_registry_button(tab_, timeout=timeout)
    result = []
    posts_ = tab_.eles(f"@class={reels_post_class}", timeout=timeout)
    if posts_:
        for r in posts_:
            if not r.text:
                continue

            try:
                video_data = r.ele(f"@@class={video_and_des_class}@@href:https://www.facebook.com/{account}/videos@@tabindex=-1")
                describe = r.ele(f"@@class={video_and_des_class}@@href:https://www.facebook.com/{account}/videos@@tabindex=0")
                user_moods = r.eles(f"@@class={user_mood_class}@@tabindex=0")
                user_moods_ = []
                for user_mood_ in user_moods:
                    user_moods_.append(user_mood_.attr("aria-label"))
                href = video_data.attr("href")
                describe = describe.text
                video_data = video_schemes.VideoData(
                    uid=account,
                    url=href,
                    describe=describe,
                    user_mood=user_moods_
                )
                result.append(video_data)

            except Exception as e:
                logging.warning(f"happen some error when try to get video data: {r}")

        return result
    logging.info("not in target uid page")
    return False