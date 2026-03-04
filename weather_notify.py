#!/usr/bin/env python3
"""
日本全国天気予報 → Slack通知スクリプト
毎朝7時にGitHub Actionsから実行されます
"""

import urllib.request
import urllib.parse
import json
import os
from datetime import datetime, timezone, timedelta

# 都道府県データ（名前・緯度・経度・地方）
PREFECTURES = [
    {"name": "北海道", "lat": 43.0642, "lon": 141.3469, "region": "北海道"},
    {"name": "青森県", "lat": 40.8244, "lon": 140.7400, "region": "東北"},
    {"name": "岩手県", "lat": 39.7036, "lon": 141.1527, "region": "東北"},
    {"name": "宮城県", "lat": 38.2688, "lon": 140.8721, "region": "東北"},
    {"name": "秋田県", "lat": 39.7186, "lon": 140.1024, "region": "東北"},
    {"name": "山形県", "lat": 38.2404, "lon": 140.3636, "region": "東北"},
    {"name": "福島県", "lat": 37.7500, "lon": 140.4676, "region": "東北"},
    {"name": "茨城県", "lat": 36.3418, "lon": 140.4468, "region": "関東"},
    {"name": "栃木県", "lat": 36.5658, "lon": 139.8836, "region": "関東"},
    {"name": "群馬県", "lat": 36.3911, "lon": 139.0608, "region": "関東"},
    {"name": "埼玉県", "lat": 35.8569, "lon": 139.6489, "region": "関東"},
    {"name": "千葉県", "lat": 35.6047, "lon": 140.1233, "region": "関東"},
    {"name": "東京都", "lat": 35.6895, "lon": 139.6917, "region": "関東"},
    {"name": "神奈川県", "lat": 35.4478, "lon": 139.6425, "region": "関東"},
    {"name": "新潟県", "lat": 37.9022, "lon": 139.0235, "region": "中部"},
    {"name": "富山県", "lat": 36.6953, "lon": 137.2113, "region": "中部"},
    {"name": "石川県", "lat": 36.5947, "lon": 136.6256, "region": "中部"},
    {"name": "福井県", "lat": 36.0652, "lon": 136.2217, "region": "中部"},
    {"name": "山梨県", "lat": 35.6642, "lon": 138.5686, "region": "中部"},
    {"name": "長野県", "lat": 36.6513, "lon": 138.1810, "region": "中部"},
    {"name": "岐阜県", "lat": 35.3912, "lon": 136.7223, "region": "中部"},
    {"name": "静岡県", "lat": 34.9769, "lon": 138.3831, "region": "中部"},
    {"name": "愛知県", "lat": 35.1802, "lon": 136.9066, "region": "中部"},
    {"name": "三重県", "lat": 34.7303, "lon": 136.5086, "region": "近畿"},
    {"name": "滋賀県", "lat": 35.0045, "lon": 135.8686, "region": "近畿"},
    {"name": "京都府", "lat": 35.0116, "lon": 135.7681, "region": "近畿"},
    {"name": "大阪府", "lat": 34.6863, "lon": 135.5200, "region": "近畿"},
    {"name": "兵庫県", "lat": 34.6913, "lon": 135.1830, "region": "近畿"},
    {"name": "奈良県", "lat": 34.6851, "lon": 135.8329, "region": "近畿"},
    {"name": "和歌山県", "lat": 34.2261, "lon": 135.1675, "region": "近畿"},
    {"name": "鳥取県", "lat": 35.5035, "lon": 134.2376, "region": "中国"},
    {"name": "島根県", "lat": 35.4723, "lon": 133.0505, "region": "中国"},
    {"name": "岡山県", "lat": 34.6618, "lon": 133.9344, "region": "中国"},
    {"name": "広島県", "lat": 34.3966, "lon": 132.4596, "region": "中国"},
    {"name": "山口県", "lat": 34.1860, "lon": 131.4706, "region": "中国"},
    {"name": "徳島県", "lat": 34.0657, "lon": 134.5593, "region": "四国"},
    {"name": "香川県", "lat": 34.3400, "lon": 134.0434, "region": "四国"},
    {"name": "愛媛県", "lat": 33.8417, "lon": 132.7657, "region": "四国"},
    {"name": "高知県", "lat": 33.5597, "lon": 133.5311, "region": "四国"},
    {"name": "福岡県", "lat": 33.6064, "lon": 130.4183, "region": "九州"},
    {"name": "佐賀県", "lat": 33.2494, "lon": 130.2988, "region": "九州"},
    {"name": "長崎県", "lat": 32.7503, "lon": 129.8777, "region": "九州"},
    {"name": "熊本県", "lat": 32.7898, "lon": 130.7417, "region": "九州"},
    {"name": "大分県", "lat": 33.2382, "lon": 131.6126, "region": "九州"},
    {"name": "宮崎県", "lat": 31.9111, "lon": 131.4239, "region": "九州"},
    {"name": "鹿児島県", "lat": 31.5602, "lon": 130.5581, "region": "九州"},
    {"name": "沖縄県", "lat": 26.2124, "lon": 127.6809, "region": "沖縄"},
]

