#!/usr/bin/env python3
"""Fetch lead images from Wikipedia for each vehicle and center-crop to square."""
import io
import json
import os
import urllib.parse
import urllib.request
from PIL import Image

UA = "cars-quiz/1.0 (https://github.com/noda-sin/cars-quiz)"

VEHICLES = [
    ("police_car",  "パトカー",        "Police_car"),
    ("fire_truck",  "消防車",          "Fire_engine"),
    ("ambulance",   "救急車",          "Ambulance"),
    ("dump_truck",  "ダンプカー",      "Dump_truck"),
    ("bulldozer",   "ブルドーザー",    "Bulldozer"),
    ("excavator",   "油圧ショベル",    "Excavator"),
    ("forklift",    "フォークリフト",  "Forklift"),
    ("tow_truck",   "レッカー車",      "Tow_truck"),
    ("truck",       "貨物自動車",      "Truck"),
    ("tractor",     "トラクター",      "Tractor"),
    ("bus",         "バス_(交通機関)", "Bus_(vehicle)"),
    ("taxi",        "タクシー",        "Taxi"),
    ("car",         "自動車",          "Car"),
    ("train",       "電車",            "Train"),
    ("shinkansen",  "新幹線",          "Shinkansen"),
]

OUT_DIR = "images/cars"
SIZE = 600


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def get_image_url(title, lang):
    api = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title, safe='')}"
    try:
        data = json.loads(fetch(api))
    except Exception as e:
        print(f"    [{lang}] summary failed: {e}")
        return None, None
    src = None
    if "originalimage" in data:
        src = data["originalimage"]["source"]
    elif "thumbnail" in data:
        src = data["thumbnail"]["source"]
    return src, data.get("description")


def crop_square(img, size=SIZE):
    img = img.convert("RGB")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((size, size), Image.LANCZOS)
    return img


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    attribution = []
    for slug, ja, en in VEHICLES:
        print(f"== {slug}")
        url, desc = get_image_url(ja, "ja")
        title_used = ja
        lang_used = "ja"
        if not url or url.lower().endswith(".svg"):
            print(f"  ja missing/svg, trying en...")
            url, desc = get_image_url(en, "en")
            title_used = en
            lang_used = "en"
        if not url:
            print(f"  !! no image found for {slug}")
            continue
        if url.lower().endswith(".svg"):
            print(f"  !! got SVG; skipping {slug}")
            continue
        print(f"  src: {url}")
        try:
            raw = fetch(url)
            img = Image.open(io.BytesIO(raw))
            img = crop_square(img)
            out_path = os.path.join(OUT_DIR, f"{slug}.jpg")
            img.save(out_path, "JPEG", quality=85, optimize=True)
            print(f"  saved: {out_path}")
            attribution.append({
                "slug": slug,
                "wiki_lang": lang_used,
                "wiki_title": title_used,
                "image_url": url,
            })
        except Exception as e:
            print(f"  !! download/process failed: {e}")

    with open(os.path.join(OUT_DIR, "_sources.json"), "w", encoding="utf-8") as f:
        json.dump(attribution, f, ensure_ascii=False, indent=2)
    print(f"\nDone. {len(attribution)}/{len(VEHICLES)} images saved.")


if __name__ == "__main__":
    main()
