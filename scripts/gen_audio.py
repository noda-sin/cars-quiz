#!/usr/bin/env python3
"""Generate Japanese voice clips (natural neural TTS) for the quiz.

Uses Google Translate's public TTS endpoint, which serves a natural
human-sounding Japanese voice as MP3. Output goes to audio/.
"""
import os
import time
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
OUT_DIR = "audio"

# slug -> spoken name (kana/kanji chosen so TTS reads it correctly)
NAMES = {
    "police_car":    "パトカー",
    "fire_truck":    "しょうぼうしゃ",
    "ambulance":     "きゅうきゅうしゃ",
    "dump_truck":    "ダンプカー",
    "bulldozer":     "ブルドーザー",
    "excavator":     "ショベルカー",
    "crane_truck":   "クレーン車",
    "mixer_truck":   "ミキサー車",
    "garbage_truck": "ごみ収集車",
    "forklift":      "フォークリフト",
    "tow_truck":     "レッカー車",
    "truck":         "トラック",
    "tractor":       "トラクター",
    "bus":           "バス",
    "taxi":          "タクシー",
    "car":           "じどうしゃ",
    "motorcycle":    "バイク",
    "road_roller":   "ロードローラー",
    "train":         "でんしゃ",
    "shinkansen":    "しんかんせん",
}

EXTRAS = {
    "start":    "くるまクイズ、はじめるよ！",
    "praise_1": "ピンポーン！せいかい！",
    "praise_2": "せいかい！すごーい！",
    "praise_3": "やったね！じょうずだね！",
    "praise_4": "せいかい！やったー！",
    "retry_1":  "ちがうよー、もういっかい！",
    "retry_2":  "あれれ？もういちど！",
    "retry_3":  "おしい！どこかなー？",
}


def tts(text, path):
    url = ("https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=ja&q="
           + urllib.parse.quote(text))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            if len(data) < 500:
                raise RuntimeError("suspiciously small response")
            with open(path, "wb") as f:
                f.write(data)
            return True
        except Exception as e:
            print(f"  retry ({e})")
            time.sleep(2)
    return False


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    jobs = {}
    for slug, name in NAMES.items():
        jobs[f"q_{slug}"] = f"{name}は、どーれだ？"
        jobs[f"n_{slug}"] = f"それは、{name}だね。"
    jobs.update(EXTRAS)

    ok = 0
    for key, text in jobs.items():
        path = os.path.join(OUT_DIR, f"{key}.mp3")
        print(f"{key}: {text}")
        if tts(text, path):
            ok += 1
        time.sleep(0.4)  # be polite
    print(f"\nDone. {ok}/{len(jobs)} clips saved.")


if __name__ == "__main__":
    main()
