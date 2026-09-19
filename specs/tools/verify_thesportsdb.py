#!/usr/bin/env python3
"""TheSportsDB の無料キーで、対象リーグの日程・結果・順位表がどれだけ取れるかを確かめる。

使い方:
    python3 verify_thesportsdb.py            # 既定の5リーグ + サウジ
    python3 verify_thesportsdb.py --season 2026-2027
    python3 verify_thesportsdb.py --key 123  # キーを変える(既定は 123)

標準ライブラリだけで動く。Mac の python3 でそのまま実行できる。
結果は画面に表と要約を出し、生の JSON を ./thesportsdb_raw/ に保存する。
無料キーは 30 リクエスト/分なので、1 リクエストごとに 2.5 秒待つ。全部で数分かかる。
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime

BASE = "https://www.thesportsdb.com/api/v1/json/{key}/"
WAIT_SEC = 2.5
RAW_DIR = "thesportsdb_raw"

# 探したいリーグ。国と、リーグ名に含まれていてほしい語(小文字)。
TARGETS = [
    ("England", ["premier league"], "プレミアリーグ"),
    ("Spain", ["la liga", "laliga"], "ラ・リーガ"),
    ("Germany", ["bundesliga"], "ブンデスリーガ"),
    ("Netherlands", ["eredivisie"], "エールディヴィジ"),
    ("Japan", ["j1", "j-league", "j. league", "j league"], "J1"),
    ("Japan", ["j2"], "J2"),
    ("Japan", ["j3"], "J3"),
    ("Saudi Arabia", ["pro league", "saudi"], "サウジ・プロリーグ"),
]

# 2部を1部と取り違えないための除外語
EXCLUDE = ["2.", "second", "segunda", "championship", "women", "u21", "u23", "reserve", "youth", "cup", "keuken", "eerste"]


def fetch(key, path, params):
    url = BASE.format(key=key) + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "spec-verify/0.1"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", errors="replace")
            status = r.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        status = e.code
    except Exception as e:  # noqa: BLE001
        return None, f"ERROR {e}", time.time() - t0
    elapsed = time.time() - t0
    time.sleep(WAIT_SEC)
    try:
        data = json.loads(body) if body.strip() else {}
    except json.JSONDecodeError:
        return None, f"HTTP {status} (JSON でない応答)", elapsed
    return data, f"HTTP {status}", elapsed


def save_raw(name, data):
    os.makedirs(RAW_DIR, exist_ok=True)
    with open(os.path.join(RAW_DIR, name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def pick_league(leagues, words):
    """国内リーグ一覧から、語を含み除外語を含まないものを1つ選ぶ。"""
    cands = []
    for lg in leagues or []:
        name = (lg.get("strLeague") or "").lower()
        alt = (lg.get("strLeagueAlternate") or "").lower()
        hay = name + " | " + alt
        if any(w in hay for w in words) and not any(x in name for x in EXCLUDE):
            cands.append(lg)
    # J1/J2/J3 は "J1" のような短い語なので、完全に近いものを優先する
    cands.sort(key=lambda lg: len(lg.get("strLeague") or ""))
    return cands[0] if cands else None


def events_summary(events):
    """イベント一覧から、件数・スコア入り件数・日付の範囲を出す。"""
    evs = events or []
    scored = [e for e in evs if (e.get("intHomeScore") not in (None, "")) and (e.get("intAwayScore") not in (None, ""))]
    dates = sorted(e.get("dateEvent") for e in evs if e.get("dateEvent"))
    return {
        "count": len(evs),
        "scored": len(scored),
        "first": dates[0] if dates else "-",
        "last": dates[-1] if dates else "-",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default="123", help="API キー(無料キーは 123。古い資料では 3)")
    ap.add_argument("--season", default=None, help="シーズン文字列。既定は 2026-2027 と 2026 の両方を試す")
    args = ap.parse_args()

    seasons = [args.season] if args.season else ["2026-2027", "2026"]
    today = date.today().isoformat()
    print(f"TheSportsDB 検証  key={args.key}  today={today}")
    print("=" * 78)

    rows = []
    notes = []

    country_cache = {}
    for country, words, label in TARGETS:
        if country not in country_cache:
            data, st, _ = fetch(args.key, "search_all_leagues.php", {"c": country, "s": "Soccer"})
            leagues = (data or {}).get("countries") or (data or {}).get("leagues") or []
            country_cache[country] = leagues
            save_raw(f"leagues_{country.replace(' ', '_')}.json", data)
            print(f"[{country}] リーグ一覧: {st}, {len(leagues)} 件")
            for lg in leagues:
                print(f"    {lg.get('idLeague')}  {lg.get('strLeague')}  ({lg.get('strCurrentSeason') or '?'})")
        lg = pick_league(country_cache[country], words)
        if not lg:
            rows.append((label, "-", "見つからず", "", "", "", "", ""))
            notes.append(f"{label}: リーグ一覧に該当なし。上の一覧から手で ID を選ぶ必要あり")
            continue
        lid = lg["idLeague"]
        lname = lg.get("strLeague")
        cur = lg.get("strCurrentSeason") or ""
        print(f"\n--- {label}: {lname} (id={lid}, current season={cur or '?'})")

        # チーム一覧
        data, st, _ = fetch(args.key, "lookup_all_teams.php", {"id": lid})
        teams = (data or {}).get("teams") or []
        save_raw(f"teams_{lid}.json", data)
        print(f"  チーム一覧: {st}, {len(teams)} チーム")

        # 次の試合、直近の結果
        data, st, _ = fetch(args.key, "eventsnextleague.php", {"id": lid})
        nxt = (data or {}).get("events") or []
        save_raw(f"next_{lid}.json", data)
        ns = events_summary(nxt)
        print(f"  次の試合(eventsnextleague): {st}, {ns['count']} 件, {ns['first']} 〜 {ns['last']}")
        for e in nxt[:5]:
            print(f"      {e.get('dateEvent')} {e.get('strTime') or ''} UTC  {e.get('strHomeTeam')} vs {e.get('strAwayTeam')}  [{e.get('intRound') or '?'}節]")

        data, st, _ = fetch(args.key, "eventspastleague.php", {"id": lid})
        past = (data or {}).get("events") or []
        save_raw(f"past_{lid}.json", data)
        ps = events_summary(past)
        print(f"  直近の結果(eventspastleague): {st}, {ps['count']} 件, スコア入り {ps['scored']} 件, {ps['first']} 〜 {ps['last']}")
        for e in past[:5]:
            print(f"      {e.get('dateEvent')}  {e.get('strHomeTeam')} {e.get('intHomeScore')}-{e.get('intAwayScore')} {e.get('strAwayTeam')}")

        # シーズン全体
        season_used, ss, table_rows = "-", {"count": 0, "scored": 0, "first": "-", "last": "-"}, 0
        for sname in ([cur] if cur else []) + [x for x in seasons if x != cur]:
            data, st, _ = fetch(args.key, "eventsseason.php", {"id": lid, "s": sname})
            evs = (data or {}).get("events") or []
            if evs:
                save_raw(f"season_{lid}_{sname}.json", data)
                season_used, ss = sname, events_summary(evs)
                print(f"  シーズン全試合(eventsseason s={sname}): {st}, {ss['count']} 件, スコア入り {ss['scored']} 件, {ss['first']} 〜 {ss['last']}")
                if ss["count"] <= 15:
                    notes.append(f"{label}: eventsseason が {ss['count']} 件しか返らない。無料キーの件数制限の可能性")
                break
            print(f"  シーズン全試合(eventsseason s={sname}): {st}, 0 件")

        # 順位表
        for sname in ([season_used] if season_used != "-" else []) + [x for x in seasons if x != season_used]:
            data, st, _ = fetch(args.key, "lookuptable.php", {"l": lid, "s": sname})
            table = (data or {}).get("table") or []
            if table:
                save_raw(f"table_{lid}_{sname}.json", data)
                table_rows = len(table)
                print(f"  順位表(lookuptable s={sname}): {st}, {table_rows} 行")
                for t in table[:5]:
                    print(f"      {t.get('intRank')}. {t.get('strTeam')}  {t.get('intPlayed')}試合 {t.get('intPoints')}pt")
                break
            print(f"  順位表(lookuptable s={sname}): {st}, 0 行")

        rows.append((label, lid, str(len(teams)), f"{ns['count']}", f"{ps['scored']}/{ps['count']}", f"{ss['scored']}/{ss['count']}", season_used, str(table_rows)))

    print("\n" + "=" * 78)
    print("要約")
    hdr = ("リーグ", "ID", "チーム", "次の試合", "直近結果", "シーズン(スコア/件数)", "シーズン文字列", "順位表行数")
    print(" | ".join(hdr))
    for r in rows:
        print(" | ".join(r))

    print("\n手で確かめること(この出力と DAZN や公式サイトを見比べる):")
    print("  1. 「次の試合」の日時・対戦相手が正しいか(時刻は UTC 表記なので +9 時間)")
    print("  2. 「直近の結果」のスコアが正しいか、終了から何時間で反映されたか(明日以降にもう一度実行して比べる)")
    print("  3. 順位表の勝点・試合数が公式と一致するか")
    print("  4. J1〜J3 とサウジのチーム数が実際のクラブ数と一致するか")
    if notes:
        print("\n気になった点:")
        for n in notes:
            print("  - " + n)
    print(f"\n生の JSON は ./{RAW_DIR}/ に保存した。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
