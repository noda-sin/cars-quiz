#!/usr/bin/env python3
"""Fetch lead images from Wikipedia for each vehicle and center-crop to square.

Prefers Japanese Wikipedia (Japanese vehicles look familiar to a Japanese
toddler), falls back to English Wikipedia. License/author metadata is saved
to images/cars/_sources.json.
"""
import io
import json
import os
import re
import urllib.parse
import urllib.request
from PIL import Image

UA = "cars-quiz/1.0 (https://github.com/noda-sin/cars-quiz)"

# slug, ja.wikipedia title, en.wikipedia title
VEHICLES = [
    ("police_car",    "パトカー",          "Police car"),
    ("fire_truck",    "消防車",            "Fire engine"),
    ("ambulance",     "救急車",            "Ambulance"),
    ("dump_truck",    "ダンプカー",        "Dump truck"),
    ("bulldozer",     "ブルドーザー",      "Bulldozer"),
    ("excavator",     "油圧ショベル",      "Excavator"),
    ("crane_truck",   "移動式クレーン",    "Mobile crane"),
    ("mixer_truck",   "ミキサー車",        "Concrete mixer"),
    ("garbage_truck", "塵芥車",            "Garbage truck"),
    ("forklift",      "フォークリフト",    "Forklift"),
    ("tow_truck",     "レッカー車",        "Tow truck"),
    ("truck",         "貨物自動車",        "Truck"),
    ("tractor",       "トラクター",        "Tractor"),
    ("bus",           "バス (交通機関)",   "Bus"),
    ("taxi",          "タクシー",          "Taxi"),
    ("car",           "自動車",            "Car"),
    ("motorcycle",    "オートバイ",        "Motorcycle"),
    ("road_roller",   "ロードローラー",    "Road roller"),
    ("train",         "電車",              "Train"),
    ("shinkansen",    "新幹線",            "Shinkansen"),
]

# Manual overrides: slug -> Wikimedia Commons file title (without "File:")
# Hand-picked for clarity/recognizability for a Japanese toddler.
OVERRIDES = {
    "dump_truck": "ISUZU Giga, Dump Truck, Yellow.jpg",
    "bulldozer": "Komatsu D85PX R04.jpg",
    "crane_truck": "Tadano Rough Terrain Crane CREVO 160 at Sanmin Road, Songshan District, Taipei 20160313.jpg",
    "taxi": "Toyota JPN Taxi Hinomaru Taxi yellow rear side.jpg",
    "shinkansen": "Series-N700S-J2.jpg",
    "train": "Series-E233-T71.jpg",
    "ambulance": "Japanese TOYOTA HIMEDIC 3rd ambulance.jpg",
    "fire_truck": "双葉電子工業特設消防隊の消防車2021-08-23.jpg",
    "bus": "Kobe City 705 Isuzu Motors Erga QKG-LV234L3.jpg",
    "forklift": "Toyota Forklift in Trondheim Harbour.jpg",
    "car": "Honda FIT e-HEV HOME (6AA-GR3) front.jpg",
    "tow_truck": "Yamaguchi Wrecker Manufactured by Isuzu Giga Tow truck.png",
}

OUT_DIR = "images/cars"
SIZE = 800


def fetch(url, tries=3):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # IncompleteRead / timeouts happen on big originals
            last = e
    raise last


def get_summary_image(title, lang):
    api = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title.replace(' ', '_'), safe='')}"
    try:
        data = json.loads(fetch(api))
    except Exception as e:
        print(f"    [{lang}] summary failed: {e}")
        return None
    if "originalimage" in data:
        return data["originalimage"]["source"]
    if "thumbnail" in data:
        return data["thumbnail"]["source"]
    return None


def commons_file_url(filename):
    """Return a 1600px-wide thumb URL (smaller + more reliable than originals)."""
    api = ("https://commons.wikimedia.org/w/api.php?action=query&format=json"
           "&prop=imageinfo&iiprop=url&iiurlwidth=1600"
           "&titles=" + urllib.parse.quote("File:" + filename))
    data = json.loads(fetch(api))
    pages = data["query"]["pages"]
    for p in pages.values():
        info = p.get("imageinfo")
        if info:
            return info[0].get("thumburl") or info[0]["url"]
    return None


def file_metadata(image_url):
    """Look up author/license on Commons from a upload.wikimedia.org URL."""
    m = re.search(r"/([^/]+)$", urllib.parse.unquote(image_url))
    if not m:
        return {}
    name = re.sub(r"^\d+px-", "", m.group(1))
    api = ("https://commons.wikimedia.org/w/api.php?action=query&format=json"
           "&prop=imageinfo&iiprop=extmetadata&iiextmetadatafilter=Artist|LicenseShortName|Credit"
           "&titles=" + urllib.parse.quote("File:" + name))
    try:
        data = json.loads(fetch(api))
        for p in data["query"]["pages"].values():
            info = p.get("imageinfo")
            if info:
                em = info[0].get("extmetadata", {})
                strip = lambda s: re.sub(r"<[^>]+>", "", s or "").strip()
                return {
                    "file": name,
                    "artist": strip(em.get("Artist", {}).get("value")),
                    "license": strip(em.get("LicenseShortName", {}).get("value")),
                }
    except Exception as e:
        print(f"    metadata lookup failed: {e}")
    return {"file": name}


def crop_square(img, size=SIZE):
    img = img.convert("RGB")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    if side > size:
        img = img.resize((size, size), Image.LANCZOS)
    return img


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    attribution = []
    for slug, ja, en in VEHICLES:
        print(f"== {slug}")
        url = None
        if slug in OVERRIDES:
            url = commons_file_url(OVERRIDES[slug])
            print(f"  override: {url}")
        if not url:
            url = get_summary_image(ja, "ja")
        if not url or url.lower().endswith(".svg"):
            print("  ja missing/svg, trying en...")
            url = get_summary_image(en, "en")
        if not url or url.lower().endswith(".svg"):
            print(f"  !! no usable image for {slug}")
            continue
        print(f"  src: {url}")
        try:
            raw = fetch(url)
            img = Image.open(io.BytesIO(raw))
            img = crop_square(img)
            out_path = os.path.join(OUT_DIR, f"{slug}.jpg")
            img.save(out_path, "JPEG", quality=82, optimize=True)
            meta = file_metadata(url)
            meta["slug"] = slug
            meta["image_url"] = url
            attribution.append(meta)
            print(f"  saved: {out_path}")
        except Exception as e:
            print(f"  !! download/process failed: {e}")

    with open(os.path.join(OUT_DIR, "_sources.json"), "w", encoding="utf-8") as f:
        json.dump(attribution, f, ensure_ascii=False, indent=2)
    print(f"\nDone. {len(attribution)}/{len(VEHICLES)} images saved.")


if __name__ == "__main__":
    main()
