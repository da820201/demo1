import datetime
import time
from DrissionPage import common, ChromiumPage
from conf import picture_save_path, all_friend_url

friend_data_by_name = {}
friend_data = {}


def send_message_with_display_name(tab_: ChromiumPage.get_tab, display_name_: str, message: str, timeout: int = 5):
    friend_data_: dict = friend_data_by_name.get(display_name_)
    if friend_data_by_name is None:
        print("no this display_name data")

    mid_ = friend_data_.get("mid")
    return send_message(tab_, mid_, display_name_, message=message, timeout=timeout)


def send_message_with_mid(tab_: ChromiumPage.get_tab, mid_: str, message: str, timeout: int = 5):
    friend_data_: dict = friend_data.get(mid_)
    if friend_data_ is None:
        print("no this mid data")

    display_name_ = friend_data_.get("displayName")
    return send_message(tab_, mid_, display_name_, message=message, timeout=timeout)


def send_message(tab_: ChromiumPage.get_tab, mid_: str, display_name_: str, message: str, timeout: int = 5) -> bool:
    if not use_search(tab_, display_name_, mid_, timeout):
        print("Use search failed")
        return False

    print("等待入對話框")
    chat_button = tab_.wait.ele_displayed(f"@@class=startChat-module__button_start__FjvEK button-module__button__NBD6v ", timeout=timeout)
    if chat_button:
        tab_.ele(f"@@class=startChat-module__button_start__FjvEK button-module__button__NBD6v ").click()

    test_box = tab_.wait.ele_displayed(f"@@class=text chatroomEditor-module__textarea__yKTlH@@placeholder=輸入訊息", timeout=timeout)
    if test_box:
        print("進入對話框")
        test_box = tab_.ele("@@class=text chatroomEditor-module__textarea__yKTlH@@placeholder=輸入訊息")
        test_box.input(message)
        tab_.actions.key_down(common.Keys.ENTER)
        tab_.actions.key_up(common.Keys.ENTER)
        print(f"完成對於 {display_name_} 的對話，內容為 {message}")
        return True
    return False


# 更新好友資料
def update_friend_data(_friend_data: dict):
    data_: dict = _friend_data.get("data", {})
    contacts_ = data_.get("contacts", {})

    for mid_, v in contacts_.items():
        contact = v.get("contact", {})
        display_name = contact.get("displayName", "")
        profile_id = contact.get("profileId", "")
        picture_path = contact.get("picturePath", "")
        if mid_ not in friend_data:
            friend_data_by_name.update(
                {
                    display_name: {
                        "mid": mid_,
                        "profile_id": profile_id,
                        "picture_path": picture_path
                    }
                }
            )
            friend_data[mid_] = v


def print_background_package(tab_: ChromiumPage.get_tab):
    for packet in tab_.listen.steps():
        response = packet.response
        url = packet.url
        if url == all_friend_url:
            update_friend_data(response.body)


def get_friend_chat_data(tab_, timeout: int = 1) -> bool:
    ...


def use_search(tab_: ChromiumPage.get_tab,  display_name_: str, mid_: str, timeout: int = 5) -> bool:
    if check_is_in_all_friend_page(tab_, timeout):
        ele_ = tab_.ele("@@class=searchInput-module__input__ekGp7 @@placeholder=以姓名搜尋")
        ele_.clear()
        ele_.input(display_name_)
        friend_chat_page = tab_.wait.ele_displayed(f"@@class=friendlistItem-module__item__1tuZn @@data-mid={mid_}", timeout=timeout)
        time.sleep(2)
        if friend_chat_page:
            tab_.ele(f"@@class=friendlistItem-module__item__1tuZn @@data-mid={mid_}").click()
            return True
    return False


def check_is_in_main_page(tab_: ChromiumPage.get_tab, timeout: int = 5) -> bool:
    # 等待進入主畫面
    print("等待進入主畫面")
    main_page = tab_.wait.ele_displayed("@class=gnb-module__button_action__aTdj7", timeout=timeout)
    print("進入主畫面")
    return main_page


