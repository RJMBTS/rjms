import requests
import json
import os
from collections import defaultdict
from datetime import datetime, timezone, timedelta

# ✅ Read from GitHub Secrets (Environment Variables)
JSON_URL = os.getenv("JSON_URL")
EPG_URL = os.getenv("EPG_URL")
OUTPUT_FILE = "rjms.m3u"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://playify.pages.dev/"
}

def fetch_json():
    try:
        if not JSON_URL:
            print("❌ JSON_URL secret is missing!")
            return []

        print("🔄 Fetching JSON from secret URL...")
        r = requests.get(JSON_URL, headers=HEADERS, timeout=30)
        print("Status:", r.status_code)

        if r.status_code != 200:
            print("❌ Non-200 response")
            return []

        try:
            data = r.json()
        except:
            data = json.loads(r.text)

        if not isinstance(data, list):
            print("❌ JSON is not a list")
            return []

        print("✅ Total channels fetched:", len(data))
        return data

    except Exception as e:
        print("❌ Fetch Exception:", e)
        return []


def categorize_channels(channels):
    categories = defaultdict(list)

    rules = {
        "Sports": ['sport', 'cricket', 'football', 'tennis', 'kabaddi', 'wwe', 'f1', 'moto'],
        "Kids": ['kids', 'cartoon', 'nick', 'disney', 'pogo', 'hungama', 'sonic', 'junior'],
        "Movies": ['movie', 'cinema', 'gold', 'max', 'flix', 'film', 'action', 'thriller'],
        "News": ['news', 'aaj', 'ndtv', 'abp', 'india', 'republic', 'times', 'cnbc', 'zee', 'tv9'],
        "Music": ['music', 'mtv', '9xm', 'b4u', 'zoom'],
        "Religious": ['bhakti', 'religious', 'aastha', 'sanskar', 'vedic'],
        "Entertainment": ['colors', 'zee', 'star', 'sony', 'sab', '&tv', 'life', 'dangal']
    }

    for ch in channels:
        name = ch.get("name", "").lower()
        category = "Others"
        for cat, keys in rules.items():
            if any(k in name for k in keys):
                category = cat
                break
        categories[category].append(ch)

    return categories


def create_m3u(categories):
    if not EPG_URL:
        print("❌ EPG_URL secret is missing!")
        return "#EXTM3U\n"

    # ✅ Auto IST Timestamp
    ist = timezone(timedelta(hours=5, minutes=30))
    last_updated = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")

    # ✅ Custom Branded Header
    m3u = (
        '#EXTM3U billed-msg="RJM Tv - RJMBTS Network"\n'
        '# Pushed and Updated by Kittujk\n'
        '# Coded & Maintained @RJMBTS\n'
        f'# Last updated: {last_updated}\n'
        f'#EXTM3U x-tvg-url="{EPG_URL}"\n\n'
    )

    order = ['Entertainment', 'Movies', 'Sports', 'Kids', 'News', 'Music', 'Religious', 'Others']

    total_written = 0
    used_links = set()

    for cat in order:
        if cat not in categories:
            continue

        for ch in categories[cat]:
            name = ch.get("name", "Unknown")
            logo = ch.get("logo", "")
            link = ch.get("link", "")
            cookie = ch.get("cookie", "")
            drm = ch.get("drmScheme", "")
            license_url = ch.get("drmLicense", "")

            if not isinstance(link, str) or not link.startswith("http"):
                continue

            if link in used_links:
                continue
            used_links.add(link)

            m3u += f'#EXTINF:-1 group-title="{cat}" tvg-logo="{logo}",{name}\n'

            if drm:
                m3u += f'#KODIPROP:inputstream.adaptive.license_type={drm}\n'

            if license_url:
                m3u += f'#KODIPROP:inputstream.adaptive.license_key={license_url}\n'

            if cookie:
                cookie = cookie.replace('"', '').strip()
                m3u += f'#EXTHTTP:{{"cookie":"{cookie}"}}\n'

            m3u += f'{link}\n\n'
            total_written += 1

    print("✅ Channels written:", total_written)
    return m3u


def main():
    data = fetch_json()

    if not data:
        print("❌ JSON EMPTY — writing header only")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
        return

    categories = categorize_channels(data)
    playlist = create_m3u(categories)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(playlist)

    print("✅ Final Playlist Saved:", OUTPUT_FILE)
    print("✅ File size:", len(playlist), "bytes")


if __name__ == "__main__":
    main()