WMO_CODES = {
    0:  ("快晴",         "☀️"),
    1:  ("晴れ",         "🌤️"),
    2:  ("一部曇り",     "⛅"),
    3:  ("曇り",         "☁️"),
    45: ("霧",           "🌫️"),
    48: ("霧氷",         "🌫️"),
    51: ("霧雨（弱）",   "🌦️"),
    53: ("霧雨",         "🌦️"),
    55: ("霧雨（強）",   "🌧️"),
    61: ("雨（弱）",     "🌧️"),
    63: ("雨",           "🌧️"),
    65: ("雨（強）",     "🌧️"),
    71: ("雪（弱）",     "❄️"),
    73: ("雪",           "🌨️"),
    75: ("雪（強）",     "❄️"),
    77: ("霰",           "🌨️"),
    80: ("にわか雨（弱）","🌦️"),
    81: ("にわか雨",     "🌧️"),
    82: ("にわか雨（強）","⛈️"),
    85: ("にわか雪",     "🌨️"),
    86: ("にわか雪（強）","❄️"),
    95: ("雷雨",         "⛈️"),
    96: ("雷雨＋雹",     "⛈️"),
    99: ("激しい雷雨",   "🌩️"),
}


def fetch_weather(pref):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={pref['lat']}&longitude={pref['lon']}"
        f"&daily=weathercode&timezone=Asia%2FTokyo&forecast_days=1"
    )
    with urllib.request.urlopen(url, timeout=10) as res:
        data = json.loads(res.read())
    code = data["daily"]["weathercode"][0]
    label, emoji = WMO_CODES.get(code, ("不明", "❓"))
    return {**pref, "code": code, "label": label, "emoji": emoji}


def build_message(weather_list):
    jst = timezone(timedelta(hours=9))
    today = datetime.now(jst).strftime("%Y年%-m月%-d日（%a）")

    # 曜日を日本語に変換
    day_map = {"Mon": "月", "Tue": "火", "Wed": "水", "Thu": "木",
               "Fri": "金", "Sat": "土", "Sun": "日"}
    for en, ja in day_map.items():
        today = today.replace(en, ja)

    # 地方ごとにグループ化
    regions = {}
    for p in weather_list:
        regions.setdefault(p["region"], []).append(p)

    lines = [f"🗾 *日本全国 天気予報 — {today}*\n"]
    for region, prefs in regions.items():
        lines.append(f"*【{region}】*")
        for p in prefs:
            lines.append(f"{p['emoji']} {p['name']}：{p['label']}")
        lines.append("")

    lines.append("_powered by Open-Meteo_")
    return "\n".join(lines)


def send_to_slack(webhook_url, message):
    payload = json.dumps({"text": message}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        return res.status


def main():
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("環境変数 SLACK_WEBHOOK_URL が設定されていません")

    print("🌐 天気データを取得中...")
    weather_list = []
    for pref in PREFECTURES:
        try:
            result = fetch_weather(pref)
            weather_list.append(result)
            print(f"  ✅ {pref['name']}: {result['emoji']} {result['label']}")
        except Exception as e:
            print(f"  ⚠️  {pref['name']}: 取得失敗 ({e})")

    print(f"\n📨 Slackに送信中... ({len(weather_list)}件)")
    message = build_message(weather_list)
    status = send_to_slack(webhook_url, message)
    print(f"✅ 送信完了 (HTTP {status})")


if __name__ == "__main__":
    main()