def check_is_in_all_friend_page(tab_: ChromiumPage.get_tab, timeout: int = 5):
    if check_is_in_main_page(tab_, timeout):
        print("等待好友畫面")
        is_in_all_friend_page = tab_.wait.ele_displayed("@class=gnb-module__button_action__aTdj7", timeout=timeout)
        tab_.ele("@class=gnb-module__button_action__aTdj7").click()
        if is_in_all_friend_page:
            print("進入好友畫面")
            return True
    return False


def send_pin_code(tab_: ChromiumPage.get_tab, timeout: int = 5):
    pin_code_result = tab_.wait.ele_displayed("@class=pinCodeModal-module__pincode__bFKMn", timeout=timeout)
    if pin_code_result:
        pin_code = tab_.ele("@class=pinCodeModal-module__pincode__bFKMn").text
        # TODO 傳送 Ping code
        print("pin_code", pin_code)
    else:
        message_box_result = tab_.wait.ele_displayed("@class=loginForm-module__error_description__p27bp", timeout=timeout)
        if message_box_result:
            message_box = tab_.ele("@class=pinCodeModal-module__pincode__bFKMn").text
            raise Exception(f"Login Error: {message_box}")


def logout(tab_: ChromiumPage.get_tab) -> bool:
    # 如果已經登入，則登出
    is_in_main_page_ = check_is_in_main_page(tab_, 2)
    if is_in_main_page_:
        print("已經登入，進行登出作業")
        tab_.wait.ele_displayed("@data-tooltip=設定", timeout=10)
        tab_.ele("@data-tooltip=設定").click()
        tab_.wait.ele_displayed("@@class=actionPopoverListItem-module__button_action__mHl56@@text()=登出", timeout=10)
        tab_.ele("@@class=actionPopoverListItem-module__button_action__mHl56@@text()=登出").click()
        print("已經完成登出作業")
    return True


def add_friend(tab_: ChromiumPage.get_tab, _chromium: ChromiumPage, _uid: str, timeout: int = 5):
    print("進行加入好友")
    tab_.wait.ele_displayed("@data-tooltip=加入好友", timeout=timeout)
    tab_.ele("@data-tooltip=加入好友").click()
    tab_.wait.ele_displayed("@class=friendlistItem-module__button_friendlist_item__xoWur", timeout=timeout)
    tab_.ele("@class=friendlistItem-module__button_friendlist_item__xoWur").click()
    time.sleep(3)
    tab_ = _chromium.get_tab(title="搜尋好友")
    tab_.wait.ele_displayed("@class=searchInput-module__label__40CWI", timeout=timeout)
    text_box = tab_.ele("@class=searchInput-module__label__40CWI")
    text_box.click()
    text_box.clear()
    text_box.input(_uid)
    tab_.actions.key_down(common.Keys.ENTER)
    tab_.actions.key_up(common.Keys.ENTER)


def login(tab_: ChromiumPage.get_tab, account: str, password: str, use_qr_code_login: bool = False, timeout: int = 5):
    # 如果已經登入，則登出
    if check_is_in_main_page(tab_, 2):
        logout(tab_)

    # 登入流程
    if use_qr_code_login:
        # 取得QR Code
        canvas_ele = tab_.ele("@style=height: 115px; width: 115px;")
        canvas_ele.get_screenshot(picture_save_path, f"{datetime.datetime.now()}.png")
        send_pin_code(tab_)
    # 一般登入
    else:
        print("進行一般登入作業")
        tab_.wait.ele_displayed("@placeholder=電子郵件帳號", timeout=timeout)
        ele = tab_.ele("@placeholder=電子郵件帳號")
        ele.clear()
        ele.input(account)

        tab_.wait.ele_displayed("@placeholder=密碼", timeout=timeout)
        ele = tab_.ele("@placeholder=密碼")
        ele.clear()
        ele.input(password)

        # 點選登入
        tab_.ele("@class=loginForm-module__button_login__gnKsN button-module__button__NBD6v ").click()
        send_pin_code(tab_)
        print("完成一般登入作業")

