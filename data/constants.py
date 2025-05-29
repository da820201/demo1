
class Setting:
    BLOK_VERSION_ID = "5f56efad68e1edec7801f630b5c122704ec5378adbee6609a448f105f34a9c73"
    ANDROID_ID = ""
    DEVICE_ID = ""


class Path:
    FacebookHost = "https://www.facebook.com"
    ThreadsHost = "https://www.threads.com"
    InstagramHost = "https://www.instagram.com"
    InstagramGraphql = f"{InstagramHost}/graphql"
    InstagramGraphqlQuery = f"{InstagramGraphql}/query"
    InstagramAPIV1 = f"{InstagramHost}/api/v1"
    ThreadsGraphql = f"{ThreadsHost}/graphql"
    ThreadsGraphqlQuery = f"{ThreadsGraphql}/query"

class ThreadsHeaders:
    GetUserProfile = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-TW,zh;q=0.9",
        "cache-control": "max-age=0",
        "dpr": "2",
        "priority": "u=0, i",
        "sec-ch-prefers-color-scheme": "light",
        "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
        "sec-ch-ua-full-version-list": "\"Chromium\";v=\"136.0.7103.114\", \"Google Chrome\";v=\"136.0.7103.114\", \"Not.A/Brand\";v=\"99.0.0.0\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": "\"\"",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-ch-ua-platform-version": "\"15.4.0\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "viewport-width": "1180"
    }

class ThreadsPayload:
    PayloadBase = (
        f"av=17841474859429560"
        f"&__user=0"
        f"&__a=1"
        f"&__req=ji"
        f"&__hs=20230.HYP%3Abarcelona_web_pkg.2.1...0"
        f"&dpr=2"
        f"&__ccg=EXCELLENT"
        f"&__rev=1023085245"
        f"&__s=jd4at2%3Ascqrpm%3Axss97y"
        f"&__hsi=7507174385136303460"
        f"&__dyn=7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W0qa0FE2awgo9oO0n24oaEd82lwv89k2C1Fwc60D85m1mzXwae4UaEW0Loco5G0zK5o4q0HU1IEGdwtU2ewbS1LwTwKG0hq1Iwqo9EpwUwiQ1mwLwHxW17y9UjgbVE-19xW1Vwn85SU7y"
        f"&__csr=ghh5Wex75tTbICDbllQzuC_NkGpp2yAFogKUKV5VayoV2XAVVuqpypbGvKbQAULw05Eny8kw11d6z0Gb4G3u7A1oxol81lw8-8N2xd1ongC6o7W29xe2S1cPwvK3G0J8z4UjgmS0Nrx3hpA1Gw8iUjw3OU12U2oK1bK5VUmw54w2dE3HwLwU41y5N0dS3EEo2bk9wcd04uwenwtodUzw6fxTSKaVxE5a2i4af41i15AFzsh4a4Qfogg1HU0Ky096ycM02c7gghk"
        f"&__hsdp=gbR9NikZ52kJyIMi0Wyq3xx31pc9bEEH9tMOMxaz4kO2W9Bsby0-G5E9Eo5NoiclE6wE9b6QoM4Mid6E4x8EEjhQ4iNP2oN8o19a4BzoCfl1i7VERxh3oqwn4u5pU4K3Ki4o5C2q2Wbwpob8y58a8O2uuEKq5U26wlEb98lye32m2Sp0"
        f"&__hblp=0mawfS9yA8zovyoJ3AAEe8J1DF0HwgUe84iqayVbzXCwzwDxmm3W8xy4AF8O8y99U-q6EaojwHG7otwAg5e1ew42wcu2O8gjCKEOdXCxicgOEix2Wxm5E8UnVE88S4Qu7Ub98C3ufBwJCg"
        f"&__comet_req=29&fb_dtsg=NAftAvIGjS2E7kW9v62eWhPgh0h193JBxqHY81AaFFCS7dN036ya-yw%3A17853667720085245%3A1747898157&jazoest=25937&lsd=M2LDCAcPD0qxRYodVH85TM"
        f"&__spin_r=1023085245"
        f"&__spin_b=trunk"
        f"&__spin_t=1747900244"
        f"&__crn=comet.threads.BarcelonaProfileThreadsColumnRoute"
        f"&fb_api_caller_class=RelayModern"
        f"&fb_api_req_friendly_name=BarcelonaFriendshipsFollowersTabQuery"
        f"&server_timestamps=true"
        f"&doc_id=29257825927198293"
    )


if __name__ == "__main__":
    pass